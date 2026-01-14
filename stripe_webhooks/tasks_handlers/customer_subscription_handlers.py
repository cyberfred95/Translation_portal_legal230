"""
Customer subscription webhook handlers for Stripe webhooks.

This module handles webhook events related to customer subscription operations,
including creation, updates, deletions, and trial end notifications for subscriptions.
"""

import random
import string

import stripe
from django.conf import settings

from emails.models import EmailType
from emails.send_email import send_email
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User

from .error.error import HttpResponse, exception_error, success_message
from .getter.get_data import (
    get_buyer_from_userSubscription_list,
    get_subscriptionType_by_stripe_product_id,
    get_user_by_stripe_customer_id,
    get_userSubscriptions_list_active_from_userSubscription_list,
    get_userSubscriptions_list_by_stripe_subscription_id,
)
from .getter.get_payload import (
    get_item_data_current_period_end,
    get_item_data_current_period_start,
    get_item_data_product_id,
    get_item_data_subscription_item_id,
    get_item_data_quantity,
    get_payload_cancel_at,
    get_payload_customer_id,
    get_payload_ended_at,
    get_payload_id,
    get_payload_item_data,
    get_payload_status,
)
from .helper.convertor import string_to_UserSubscriptionChoices
from .helper.stripe_session import get_stripe_customer_session_url
from .setter.set_userSubscription import (
    create_userSubscriptions,
    deactivate_userSubscriptions,
    set_new_userSubscription_list_values,
)


def _send_admin_notification_email(
    admin: User,
    buyer: User,
    email_type: EmailType,
    subscription_type: SubscriptionType,
    additional_params: dict | None = None
) -> HttpResponse | None:
    """
    Send notification email to an admin user.

    Args:
        admin: The admin user to notify.
        buyer: The buyer user (for Stripe session link).
        email_type: Type of email to send.
        subscription_type: The subscription type.
        additional_params: Additional parameters for email template.

    Returns:
        Error response if sending fails, None otherwise.
    """
    error_response, session_link = get_stripe_customer_session_url(
        buyer.stripe_customer_id
    )
    if error_response:
        return error_response

    params = {
        "lexa_company_name": buyer.group.name,
        "lexa_username": admin.username,
        "stripe_subscription_type": subscription_type.name,
        "stripe_session_link": session_link
    }
    if additional_params:
        params.update(additional_params)

    return send_email(
        admin.email,
        email_type,
        admin.language,
        params
    )


def _send_inactive_subscription_notifications(
    active_user_subscription_list: list[UserSubscription],
    group_admins: list[User],
    subscription_type: SubscriptionType,
    buyer: User
) -> HttpResponse | None:
    """
    Send notifications when subscriptions become inactive.

    Args:
        active_user_subscription_list: List of active subscriptions.
        group_admins: List of admin users in the group.
        subscription_type: The subscription type.
        buyer: The buyer user.

    Returns:
        Error response if sending fails, None otherwise.
    """
    # Notify regular users about subscription becoming inactive
    for user_subscription in active_user_subscription_list:
        user = user_subscription.user
        if user not in group_admins:
            error_response = send_email(
                user.email,
                EmailType.SUBSCRIPTION_UPDATED_INACTIVE,
                user.language,
                {
                    "lexa_username": user.username,
                    "stripe_subscription_type": subscription_type.name,
                }
            )
            if error_response:
                return error_response

    # Notify admins about subscription becoming inactive
    for admin in group_admins:
        error_response = _send_admin_notification_email(
            admin,
            buyer,
            EmailType.SUBSCRIPTION_UPDATED_INACTIVE_ADMIN,
            subscription_type
        )
        if error_response:
            return error_response

    return None


def _send_quantity_change_notifications(
    group_admins: list[User],
    buyer: User,
    subscription_type: SubscriptionType,
    quantity: int
) -> HttpResponse | None:
    """
    Send notifications when subscription quantity changes.

    Args:
        group_admins: List of admin users in the group.
        buyer: The buyer user.
        subscription_type: The subscription type.
        quantity: The new quantity.

    Returns:
        Error response if sending fails, None otherwise.
    """
    for admin in group_admins:
        error_response = _send_admin_notification_email(
            admin,
            buyer,
            EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN,
            subscription_type,
            {"quantity": quantity}
        )
        if error_response:
            return error_response

    return None


