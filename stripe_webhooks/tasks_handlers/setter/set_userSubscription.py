"""
User subscription management handlers.

This module provides functions for creating, updating, and deactivating
user subscriptions in the Stripe webhook system.
"""

from datetime import datetime

from django.db import transaction

from emails.models import EmailType
from subscriptions.models import UserSubscription, SubscriptionType
from subscriptions.permissions import is_user_subscription_active
from users.models import User

from ..error.error import HttpResponse, exception_error
from ..setter.set_user import create_user, deactivate_user


def create_userSubscriptions(
    stripe_customer_id: str,
    subscription_type: SubscriptionType,
    stripe_subscription_id: str,
    stripe_subscription_item_id: str,
    start_time: datetime,
    end_time: datetime,
    status: str,
    buyer: User,
    is_buying: bool = False,
    quantity: int = 1
) -> tuple[HttpResponse | None, list[UserSubscription] | None]:
    """
    Create multiple user subscriptions for a given subscription type.

    This function creates user subscriptions based on the quantity specified.
    If is_buying is True, the first subscription is assigned to the buyer.
    Additional subscriptions create new users in the same group.

    Args:
        stripe_customer_id (str): The Stripe customer identifier.
        subscription_type (SubscriptionType): The type of subscription to create.
        stripe_subscription_id (str): The Stripe subscription identifier.
        start_time (datetime): The subscription start date.
        end_time (datetime): The subscription end date.
        status (str): The subscription status.
        buyer (User): The user who purchased the subscription.
        is_buying (bool, optional): Whether the buyer gets the first subscription.
                                   Defaults to False.
        quantity (int, optional): Number of subscriptions to create. Defaults to 1.

    Returns:
        tuple[HttpResponse | None, list[UserSubscription] | None]: Error response
        and list of created subscriptions, or None and subscriptions on success.
    """
    try:
        with transaction.atomic():
            for i in range(quantity):
                if i == 0 and is_buying:
                    user = buyer
                else:
                    error_response, user, _ = create_user(
                        stripe_customer_id=stripe_customer_id,
                        language=buyer.language,
                        group=buyer.group,
                        is_buyer=False
                    )
                    if error_response:
                        return error_response, None
                    user.save()

                user_subscription = UserSubscription.objects.create(
                    user=user,
                    subscription=subscription_type,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_subscription_item_id=stripe_subscription_item_id,
                    start_date=start_time,
                    end_date=end_time,
                    status=status
                )
                user_subscription.save()

    except Exception as error:
        return exception_error(error), None

    return None, UserSubscription.objects.filter(
        stripe_subscription_id=stripe_subscription_id
    )


def set_new_userSubscription_list_values(
    userSubscription_list: list[UserSubscription],
    new_values: dict
) -> tuple[HttpResponse | None, list[EmailType], bool]:
    """
    Update a list of user subscriptions with new values.

    This function updates subscription end dates, statuses, and Stripe item IDs
    for multiple subscriptions. It tracks which email types should be sent based on
    status changes and whether any changes were made.

    Args:
        userSubscription_list (list[UserSubscription]): List of subscriptions
                                                        to update.
        new_values (dict): Dictionary containing new values to apply.
                          Can include 'end_date', 'status', and 'stripe_subscription_item_id'.

    Returns:
        tuple[HttpResponse | None, list[EmailType], bool]: Error response,
        list of email types to send, and boolean indicating if changes were made.
    """
    email_types: list[EmailType] = []

    try:
        global_changed = False
        for user_subscription in userSubscription_list:
            changed = False

            # Update end date if provided
            if 'end_date' in new_values:
                new_end = new_values['end_date'].astimezone(
                    user_subscription.end_date.tzinfo
                )
                if new_end != user_subscription.end_date:
                    user_subscription.end_date = new_values['end_date']
                    changed = True

            # Update status if provided and different
            if ('status' in new_values and
                    new_values['status'] != user_subscription.status):
                user_subscription.status = new_values['status']
                changed = True

            if ('stripe_subscription_item_id' in new_values and
                    new_values['stripe_subscription_item_id'] != user_subscription.stripe_subscription_item_id):
                user_subscription.stripe_subscription_item_id = new_values['stripe_subscription_item_id']
                changed = True

            if changed:
                user_subscription.save()
                global_changed = True

            # Deactivate user if subscription becomes inactive
            if not is_user_subscription_active(user_subscription.status):
                user_subscription.user.is_active = False
                if EmailType.SUBSCRIPTION_UPDATED_INACTIVE not in email_types:
                    email_types.append(EmailType.SUBSCRIPTION_UPDATED_INACTIVE)

    except Exception as error:
        return exception_error(error), [], False

    return None, email_types, global_changed


def deactivate_userSubscription(
    user_subscription: UserSubscription,
    cancel_at: datetime
) -> tuple[HttpResponse | None, bool]:
    """
    Deactivate a single user subscription.

    This function terminates an active subscription by updating its status
    and end date, and deactivates the associated user.

    Args:
        user_subscription (UserSubscription): The subscription to deactivate.
        cancel_at (datetime): The cancellation date to set as end date.

    Returns:
        tuple[HttpResponse | None, bool]: Error response and boolean indicating
        if the subscription was actually changed.
    """
    try:
        if is_user_subscription_active(user_subscription.status):
            user_subscription.status = (
                UserSubscription.UserSubscriptionChoices.TERMINATED
            )
            user_subscription.end_date = cancel_at

            error_response = deactivate_user(user_subscription.user)
            if error_response:
                return error_response, False

            user_subscription.save()
            return None, True
        else:
            return None, False

    except Exception as error:
        return exception_error(error), False


def deactivate_userSubscriptions(
    userSubscription_list: list[UserSubscription],
    cancel_at: datetime
) -> tuple[HttpResponse | None, list[bool]]:
    """
    Deactivate multiple user subscriptions.

    This function processes a list of subscriptions and deactivates each one
    individually, collecting the results of each operation.

    Args:
        userSubscription_list (list[UserSubscription]): List of subscriptions
                                                        to deactivate.
        cancel_at (datetime): The cancellation date to apply to all subscriptions.

    Returns:
        tuple[HttpResponse | None, list[bool]]: Error response and list of
        booleans indicating which subscriptions were actually changed.
    """
    changed = []

    try:
        for user_subscription in userSubscription_list:
            error_response, did_changed = deactivate_userSubscription(
                user_subscription=user_subscription,
                cancel_at=cancel_at
            )
            if error_response:
                return error_response, []

            changed.append(did_changed)

    except Exception as error:
        return exception_error(error), []

    return None, changed


def reset_userSubscription_counts(
    user_subscription: UserSubscription
) -> tuple[HttpResponse | None, UserSubscription | None]:
    """
    Reset the translation counters for a given UserSubscription.

    This function sets translated_symbols_count, translated_words_count, and translated_files_count to zero
    for the provided UserSubscription and saves the changes.

    Args:
        user_subscription (UserSubscription): The subscription whose counters will be reset.

    Returns:
        tuple[HttpResponse | None, UserSubscription | None]:
            Error response and None if an error occurs, otherwise None and the updated UserSubscription.
    """
    try:
        user_subscription.translated_symbols_count = 0
        user_subscription.translated_words_count = 0
        user_subscription.translated_files_count = 0
        user_subscription.save()
        return None, user_subscription

    except Exception as error:
        return exception_error(error), None
