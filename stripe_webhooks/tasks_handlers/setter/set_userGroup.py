"""
User group management handlers.

This module provides functions for creating and managing user groups
in the Stripe webhook system.
"""

from django.conf import settings

from users.models import UserGroup

from ..error.error import HttpResponse, exception_error
from ..getter.get_data import get_userGroup_by_group_name


def create_userGroup(group_name: str) -> tuple[HttpResponse | None, UserGroup | None]:
    """
    Create a new user group with the specified name.

    This function creates a new UserGroup object with the provided name
    and assigns the default API key from settings.

    Args:
        group_name (str): The name for the new group.

    Returns:
        tuple[HttpResponse | None, UserGroup | None]: Error response and
        created group, or None and group on success.
    """
    try:
        group = UserGroup.objects.create(
            name=group_name,
            api_key=settings.LEXA_API_GROUP_DEFAULT_API_KEY
        )
        return None, group

    except Exception as error:
        return exception_error(error), None


def create_userGroup_if_not_exists(
    group_name: str
) -> tuple[HttpResponse | None, UserGroup | None, bool | None]:
    """
    Create a user group if it doesn't already exist.

    This function checks if a group with the given name already exists.
    If it doesn't exist, it creates a new group. If it exists, it returns
    the existing group.

    Args:
        group_name (str): The name of the group to create or retrieve.

    Returns:
        tuple[HttpResponse | None, UserGroup | None, bool | None]: Error response,
        group object, and boolean indicating if the group was found (True) or
        created (False). Returns None values on error.
    """
    is_group_founded = False
    group_name_upper = group_name.upper()

    try:
        error_response, group = get_userGroup_by_group_name(group_name_upper)

        if error_response:
            # Group doesn't exist, create it
            if error_response.exception is not None:
                return error_response, None, None

            error_response, group = create_userGroup(group_name_upper)
            if error_response:
                return error_response, None, None

            group.save()
        else:
            # Group already exists
            is_group_founded = True

        return None, group, is_group_founded

    except Exception as error:
        return exception_error(error), None, None
