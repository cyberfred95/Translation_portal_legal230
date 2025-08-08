"""
Data conversion utilities.

This module provides utility functions for converting between different data formats
and types used in the Stripe webhook system, including subscription status mapping,
timestamp conversion, and name formatting.
"""

from datetime import datetime

from pytz import timezone as pytz_timezone

from subscriptions.models import UserSubscription
from users.models import UserGroup


def string_to_UserSubscriptionChoices(status: str):
    """
    Convert a string status to UserSubscriptionChoices enum.

    This function handles the conversion of string statuses (typically from Stripe)
    to the corresponding UserSubscriptionChoices enum values. It includes special
    handling for 'canceled' status which maps to 'TERMINATED'.

    Args:
        status (str): The status string to convert.

    Returns:
        UserSubscriptionChoices: The corresponding enum value, or UNKNOWN if
        no match is found.
    """
    # Special mapping for 'canceled' to 'TERMINATED'
    if status.strip().upper() == 'CANCELED':
        return UserSubscription.UserSubscriptionChoices.TERMINATED

    normalized = status.strip().replace('-', '_').upper()
    
    try:
        return UserSubscription.UserSubscriptionChoices[normalized]
    except KeyError:
        return UserSubscription.UserSubscriptionChoices.UNKNOWN


def int_to_DateTimeField(timestamp: int | None) -> datetime | None:
    """
    Convert a Unix timestamp to a timezone-aware datetime object.

    This function converts Unix timestamps (typically from Stripe API responses)
    to datetime objects in the Europe/Paris timezone.

    Args:
        timestamp (int | None): The Unix timestamp to convert, or None.

    Returns:
        datetime | None: The converted datetime object in Europe/Paris timezone,
        or None if the input timestamp is None.
    """
    if timestamp is None:
        return None
        
    return datetime.fromtimestamp(timestamp, tz=pytz_timezone("Europe/Paris"))


def dict_to_pair_list(data: dict) -> list:
    """
    Convert a dictionary to a list of key-value pairs.

    This function transforms a dictionary into a list of dictionaries,
    each containing 'key' and 'value' fields.

    Args:
        data (dict): The dictionary to convert.

    Returns:
        list: A list of dictionaries with 'key' and 'value' fields.
    """
    return [{"key": key, "value": value} for key, value in data.items()]


def user_name_to_group_name(user: UserGroup) -> str:
    """
    Generate a group name from a user's first and last name.

    This function creates a formatted group name by combining the user's
    first and last names in uppercase. If no last name is provided,
    only the first name is used.

    Args:
        user (UserGroup): The user object containing first_name and last_name.

    Returns:
        str: The formatted group name in uppercase.
    """
    if user.last_name:
        return f"{user.first_name} {user.last_name}".upper()
    else:
        return user.first_name.upper()


def group_name_to_user_name(group_name: str) -> tuple[str, str]:
    """
    Split a group name into first and last name components.

    This function parses a group name string and splits it into
    first and last name components for user creation.

    Args:
        group_name (str): The group name to split.

    Returns:
        tuple[str, str]: A tuple containing (first_name, last_name).
        If no space is found, returns (group_name, "").
    """
    if group_name and " " in group_name:
        parts = group_name.split(" ", 1)
        return (parts[0], parts[1])
    else:
        return (group_name, "")
