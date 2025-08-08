"""
Customer subscription webhook handlers for Stripe webhooks.

This module handles webhook events related to customer subscription operations,
including creation, updates, deletions, and trial end notifications for subscriptions.
"""

from emails.models import EmailType
from emails.send_email import send_email
from subscriptions.models import UserSubscription

from .error.error import HttpResponse, success_message
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

    error_response, payload_status = get_payload_status(payload)
    if error_response:
        return error_response

    status = string_to_UserSubscriptionChoices(payload_status)

    error_response, _ = create_userSubscriptions(
        stripe_customer_id=buyer.stripe_customer_id,
        subscription_type=subscription_type,
        stripe_subscription_id=stripe_subscription_id,
        start_time=start_time,
        end_time=end_time,
        status=status,
        buyer=buyer,
        is_buying=True,
        quantity=quantity
    )
    if error_response:
        return error_response

    if status == UserSubscription.UserSubscriptionChoices.INCOMPLETE:
        for admin in buyer.group.admin.all():
            error_response, session_link = get_stripe_customer_session_url(
                buyer.stripe_customer_id
            )
            if error_response:
                return error_response

            error_response = send_email(
                admin.email,
                EmailType.SUBSCRIPTION_NEED_PAYMENT_ADMIN,
                admin.language,
                {
                    "lexa_company_name": buyer.group.name,
                    "stripe_subscription_type": subscription_type.name,
                    "stripe_session_link": session_link
                }
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
    group_admins = buyer.group.admin.all()

    # Update existing subscriptions with new values
    error_response, emailType_list, did_changed = set_new_userSubscription_list_values(
        active_user_subscription_list,
        {
            "end_date": end_time,
            "status": status
        }
    )
    if error_response:
        return error_response

    if quantity > old_quantity:
        # Need to create additional subscriptions
        did_changed = True
        error_response, _ = create_userSubscriptions(
            stripe_customer_id=buyer.stripe_customer_id,
            buyer=buyer,
            subscription_type=subscription_type,
            stripe_subscription_id=stripe_subscription_id,
            start_time=start_time,
            end_time=end_time,
            status=status,
            is_buying=False,
            quantity=quantity - old_quantity
        )
        if error_response:
            return error_response

    if quantity < old_quantity:
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

    if quantity != old_quantity:
        emailType_list.append(EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN)

    group_admins = buyer.group.admin.all()

    # Handle subscription inactive notifications
    if EmailType.SUBSCRIPTION_UPDATED_INACTIVE in emailType_list:
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
            error_response, session_link = get_stripe_customer_session_url(
                buyer.stripe_customer_id
            )
            if error_response:
                return error_response

            error_response = send_email(
                admin.email,
                EmailType.SUBSCRIPTION_UPDATED_INACTIVE_ADMIN,
                admin.language,
                {
                    "lexa_company_name": admin.group.name,
                    "lexa_username": admin.username,
                    "stripe_subscription_type": subscription_type.name,
                    "stripe_session_link": session_link
                }
            )
            if error_response:
                return error_response

    # Handle quantity change notifications
    if EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN in emailType_list:
        for admin in group_admins:
            error_response, session_link = get_stripe_customer_session_url(
                buyer.stripe_customer_id
            )
            if error_response:
                return error_response

            error_response = send_email(
                admin.email,
                EmailType.SUBSCRIPTION_UPDATED_QUANTITY_ADMIN,
                admin.language,
                {
                    "lexa_company_name": admin.group.name,
                    "lexa_username": admin.username,
                    "stripe_subscription_type": subscription_type.name,
                    "quantity": quantity,
                    "stripe_session_link": session_link
                }
            )
            if error_response:
                return error_response

    if not did_changed:
        return success_message(
            "customer_subscription_identical",
            stripe_subscription_id=stripe_subscription_id
        )
    else:
        return success_message(
            "customer_subscription_updated",
            quantity=quantity,
            stripe_subscription_id=stripe_subscription_id,
            status=status,
            payload_status=payload_status
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
