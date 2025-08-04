"""
Customer tax ID webhook handlers for Stripe webhooks.

This module handles webhook events related to customer tax ID operations,
including creation and management of tax IDs for customers when they register
their company/business information.
"""

from django.db import transaction

from .error.error import HttpResponse, exception_error, success_message
from .getter.get_data import get_user_by_stripe_customer_id, get_userGroup_by_id
from .getter.get_payload import get_payload_customer_id
from .helper.convertor import user_name_to_group_name
from .setter.set_userGroup import create_userGroup_if_not_exists


def handle_customer_tax_id_created(payload: dict) -> HttpResponse:
    """
    Handle customer tax ID created webhook event.

    This function processes the creation of a tax ID for a customer, which typically
    indicates that the customer has registered their business/company information.
    The function handles two main scenarios:
    1. User doesn't exist: Creates a temporary group for future user creation
    2. User exists: Updates user info and renames group to reflect business name

    When a tax ID is created, it means the customer is transitioning from an
    individual to a business entity, so we clear personal names and use the
    business name for the group.

    Args:
        payload (dict): The webhook payload containing customer tax ID data.

    Returns:
        HttpResponse: Success or error response indicating the operation result.
    """
    error_response, stripe_customer_id = get_payload_customer_id(payload)
    if error_response:
        return error_response

    error_response, user = get_user_by_stripe_customer_id(stripe_customer_id)
    if error_response and not user:
        if error_response.exception is not None:
            return error_response

        # User doesn't exist yet - create temporary group for future use
        error_response, group, _ = create_userGroup_if_not_exists(
            stripe_customer_id)
        if error_response:
            return error_response

        return success_message(
            "customer_tax_id_created_temporary",
            stripe_customer_id=stripe_customer_id
        )

    # User exists - update their information for business registration
    error_response, group = get_userGroup_by_id(user.group_id)
    if error_response:
        return error_response

    group_name = user_name_to_group_name(user)

    try:
        with transaction.atomic():
            # Clear personal names since this is now a business entity
            user.first_name = ""
            user.last_name = ""
            user.group_id = group.id
            user.save()

            # Update group name if it was using the temporary customer ID
            if group.name == stripe_customer_id.upper():
                group.name = group_name
                group.save()

    except Exception as error:
        return exception_error(error)

    return success_message(
        "customer_tax_id_created",
        stripe_customer_id=stripe_customer_id,
        group_name=group_name
    )


CUSTOMER_TAX_ID_EVENT_HANDLERS = {
    "customer.tax_id.created": handle_customer_tax_id_created,
}
