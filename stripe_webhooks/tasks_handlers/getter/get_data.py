"""
Database data retrieval utilities.

This module provides functions for retrieving and validating data from
the database, including users, subscriptions, groups, and related entities
used in the Stripe webhook system.
"""

from subscriptions.models import SubscriptionType, UserSubscription
from subscriptions.permissions import is_user_subscription_active
from users.models import User, UserGroup

from ..error.error import HttpResponse, error_message, exception_error


def get_user_by_stripe_customer_id(stripe_customer_id: str) -> tuple[HttpResponse | None, User | None]:
    """
    Retrieve a user by their Stripe customer ID.

    Args:
        stripe_customer_id (str): The Stripe customer identifier.

    Returns:
        tuple[HttpResponse | None, User | None]: Error response and user,
        or None and user on success.
    """
    try:
        return None, User.objects.get(stripe_customer_id=stripe_customer_id)
    except User.DoesNotExist:
        return error_message(
            "not_found_user_by_stripe_customer_id",
            stripe_customer_id=stripe_customer_id
        ), None
    except Exception as error:
        return exception_error(error), None


def get_subscriptionType_by_stripe_product_id(
    stripe_product_id: str
) -> tuple[HttpResponse | None, SubscriptionType | None]:
    """
    Retrieve a subscription type by Stripe product ID.

    Args:
        stripe_product_id (str): The Stripe product identifier.

    Returns:
        tuple[HttpResponse | None, SubscriptionType | None]: Error response
        and subscription type, or None and subscription type on success.
    """
    try:
        return None, SubscriptionType.objects.get(stripe_product_id=stripe_product_id)
    except SubscriptionType.DoesNotExist:
        return error_message(
            "not_found_subscriptionType_by_stripe_product_id",
            stripe_product_id=stripe_product_id
        ), None
    except Exception as error:
        return exception_error(error), None


def get_userSubscriptions_list_by_stripe_subscription_id(
    stripe_subscription_id: str
) -> tuple[HttpResponse | None, list[UserSubscription] | None]:
    """
    Retrieve a list of user subscriptions by Stripe subscription ID.

    Args:
        stripe_subscription_id (str): The Stripe subscription identifier.

    Returns:
        tuple[HttpResponse | None, list[UserSubscription] | None]: Error response
        and subscription list, or None and subscription list on success.
    """
    try:
        user_subscriptions_list = UserSubscription.objects.filter(
            stripe_subscription_id=stripe_subscription_id
        )
        if user_subscriptions_list.exists():
            return None, list(user_subscriptions_list)
        else:
            return error_message(
                "not_found_userSubscription_by_stripe_subscription_id",
                stripe_subscription_id=stripe_subscription_id
            ), None
    except Exception as error:
        return exception_error(error), None


def get_userGroup_by_group_name(group_name: str) -> tuple[HttpResponse | None, UserGroup | None]:
    """
    Retrieve a user group by its name.

    Args:
        group_name (str): The name of the group to retrieve.

    Returns:
        tuple[HttpResponse | None, UserGroup | None]: Error response and group,
        or None and group on success.
    """
    try:
        return None, UserGroup.objects.get(name=group_name)
    except UserGroup.DoesNotExist:
        return error_message(
            "not_found_userGroup_by_group_name",
            group_name=group_name
        ), None
    except Exception as error:
        return exception_error(error), None


def get_userGroup_by_id(group_id: str) -> tuple[HttpResponse | None, UserGroup | None]:
    """
    Retrieve a user group by its ID.

    Args:
        group_id (str): The ID of the group to retrieve.

    Returns:
        tuple[HttpResponse | None, UserGroup | None]: Error response and group,
        or None and group on success.
    """
    try:
        return None, UserGroup.objects.get(id=group_id)
    except UserGroup.DoesNotExist:
        return error_message(
            "not_found_userGroup_by_id",
            group_id=group_id
        ), None
    except Exception as error:
        return exception_error(error), None


