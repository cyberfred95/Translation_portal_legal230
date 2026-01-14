"""
User subscription management handlers.

This module provides functions for creating, updating, and deactivating
user subscriptions in the Stripe webhook system.
"""

from datetime import datetime
from typing import Any

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
    interval: str,
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
        interval (str): The billing interval (day, week, month, or year).
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

                UserSubscription.objects.create(
                    user=user,
                    subscription=subscription_type,
                    stripe_subscription_id=stripe_subscription_id,
                    stripe_subscription_item_id=stripe_subscription_item_id,
                    start_date=start_time,
                    end_date=end_time,
                    status=status,
                    interval=interval
                )

    except Exception as error:
        return exception_error(error), None

    return None, UserSubscription.objects.filter(
        stripe_subscription_id=stripe_subscription_id
    )


def _update_subscription_type_and_limits(
    user_subscription: UserSubscription,
    new_subscription_type: SubscriptionType,
    changed_fields: set[str]
) -> bool:
    """
    Update subscription type and copy limits from the new SubscriptionType.

    Args:
        user_subscription: The subscription to update.
        new_subscription_type: The new SubscriptionType to apply.
        changed_fields: Set to track which fields were changed.

    Returns:
        bool: True if subscription type was changed, False otherwise.
    """
    if user_subscription.subscription == new_subscription_type:
        return False

    user_subscription.subscription = new_subscription_type
    user_subscription.max_symbols_count = new_subscription_type.max_symbols_count
    user_subscription.max_words_count = new_subscription_type.max_words_count
    user_subscription.max_files_count = new_subscription_type.max_files_count
    user_subscription.custom_glossaries_count = new_subscription_type.custom_glossaries_count

    changed_fields.add('subscription')
    changed_fields.add('limits')
    return True


def _add_field_if_changed(
    field_name: str,
    old_value: Any,
    new_value: Any,
    changed_fields: set[str]
) -> bool:
    """
    Add field name to changed_fields set if values differ.

    Args:
        field_name: Name of the field being checked.
        old_value: Current value.
        new_value: New value to compare.
        changed_fields: Set to track changed fields.

    Returns:
        bool: True if values differ, False otherwise.
    """
    if old_value != new_value:
        changed_fields.add(field_name)
        return True
    return False


def _update_simple_field(
    user_subscription: UserSubscription,
    field_name: str,
    new_value: Any,
    changed_fields: set[str]
) -> bool:
    """
    Update a simple field on user_subscription if the value has changed.

    Args:
        user_subscription: The subscription to update.
        field_name: Name of the field to update.
        new_value: New value to set.
        changed_fields: Set to track changed fields.

    Returns:
        bool: True if field was updated, False otherwise.
    """
    old_value = getattr(user_subscription, field_name)
    if _add_field_if_changed(field_name, old_value, new_value, changed_fields):
        setattr(user_subscription, field_name, new_value)
        return True
    return False


def set_new_userSubscription_list_values(
    userSubscription_list: list[UserSubscription],
    new_values: dict
) -> tuple[HttpResponse | None, list[EmailType], bool, list[str]]:
    """
    Update a list of user subscriptions with new values.

    This function updates subscription end dates, statuses, Stripe item IDs,
    and subscription types for multiple subscriptions. It tracks which email types
    should be sent based on status changes and whether any changes were made.
    
    When the subscription type changes, it automatically updates the limits
    (max_symbols_count, max_words_count, max_files_count, custom_glossaries_count)
    from the new SubscriptionType.

    Args:
        userSubscription_list: List of subscriptions to update.
        new_values: Dictionary containing new values to apply.
                   Can include 'end_date', 'status', 'stripe_subscription_item_id',
                   'interval', and 'subscription' (SubscriptionType).
                   When 'subscription' is provided and different, limits are
                   automatically copied from the new SubscriptionType.

    Returns:
        tuple containing:
        - Error response (None if success)
        - List of email types to send
        - Boolean indicating if changes were made
        - List of changed field names
    """
    email_types: list[EmailType] = []
    changed_fields: set[str] = set()

    try:
        global_changed = False
        for user_subscription in userSubscription_list:
            subscription_changed = False

            # Update subscription type if provided and different
            if 'subscription' in new_values:
                if _update_subscription_type_and_limits(
                    user_subscription,
                    new_values['subscription'],
                    changed_fields
                ):
                    subscription_changed = True

            # Update end date if provided
            if 'end_date' in new_values:
                new_end = new_values['end_date'].astimezone(
                    user_subscription.end_date.tzinfo
                )
                if _add_field_if_changed(
                    'end_date',
                    user_subscription.end_date,
                    new_end,
                    changed_fields
                ):
                    user_subscription.end_date = new_end
                    subscription_changed = True

            # Update status if provided and different
            if 'status' in new_values:
                if _update_simple_field(
                    user_subscription,
                    'status',
                    new_values['status'],
                    changed_fields
                ):
                    subscription_changed = True

            # Update stripe subscription item ID if provided and different
            if 'stripe_subscription_item_id' in new_values:
                if _update_simple_field(
                    user_subscription,
                    'stripe_subscription_item_id',
                    new_values['stripe_subscription_item_id'],
                    changed_fields
                ):
                    subscription_changed = True

            # Update interval if provided and different
            if 'interval' in new_values:
                if _update_simple_field(
                    user_subscription,
                    'interval',
                    new_values['interval'],
                    changed_fields
                ):
                    subscription_changed = True

            if subscription_changed:
                user_subscription.save()
                global_changed = True

            # Track email types for inactive subscriptions
            if not is_user_subscription_active(user_subscription.status):
                user_subscription.user.is_active = False
                if EmailType.SUBSCRIPTION_UPDATED_INACTIVE not in email_types:
                    email_types.append(EmailType.SUBSCRIPTION_UPDATED_INACTIVE)

    except Exception as error:
        return exception_error(error), [], False, []

    return None, email_types, global_changed, sorted(changed_fields)


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
    Also resets the technical_maximum_symbol_removed flag to False.

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
        user_subscription.technical_maximum_symbol_removed = False
        user_subscription.save(update_fields=[
            'translated_symbols_count',
            'translated_words_count',
            'translated_files_count',
            'technical_maximum_symbol_removed'
        ])
        return None, user_subscription

    except Exception as error:
        return exception_error(error), None
