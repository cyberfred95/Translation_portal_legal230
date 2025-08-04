"""
Customer webhook handlers for Stripe webhooks.

This module handles webhook events related to customer operations,
including customer creation and updates, user management, and group management.
"""

from django.db import transaction

from emails.models import EmailType
from emails.send_email import send_email

from .error.error import HttpResponse, exception_error, success_message
from .getter.get_data import get_user_by_stripe_customer_id
from .getter.get_payload import (
    get_payload_email,
    get_payload_id,
    get_payload_language,
    get_payload_name,
)
from .helper.convertor import group_name_to_user_name
from .helper.stripe_session import get_stripe_customer_session_url
from .setter.set_user import create_user
from .setter.set_userGroup import (
    create_userGroup_if_not_exists,
    get_userGroup_by_group_name,
)


def handle_customer_created(payload: dict) -> HttpResponse:
    """
    Handle customer created webhook event.

    This function processes the creation of a new customer by managing user creation,
    group assignment, and sending welcome emails. It handles two main scenarios:
    1. Group already exists: Customer joins the existing group
    2. Group doesn't exist: Creates a new group for the customer

    The function also handles cleanup of temporary groups that might have been
    created with the customer ID as the name.

    Args:
        payload (dict): The webhook payload containing customer data including
                       ID, name, email, and language preferences.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    # Extract customer data from payload
    error_response, stripe_customer_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, name = get_payload_name(payload)
    if error_response:
        return error_response

    upper_name = name.upper()

    error_response, email = get_payload_email(payload)
    if error_response:
        return error_response

    error_response, language = get_payload_language(payload)
    if error_response:
        return error_response

    # Check if group already exists with this name
    error_response, group = get_userGroup_by_group_name(upper_name)
    if error_response and error_response.exception is not None:
        return error_response

    if group is not None:
        # Group exists - customer joins existing group
        is_group_founded = True

        # Clean up any temporary group with customer ID as name
        error_response, temporary_group = get_userGroup_by_group_name(
            stripe_customer_id.upper()
        )
        if error_response and error_response.exception is not None:
            return error_response

        if temporary_group is not None:
            try:
                temporary_group.delete()
            except Exception as error:
                return exception_error(error)
    else:
        # Group doesn't exist - create new group
        error_response, group, is_group_founded = create_userGroup_if_not_exists(
            stripe_customer_id.upper()
        )
        if error_response:
            return error_response

    # Create user and update group information within transaction
    try:
        with transaction.atomic():
            error_response, user, password = create_user(
                stripe_customer_id=stripe_customer_id,
                email=email,
                language=language,
                group=group
            )
            if error_response:
                return error_response

            # Set user names if this is a new group
            if group.name == stripe_customer_id.upper() and not is_group_founded:
                user.first_name, user.last_name = group_name_to_user_name(
                    group_name=upper_name
                )

            # Update group name if joining existing group
            if is_group_founded:
                group.name = upper_name

            # Make user admin if no admins exist
            if group.admin.count() == 0:
                group.admin.add(user)

            user.save()
            group.save()

    except Exception as error:
        return exception_error(error)

    # Send welcome email to the new user
    error_response = send_email(
        user.email,
        EmailType.USER_CREATED,
        user.language,
        {
            "lexa_username": user.username,
            "lexa_password": password
        }
    )
    if error_response:
        return error_response

    return success_message("customer_created")


def handle_customer_updated(payload: dict) -> HttpResponse:
    """
    Handle customer updated webhook event.

    This function processes updates to an existing customer's information,
    including email and language preferences. It only updates fields that have
    actually changed to optimize performance and avoid unnecessary database writes.

    Args:
        payload (dict): The webhook payload containing updated customer data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    # Extract customer data from payload
    error_response, stripe_customer_id = get_payload_id(payload)
    if error_response:
        return error_response

    error_response, user = get_user_by_stripe_customer_id(stripe_customer_id)
    if error_response:
        return error_response

    error_response, email = get_payload_email(payload)
    if error_response:
        return error_response

    error_response, language = get_payload_language(payload)
    if error_response:
        return error_response

    # Update user information only if changes are detected
    try:
        updated = False

        if email != user.email:
            user.email = email
            updated = True

        if language != user.language:
            user.language = language
            updated = True

        # Return early if no changes were made
        if not updated:
            return success_message("customer_identical", username=user.username)

        user.save()

    except Exception as error:
        return exception_error(error)

    return success_message("customer_updated")


CUSTOMER_EVENT_HANDLERS = {
    "customer.created": handle_customer_created,
    "customer.updated": handle_customer_updated,
}
