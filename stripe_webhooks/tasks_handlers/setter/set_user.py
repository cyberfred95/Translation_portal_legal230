"""
User management handlers.

This module provides functions for creating and managing users
in the Stripe webhook system.
"""

import random
import string

from users.models import User

from ..error.error import HttpResponse, exception_error


def create_user(
    stripe_customer_id: str,
    email: str = None,
    language: str = None,
    group=None,
    is_buyer: bool = True
) -> tuple[HttpResponse | None, User | None, str | None]:
    """
    Create a new user with the specified parameters.

    This function creates a new User object with a unique username based on
    the Stripe customer ID. It generates a random password and handles
    optional email, language, and group assignment.

    Args:
        stripe_customer_id (str): The Stripe customer identifier.
        email (str, optional): The user's email address. Defaults to None.
        language (str, optional): The user's preferred language. Defaults to None.
        group: The user group to assign. Defaults to None.
        is_buyer (bool, optional): Whether this user is the buyer. If True,
                                  assigns the stripe_customer_id. Defaults to True.

    Returns:
        tuple[HttpResponse | None, User | None, str | None]: Error response,
        created user, and generated password. Returns None values on error.
    """
    try:
        # Generate unique username based on Stripe customer ID
        username = f"lexa{stripe_customer_id[3:]}"
        index = 1
        while User.objects.filter(username=username).exists():
            username = f"lexa{stripe_customer_id[3:]}_{index}"
            index += 1

        # Prepare user data
        user_data = {
            'stripe_customer_id': stripe_customer_id if is_buyer else None,
            'username': username,
            'group': group,
        }

        if language is not None:
            user_data['language'] = language

        if email is not None:
            user_data['email'] = email

        # Create user and set random password
        user = User.objects.create(**user_data)
        random_password = ''.join(
            random.choice(string.ascii_letters + string.digits)
            for _ in range(8)
        )
        user.set_password(random_password)
        user.save()

        return None, user, random_password

    except Exception as error:
        return exception_error(error), None, None


def deactivate_user(user: User) -> HttpResponse | None:
    """
    Deactivate a user and remove admin privileges if applicable.

    This function sets the user as inactive and removes them from the
    admin group if they were an administrator.

    Args:
        user (User): The user to deactivate.

    Returns:
        HttpResponse | None: Error response on failure, None on success.
    """
    try:
        user.is_active = False

        # Remove admin privileges if user is an admin
        if user in user.group.admin.all():
            user.group.admin.remove(user)

        user.save()
        return None

    except Exception as error:
        return exception_error(error)
