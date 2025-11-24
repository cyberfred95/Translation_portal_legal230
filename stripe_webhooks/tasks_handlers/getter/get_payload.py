"""
Payload data extraction utilities.

This module provides functions for extracting and validating data from
Stripe webhook payloads, including customer information, subscription data,
and timestamp conversions.
"""

from datetime import datetime

from django.conf import settings

from ..error.error import HttpResponse, error_message
from ..helper.convertor import int_to_DateTimeField


def get_payload_status(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract status from payload.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and status,
        or None and status on success.
    """
    payload_status = payload.get('status')
    if not payload_status:
        return error_message("not_found_status"), None
    return None, payload_status


def get_payload_id(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract ID from payload.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and ID,
        or None and ID on success.
    """
    payload_id = payload.get('id', "")
    if not payload_id:
        return error_message("not_found_id"), None
    return None, payload_id


def get_payload_customer_id(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract customer ID from payload.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and customer ID,
        or None and customer ID on success.
    """
    payload_customer_id = payload.get('customer', "")
    if not payload_customer_id:
        return error_message("not_found_customer_id"), None
    return None, payload_customer_id


def get_payload_name(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract and normalize name from payload.

    This function extracts the name field and normalizes whitespace by
    removing extra spaces and trimming.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and name,
        or None and normalized name on success. Returns empty string if
        name field exists but is empty.
    """
    if 'name' not in payload:
        return error_message("not_found_name"), None

    payload_name = payload.get('name', "")
    if not payload_name:
        return None, ""

    # Normalize whitespace by removing extra spaces
    return None, ' '.join(payload_name.strip().split())


def get_payload_email(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract email from payload.

    This function extracts the email field and handles cases where
    the email field is missing or empty.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: None and email on success,
        or None and empty string if email is missing or empty.
    """

    if 'email' not in payload:
        return None, ""
    email_value = payload.get('email', "")
    if not isinstance(email_value, str):
        return None, ""
    payload_email = email_value.strip()
    if not payload_email:
        return None, ""

    return None, payload_email


def get_payload_language(payload: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract and validate language from payload preferred_locales.

    This function extracts the preferred language from the preferred_locales
    field and validates it against Django's configured languages. Returns
    the first valid language found or the default language code.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and language,
        or None and language code on success.
    """
    if 'preferred_locales' not in payload:
        return error_message("not_found_language"), None

    locales = payload.get("preferred_locales", [])
    if not isinstance(locales, list):
        return error_message("not_found_language"), None

    # Check for valid language codes from Django settings
    valid_codes = {code for code, _ in settings.LANGUAGES}
    for loc in locales:
        if loc in valid_codes:
            return None, loc

    # Return default language if no valid locale found
    return None, settings.LANGUAGE_CODE


def get_payload_item_data(payload: dict, index: int) -> tuple[HttpResponse | None, dict | None]:
    """
    Extract item data from payload at specified index.

    Args:
        payload (dict): The webhook payload.
        index (int): The index of the item to extract.

    Returns:
        tuple[HttpResponse | None, dict | None]: Error response and item data,
        or None and item data on success.
    """
    item_data = payload.get('items', {}).get('data', [{}])[index]
    if not item_data:
        return error_message("not_found_item_data"), None
    return None, item_data


def get_payload_cancel_at(payload: dict) -> tuple[HttpResponse | None, datetime | None]:
    """
    Extract and convert cancel_at timestamp from payload.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, datetime | None]: Error response and datetime,
        or None and converted datetime on success.
    """
    string_date = payload.get('cancel_at', None)
    dateTime_date = int_to_DateTimeField(string_date)
    if dateTime_date is None:
        return error_message("not_found_cancel_at"), None
    return None, dateTime_date


def get_payload_ended_at(payload: dict) -> tuple[HttpResponse | None, datetime | None]:
    """
    Extract and convert ended_at timestamp from payload.

    Args:
        payload (dict): The webhook payload.

    Returns:
        tuple[HttpResponse | None, datetime | None]: Error response and datetime,
        or None and converted datetime on success.
    """
    string_date = payload.get('ended_at', None)
    dateTime_date = int_to_DateTimeField(string_date)
    if dateTime_date is None:
        return error_message("not_found_ended_at"), None
    return None, dateTime_date


def get_item_data_product_id(item_data: dict) -> tuple[HttpResponse | None, str | None]:
    """
    Extract product ID from item data.

    Args:
        item_data (dict): The item data from payload.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and product ID,
        or None and product ID on success.
    """
    payload_product_id = item_data.get('plan', {}).get('product', "")
    if not payload_product_id:
        return error_message("not_found_stripe_product_id"), None
    return None, payload_product_id


def get_item_data_quantity(item_data: dict) -> tuple[HttpResponse | None, int | None]:
    """
    Extract and validate quantity from item data.

    This function extracts the quantity and validates that it's a positive integer.

    Args:
        item_data (dict): The item data from payload.

    Returns:
        tuple[HttpResponse | None, int | None]: Error response and quantity,
        or None and validated quantity on success.
    """
    quantity = item_data.get('quantity')
    if quantity is None:
        return error_message("not_found_quantity"), None

    if not isinstance(quantity, int) or quantity < 1:
        return error_message("quantity_user_subscription_ivalid", quantity=quantity), None

    return None, quantity


def get_item_data_current_period_start(item_data: dict) -> tuple[HttpResponse | None, datetime | None]:
    """
    Extract and convert current_period_start timestamp from item data.

    Args:
        item_data (dict): The item data from payload.

    Returns:
        tuple[HttpResponse | None, datetime | None]: Error response and datetime,
        or None and converted datetime on success.
    """
    string_date = item_data.get('current_period_start', None)
    dateTime_date = int_to_DateTimeField(string_date)
    if dateTime_date is None:
        return error_message("not_found_current_period_start"), None
    return None, dateTime_date


def get_item_data_subscription_item_id(item_data: dict) -> tuple[HttpResponse | None, str | None]:
    subscription_item_id = item_data.get('id')
    if not subscription_item_id:
        return error_message("not_found_subscription_item_id"), None
    return None, subscription_item_id


def get_item_data_current_period_end(item_data: dict) -> tuple[HttpResponse | None, datetime | None]:
    """
    Extract and convert current_period_end timestamp from item data.

    Args:
        item_data (dict): The item data from payload.

    Returns:
        tuple[HttpResponse | None, datetime | None]: Error response and datetime,
        or None and converted datetime on success.
    """
    string_date = item_data.get('current_period_end', None)
    dateTime_date = int_to_DateTimeField(string_date)
    if dateTime_date is None:
        return error_message("not_found_current_period_end"), None
    return None, dateTime_date