def _format_changed_fields_message(
    changed_fields: list[str],
    old_quantity: int,
    new_quantity: int
) -> str:
    """
    Format changed fields for success message.

    Args:
        changed_fields: List of changed field names.
        old_quantity: Previous quantity.
        new_quantity: New quantity.

    Returns:
        Formatted string describing changes.
    """
    fields_str = ", ".join(changed_fields) if changed_fields else "unknown changes"
    if old_quantity != new_quantity:
        fields_str += f", quantity ({old_quantity} → {new_quantity})"
    return fields_str


def _has_existing_subscriptions(user: User, exclude_subscription_id: str) -> bool:
    """
    Check if a user has existing subscriptions, excluding a specific one.

    Args:
        user: The user to check.
        exclude_subscription_id: Stripe subscription ID to exclude from the check.

    Returns:
        True if user has other subscriptions, False otherwise.
    """
    return UserSubscription.objects.filter(
        user=user
    ).exclude(
        stripe_subscription_id=exclude_subscription_id
    ).exists()


def _generate_and_set_password(user: User) -> tuple[HttpResponse | None, str | None]:
    """
    Generate a random password and set it for the user.

    Args:
        user: The user to set the password for.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and password,
        or None and password on success.
    """
    try:
        random_password = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(8)
        )
        user.set_password(random_password)
        user.save()
        return None, random_password
    except Exception as error:
        return exception_error(error), None


def _send_lexa_user_creation_email(
    user: User,
    password: str
) -> HttpResponse | None:
    """
    Send user creation email for LEXA subscription type.

    Args:
        user: The user to send the email to.
        password: The generated password.

    Returns:
        Error response if sending fails, None otherwise.
    """
    return send_email(
        user.email,
        EmailType.USER_CREATED,
        user.language,
        {
            "lexa_username": user.username,
            "lexa_email": user.email,
            "lexa_password": password
        }
    )


def _send_subscription_creation_email(
    user: User,
    subscription_type: SubscriptionType,
    api_key: str
) -> HttpResponse | None:
    """
    Send subscription creation email based on product type.

    Args:
        user: The user to send the email to.
        subscription_type: The subscription type.
        api_key: The API key for API/ADDIN subscriptions.

    Returns:
        Error response if sending fails, None otherwise.
    """
    if subscription_type.product_type == SubscriptionType.ProductChoices.API:
        email_type = EmailType.API_CREATED
    else:  # ADDIN
        email_type = EmailType.ADDIN_CREATED

    return send_email(
        user.email,
        email_type,
        user.language,
        {
            "lexa_username": user.username,
            "lexa_email": user.email,
            "lexa_apikey": api_key
        }
    )


def _send_incomplete_subscription_notifications(
    buyer: User,
    subscription_type: SubscriptionType
) -> HttpResponse | None:
    """
    Send notifications to admins when subscription status is INCOMPLETE.

    Args:
        buyer: The buyer user.
        subscription_type: The subscription type.

    Returns:
        Error response if sending fails, None otherwise.
    """
    for admin in buyer.group.admin.all():
        error_response = _send_admin_notification_email(
            admin,
            buyer,
            EmailType.SUBSCRIPTION_NEED_PAYMENT_ADMIN,
            subscription_type
        )
        if error_response:
            return error_response
    return None


def _configure_subscription_cancellation_at_period_end(
    subscription_type: SubscriptionType,
    stripe_subscription_id: str
) -> HttpResponse | None:
    """
    Configure Stripe subscription to cancel at period end if required.

    If the subscription type has block_after_first_month enabled, this function
    configures the Stripe subscription to automatically cancel at the end of
    the current billing period.

    Args:
        subscription_type: The subscription type to check for cancellation setting.
        stripe_subscription_id: The Stripe subscription ID to modify.

    Returns:
        Error response if Stripe API call fails or API key is not configured, None otherwise.
    """
    if not subscription_type.block_after_first_month:
        return None

    api_key = settings.STRIPE_API_KEY
    if not api_key:
        return exception_error(
            ValueError("STRIPE_API_KEY is not configured")
        )

    try:
        stripe.Subscription.modify(
            stripe_subscription_id,
            cancel_at_period_end=True,
            api_key=api_key
        )
    except stripe.error.StripeError as error:
        return exception_error(error)

    return None