def get_user_count_from_userGroup_by_group_id(
    group_id: int
) -> tuple[HttpResponse | None, int | None]:
    """
    Get the count of users in a specific group.

    Args:
        group_id (int): The ID of the group to count users for.

    Returns:
        tuple[HttpResponse | None, int | None]: Error response and user count,
        or None and user count on success.
    """
    try:
        user_count = User.objects.filter(group_id=group_id).count()
        if user_count > 0:
            return None, user_count
        else:
            return error_message(
                "user_count_from_userGroup_by_group_id",
                group_id=group_id
            ), None
    except Exception as error:
        return exception_error(error), None


def get_groupSubscription_list_from_group_id(group_id: int):
    """
    Placeholder function for group subscription retrieval.

    This function is currently not implemented and returns an error.
    The commented code shows the intended implementation for future use.

    Args:
        group_id (int): The ID of the group.

    Returns:
        tuple[HttpResponse, None]: Always returns an exception error.
    """
    return exception_error(None), None


def get_userSubscriptions_list_active_from_userSubscription_list(
    user_subscription_list: list[UserSubscription]
) -> tuple[HttpResponse | None, list[UserSubscription] | None]:
    """
    Filter active subscriptions from a list of user subscriptions.

    Args:
        user_subscription_list (list[UserSubscription]): List of user subscriptions
                                                         to filter.

    Returns:
        tuple[HttpResponse | None, list[UserSubscription] | None]: Error response
        and active subscriptions, or None and active subscriptions on success.
    """
    active_user_subscription_list = [
        us for us in user_subscription_list
        if is_user_subscription_active(us.status)
    ]

    if not active_user_subscription_list:
        stripe_subscription_id = (
            user_subscription_list[0].stripe_subscription_id
            if user_subscription_list else None
        )
        return error_message(
            "not_found_userSubscriptions_active",
            stripe_subscription_id=stripe_subscription_id
        ), None

    return None, active_user_subscription_list


def get_buyer_from_userSubscription_list(
    user_subscription_list: list[UserSubscription]
) -> tuple[HttpResponse | None, User | None]:
    """
    Extract the buyer user from a list of user subscriptions.

    The buyer is identified as the user with a non-null stripe_customer_id.
    There should be exactly one buyer per subscription list.

    Args:
        user_subscription_list (list[UserSubscription]): List of user subscriptions
                                                         to search for buyer.

    Returns:
        tuple[HttpResponse | None, User | None]: Error response and buyer user,
        or None and buyer user on success.
    """
    buyers_with_stripe_id = [
        us.user for us in user_subscription_list
        if us.user.stripe_customer_id is not None
    ]

    if len(buyers_with_stripe_id) != 1:
        stripe_subscription_id = (
            user_subscription_list[0].stripe_subscription_id
            if user_subscription_list else None
        )
        return error_message(
            "buyer_count_from_userSubscription_list",
            strip_subscription_id=stripe_subscription_id,
            found_amount=len(buyers_with_stripe_id)
        ), None

    return None, buyers_with_stripe_id[0]


def get_stripe_subscription_id_from_user(user: User) -> tuple[HttpResponse | None, str | None]:
    """
    Retrieve the Stripe subscription ID from a user's subscription.

    This function finds the user's subscriptions and returns the Stripe subscription ID.
    If the user has multiple subscriptions, it returns an error.
    If the user has no subscriptions, it returns an error.

    Args:
        user (User): The user to get the subscription ID for.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and subscription ID,
        or None and subscription ID on success.
    """
    try:
        # Get all user subscriptions
        subscriptions = UserSubscription.objects.filter(user=user)

        if not subscriptions.exists():
            return error_message(
                "not_found_subscription_for_user",
                user_stripe_customer_id=user.stripe_customer_id
            ), None

        # Check if user has multiple subscriptions
        if subscriptions.count() > 1:
            return error_message(
                "multiple_subscriptions_found_for_user",
                user_stripe_customer_id=user.stripe_customer_id,
                subscription_count=subscriptions.count()
            ), None

        # Get the single subscription
        subscription = subscriptions.first()
        if not subscription.stripe_subscription_id:
            return error_message(
                "no_stripe_subscription_id_for_user",
                user_stripe_customer_id=user.stripe_customer_id,
            ), None

        return None, subscription.stripe_subscription_id

    except Exception as error:
        return exception_error(error), None
