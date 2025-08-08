"""
Email sending utilities.

This module provides functions for sending emails through the Active Trail API,
including email settings retrieval and message body formatting for various
email types used throughout the application.
"""

import requests

from django.conf import settings

from stripe_webhooks.tasks_handlers.error.error import (
    HttpResponse,
    error_message,
    exception_error
)

from .models import EmailSettings, EmailType


def init_active_trail_header() -> dict:
    """
    Initialize HTTP headers for Active Trail API requests.

    Returns:
        dict: Headers dictionary with Content-Type and Authorization.
    """
    return {
        "Content-Type": "application/json",
        "Authorization": settings.ACTIVE_TRAIL_API_KEY
    }


def get_email_setting(
    email_type: EmailType,
    language: str
) -> tuple[HttpResponse | None, EmailSettings | None]:
    """
    Retrieve email settings for a specific email type and language.

    Args:
        email_type (EmailType): The type of email to get settings for.
        language (str): The language code for the email template.

    Returns:
        tuple[HttpResponse | None, EmailSettings | None]: Error response and
        email settings, or None and settings on success.
    """
    try:
        email_setting = EmailSettings.objects.get(
            email_type=email_type.name,
            language=language
        )
        return None, email_setting
    except EmailSettings.DoesNotExist:
        return error_message(
            "not_found_emailSettings_by_email_type_and_language",
            email_type=email_type.name,
            language=language
        ), None
    except Exception as error:
        return exception_error(error), None


def init_active_trail_operational_message_body(
    email: str,
    email_type: EmailType,
    language: str,
    dict_pairs: dict
) -> tuple[HttpResponse | None, dict | None]:
    """
    Initialize the message body for Active Trail operational email.

    This function prepares the complete message body structure required
    by the Active Trail API for sending operational emails.

    Args:
        email (str): The recipient email address.
        email_type (EmailType): The type of email to send.
        language (str): The language code for the email template.
        dict_pairs (dict): Key-value pairs for email template variables.

    Returns:
        tuple[HttpResponse | None, dict | None]: Error response and message body,
        or None and body on success.
    """
    error_response, setting = get_email_setting(email_type, language)
    if error_response:
        return error_response, None

    return None, {
        "email_package": [
            {
                "email": email,
                "pairs": [
                    {"key": key, "value": value}
                    for key, value in dict_pairs.items()
                ]
            }
        ],
        "details": {
            "name": email_type.name,
            "subject": setting.subject,
            "user_profile_id": settings.ACTIVE_TRAIL_SENDING_PROFILE_ID,
            "user_profile_fromname": settings.ACTIVE_TRAIL_USER_PROFILE_FROMNAME,
            "classification": email_type.name,
        },
        "design": {
            "language_type": "UTF8",
            "template_id": setting.template_id,
            "add_Statistics": True,
        },
    }


def send_email(
    email: str,
    email_type: EmailType,
    language: str,
    dict_pairs: dict
) -> HttpResponse | None:
    """
    Send an email using the Active Trail API.

    This function handles the complete email sending process including
    validation, message body preparation, and API communication.

    Args:
        email (str): The recipient email address.
        email_type (EmailType): The type of email to send.
        language (str): The language code for the email template.
        dict_pairs (dict): Key-value pairs for email template variables.

    Returns:
        HttpResponse | None: Error response if email sending fails,
        or None on success.
    """
    # Validate email parameter
    if not email:
        return error_message("not_found_email")

    # Prepare API request components
    headers = init_active_trail_header()
    error_response, body = init_active_trail_operational_message_body(
        email, email_type, language, dict_pairs
    )

    if error_response:
        return error_response

    # Send email via Active Trail API
    try:
        response = requests.post(
            settings.ACTIVE_TRAIL_SEND_EMAIL_REQUEST_URL,
            json=body,
            headers=headers
        )
        response.raise_for_status()
    except requests.exceptions.HTTPError as error:
        return exception_error(error)

    return None