def handle_customer_subscription_created(payload: dict) -> HttpResponse:
    """
    Handle customer subscription created webhook event.

    This function processes the creation of a new subscription for a customer.
    It creates user subscriptions and sends appropriate notifications based on
    the subscription status.

    Args:
        payload (dict): The webhook payload containing subscription data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    error_response, stripe_subscription_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, stripe_customer_id = get_payload_customer_id(payload)
    if error_response:
        return error_response

    error_response, buyer = get_user_by_stripe_customer_id(stripe_customer_id)
    if error_response:
        return error_response

    error_response, item_data = get_payload_item_data(payload, 0)
    if error_response:
        return error_response

    error_response, start_time = get_item_data_current_period_start(item_data)
    if error_response:
        return error_response

    error_response, end_time = get_item_data_current_period_end(item_data)
    if error_response:
        return error_response

    error_response, stripe_product_id = get_item_data_product_id(item_data)
    if error_response:
        return error_response

    error_response, quantity = get_item_data_quantity(item_data)
    if error_response:
        return error_response

    error_response, subscription_type = get_subscriptionType_by_stripe_product_id(
        stripe_product_id
    )
    if error_response:
        return error_response

    error_response, subscription_item_id = get_item_data_subscription_item_id(item_data)
    if error_response:
        return error_response

    error_response, payload_status = get_payload_status(payload)
    if error_response:
        return error_response

    status = string_to_UserSubscriptionChoices(payload_status)

    # Check if user has existing subscriptions (excluding the one being created)
    is_new_user = not _has_existing_subscriptions(buyer, stripe_subscription_id)

    # Create user subscriptions
    error_response, userSubscriptions = create_userSubscriptions(
        stripe_customer_id=buyer.stripe_customer_id,
        subscription_type=subscription_type,
        stripe_subscription_id=stripe_subscription_id,
        stripe_subscription_item_id=subscription_item_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        buyer=buyer,
        is_buying=True,
        quantity=quantity
    )
    if error_response:
        return error_response

    # Configure subscription cancellation at period end if required
    error_response = _configure_subscription_cancellation_at_period_end(
        subscription_type,
        stripe_subscription_id
    )
    if error_response:
        return error_response

    # Send notifications for incomplete subscriptions
    if status == UserSubscription.UserSubscriptionChoices.INCOMPLETE:
        error_response = _send_incomplete_subscription_notifications(
            buyer,
            subscription_type
        )
        if error_response:
            return error_response

    # Handle subscription creation emails based on product type
    if subscription_type.product_type == SubscriptionType.ProductChoices.LEXA:
        # Only reset password and send email for new users
        if is_new_user:
            error_response, password = _generate_and_set_password(buyer)
            if error_response:
                return error_response

            error_response = _send_lexa_user_creation_email(buyer, password)
            if error_response:
                return error_response
    elif subscription_type.product_type in (
        SubscriptionType.ProductChoices.API,
        SubscriptionType.ProductChoices.ADDIN
    ):
        # Always send creation email for API and ADDIN subscriptions
        error_response = _send_subscription_creation_email(
            buyer,
            subscription_type,
            userSubscriptions[0].api_key
        )
        if error_response:
            return error_response

    return success_message(
        "customer_subscription_created",
        quantity=quantity,
        stripe_subscription_id=stripe_subscription_id,
        status=status,
        payload_status=payload_status
    )


def handle_customer_subscription_updated(payload: dict) -> HttpResponse:
    """
    Handle customer subscription updated webhook event.

    This function processes updates to an existing subscription, including
    status changes, quantity changes, and period updates. It manages user
    subscriptions and sends appropriate notifications.

    Args:
        payload (dict): The webhook payload containing updated subscription data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    error_response, stripe_subscription_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, user_subscription_list = get_userSubscriptions_list_by_stripe_subscription_id(
        stripe_subscription_id
    )
    if error_response:
        return error_response

    error_response, item_data = get_payload_item_data(payload, 0)
    if error_response:
        return error_response

    error_response, stripe_product_id = get_item_data_product_id(item_data)
    if error_response:
        return error_response

    error_response, subscription_type = get_subscriptionType_by_stripe_product_id(
        stripe_product_id
    )
    if error_response:
        return error_response

    error_response, quantity = get_item_data_quantity(item_data)
    if error_response:
        return error_response

    error_response, subscription_item_id = get_item_data_subscription_item_id(item_data)
    if error_response:
        return error_response

    error_response, end_time = get_payload_cancel_at(payload)
    if error_response:
        if error_response.exception is not None:
            return error_response
        else:
            # Fallback to current period end if cancel_at is not available
            error_response, end_time = get_item_data_current_period_end(
                item_data)
            if error_response:
                return error_response

    error_response, start_time = get_item_data_current_period_start(item_data)
    if error_response:
        return error_response

    error_response, payload_status = get_payload_status(payload)
    if error_response:
        return error_response

    error_response, active_user_subscription_list = get_userSubscriptions_list_active_from_userSubscription_list(
        user_subscription_list
    )
    if error_response:
        return error_response

    error_response, buyer = get_buyer_from_userSubscription_list(
        user_subscription_list)
    if error_response:
        return error_response

    status = string_to_UserSubscriptionChoices(payload_status)
    old_quantity = len(active_user_subscription_list)
    group_admins = list(buyer.group.admin.all())

    # Update existing subscriptions with new values
    error_response, emailType_list, did_changed, changed_fields = set_new_userSubscription_list_values(
        active_user_subscription_list,
        {
            "end_date": end_time,
            "status": status,
            "stripe_subscription_item_id": subscription_item_id,
            "subscription": subscription_type,
        }
    )
    if error_response:
        return error_response

    # Handle quantity changes
    if quantity > old_quantity:
        # Need to create additional subscriptions
        did_changed = True
        error_response, _ = create_userSubscriptions(
            stripe_customer_id=buyer.stripe_customer_id,
            buyer=buyer,
            subscription_type=subscription_type,
            stripe_subscription_id=stripe_subscription_id,
            stripe_subscription_item_id=subscription_item_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            is_buying=False,
            quantity=quantity - old_quantity
        )
        if error_response:
            return error_response

    elif quantity < old_quantity:
        # Need to deactivate excess subscriptions
        did_changed = True
        deactivated_user_subscription_list = sorted(
            (us for us in active_user_subscription_list if us.user != buyer),
            key=lambda us: us.user in group_admins
        )[:old_quantity - quantity]

        error_response, _ = deactivate_userSubscriptions(
            deactivated_user_subscription_list,
            end_time
        )
        if error_response:
            return error_response

    # Track quantity change for email notifications
    if quantity != old_quantity:
        emailType_list.append(EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN)

    # Send email notifications
    if EmailType.SUBSCRIPTION_UPDATED_INACTIVE in emailType_list:
        error_response = _send_inactive_subscription_notifications(
            active_user_subscription_list,
            group_admins,
            subscription_type,
            buyer
        )
        if error_response:
            return error_response

    if EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN in emailType_list:
        error_response = _send_quantity_change_notifications(
            group_admins,
            buyer,
            subscription_type,
            quantity
        )
        if error_response:
            return error_response

    # Return success response
    if not did_changed:
        return success_message(
            "customer_subscription_identical",
            stripe_subscription_id=stripe_subscription_id
        )

    changed_fields_str = _format_changed_fields_message(
        changed_fields,
        old_quantity,
        quantity
    )

    return success_message(
        "customer_subscription_updated",
        quantity=quantity,
        stripe_subscription_id=stripe_subscription_id,
        status=status,
        payload_status=payload_status,
        changed_fields=changed_fields_str
    )


def handle_customer_subscription_deleted(payload: dict) -> HttpResponse:
    """
    Handle customer subscription deleted webhook event.

    This function processes the deletion of a subscription, deactivating
    all related user subscriptions and sending appropriate notifications
    to affected users and administrators.

    Args:
        payload (dict): The webhook payload containing subscription deletion data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    error_response, stripe_subscription_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, user_subscription_list = get_userSubscriptions_list_by_stripe_subscription_id(
        stripe_subscription_id
    )
    if error_response:
        return error_response

    error_response, cancel_at = get_payload_ended_at(payload)
    if error_response:
        return error_response

    error_response, buyer = get_buyer_from_userSubscription_list(
        user_subscription_list)
    if error_response:
        return error_response

    error_response, changed_list = deactivate_userSubscriptions(
        user_subscription_list,
        cancel_at
    )

    quantity = len(user_subscription_list)

    # Send notifications to affected users
    for i in range(quantity):
        if changed_list[i]:
            user = user_subscription_list[i].user

            param = {
                "lexa_username": user.username,
                "stripe_subscription_type": user_subscription_list[i].subscription.name,
                "lexa_company_name": user.group.name,
            }

            if user not in buyer.group.admin.all():
                email_type = EmailType.SUBSCRIPTION_DELETED
            else:
                # Admin users get additional context and session link
                email_type = EmailType.SUBSCRIPTION_DELETED_ADMIN
                error_response, session_link = get_stripe_customer_session_url(
                    buyer.stripe_customer_id
                )
                if error_response:
                    return error_response
                param["stripe_session_link"] = session_link
            error_response = send_email(
                user.email, email_type, user.language, param)
            if error_response:
                return error_response

    return success_message(
        "customer_subscription_deleted",
        quantity=quantity,
        stripe_subscription_id=stripe_subscription_id
    )


def handle_customer_subscription_trials_will_end(payload: dict) -> HttpResponse:
    """
    Handle customer subscription trial will end webhook event.

    This function processes notifications for subscriptions that are about
    to end their trial period, sending appropriate notifications to users
    and administrators.

    Args:
        payload (dict): The webhook payload containing trial end data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    error_response, stripe_subscription_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, stripe_customer_id = get_payload_customer_id(payload)
    if error_response:
        return error_response

    error_response, user_subscription_list = get_userSubscriptions_list_by_stripe_subscription_id(
        stripe_subscription_id
    )
    if error_response:
        return error_response

    error_response, buyer = get_user_by_stripe_customer_id(stripe_customer_id)
    if error_response:
        return error_response

    # Collect users without email addresses
    user_not_email_list = [
        us.user for us in user_subscription_list if not us.user.email
    ]

    # Send trial end notifications to users with email addresses
    for user_subscription in user_subscription_list:
        user = user_subscription.user
        if user not in user_not_email_list:
            param = {
                "lexa_username": user.username,
                "stripe_subscription_type": user_subscription.subscription.name,
            }

            if user not in buyer.group.admin.all():
                error_response = send_email(
                    user.email,
                    EmailType.SUBSCRIPTION_TRIALS_WILL_END,
                    user.language,
                    param
                )
            else:
                error_response = send_email(
                    user.email,
                    EmailType.SUBSCRIPTION_TRIALS_WILL_END_ADMIN,
                    user.language,
                    param
                )
            if error_response:
                return error_response

    # Handle case where some users don't have email addresses
    if len(user_not_email_list) > 0:
        return success_message(
            "customer_subscription_trial_will_end_no_email",
            username_list=', '.join(
                [user.username for user in user_not_email_list])
        )
    return success_message("customer_subscription_trial_will_end")


CUSTOMER_SUBSCRIPTION_EVENT_HANDLERS = {
    "customer.subscription.created": handle_customer_subscription_created,
    "customer.subscription.updated": handle_customer_subscription_updated,
    "customer.subscription.deleted": handle_customer_subscription_deleted,
    "customer.subscription.trial_will_end": handle_customer_subscription_trials_will_end,
}
