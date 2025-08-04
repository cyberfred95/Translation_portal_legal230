"""
API Utilities for Legal230 Application

This module provides utility functions for API authentication, request data
processing, user validation, and file type detection. It includes functions
for API key validation, user subscription checking, and request parsing.
"""

# Standard library imports
import json

# Local imports
from subscriptions.models import UserSubscription, SubscriptionType
from users.models import User, UserGroup
from .settings import MAX_API_KEY_LENGTH, MAX_LANGUAGE_CODE_LENGTH
from .views.error.error import error_message
from .views.error.error_messages import (
    AUTHORIZATION_HEADER_REQUIRED,
    AUTHORIZATION_HEADER_FORMAT,
    API_KEY_REQUIRED_AFTER_BEARER,
    API_KEY_TOO_LONG,
    INVALID_API_KEY_NO_GROUP,
    API_PRODUCT_NOT_FOUND,
    API_PRODUCT_ERROR,
    NO_ACTIVE_SUBSCRIPTION,
    MULTIPLE_ACTIVE_SUBSCRIPTIONS,
    SOURCE_LANGUAGE_TOO_LONG,
    TARGET_LANGUAGE_TOO_LONG,
    INVALID_JSON,
)


def extract_and_validate_api_key(auth_header):
    """
    Extract and validate API key from Authorization header.

    Args:
        auth_header: Authorization header string

    Returns:
        tuple: (api_key, error_message) where error_message is None on success
    """
    if not auth_header:
        return None, AUTHORIZATION_HEADER_REQUIRED

    # Check Bearer format
    if not auth_header.startswith('Bearer '):
        return None, AUTHORIZATION_HEADER_FORMAT

    # Extract API key after "Bearer "
    api_key = auth_header[7:]  # Remove "Bearer "
    if not api_key:
        return None, API_KEY_REQUIRED_AFTER_BEARER
    if len(api_key) > MAX_API_KEY_LENGTH:
        return None, API_KEY_TOO_LONG

    return api_key, None


def get_api_user(request):
    """
    Get user and group from API key authentication.

    Args:
        request: Django HttpRequest object

    Returns:
        tuple: ((user, group), error_message) where error_message is None on success
    """
    auth_header = request.headers.get('Authorization')

    # Extract and validate API key
    api_key, error = extract_and_validate_api_key(auth_header)
    if error:
        return None, error

    # Find group by API key (temporary waiting for custom.mt: API key should be unique)
    group = UserGroup.objects.filter(api_key=api_key).first()
    if not group:
        return None, INVALID_API_KEY_NO_GROUP

    users = User.objects.filter(group=group)

    try:
        api_products = SubscriptionType.objects.filter(
            price_type=SubscriptionType.PriceTypeChoices.AU
        )
    except SubscriptionType.DoesNotExist:
        return None, API_PRODUCT_NOT_FOUND
    except Exception as error:
        return None, API_PRODUCT_ERROR.format(error=error)

    user_subscriptions = UserSubscription.objects.filter(
        user__in=users, subscription__in=api_products
    )

    if not user_subscriptions.exists():
        return None, NO_ACTIVE_SUBSCRIPTION
    if user_subscriptions.count() > 1:
        return None, MULTIPLE_ACTIVE_SUBSCRIPTIONS

    return (user_subscriptions[0].user, group), None


def get_request_data(request, from_query=False):
    """
    Extract and validate request data from query parameters or request body.

    Args:
        request: Django HttpRequest object
        from_query: Boolean indicating whether to extract from query parameters

    Returns:
        tuple: (data, error_message) where error_message is None on success
    """
    if from_query:
        source_language = request.GET.get('source_language') or None
        target_language = request.GET.get('target_language') or None

        # Validate query parameters
        if source_language and len(source_language) > MAX_LANGUAGE_CODE_LENGTH:
            return None, SOURCE_LANGUAGE_TOO_LONG
        if target_language and len(target_language) > MAX_LANGUAGE_CODE_LENGTH:
            return None, TARGET_LANGUAGE_TOO_LONG

        return {
            "source_language": source_language,
            "target_language": target_language
        }, None

    if request.content_type and request.content_type.startswith('application/json'):
        try:
            return json.loads(request.body), None
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None, INVALID_JSON

    return request.POST, None


def get_user_and_data(request, with_data=True, from_query=False):
    """
    Get authenticated user and request data in one operation.

    Args:
        request: Django HttpRequest object
        with_data: Boolean indicating whether to extract request data
        from_query: Boolean indicating whether to extract from query parameters

    Returns:
        tuple: (user, data, error_dict) where error_dict is None on success
    """
    user_group, error = get_api_user(request)
    if error:
        return None, None, error_message(error)

    data = None
    if with_data:
        data, error = get_request_data(request, from_query)
        if error:
            return None, None, error_message(error)

    return user_group[0], data, None


def detect_glossary_file_type(file_content):
    """
    Detect file type based on content signature for glossary files.

    Args:
        file_content: Binary content of the file

    Returns:
        tuple: (file_extension, mime_type) or (None, None) if unrecognized
    """
    if file_content[:4] == b'PK\x03\x04':
        return '.xlsx', "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    elif file_content[:2] == b'\xD0\xCF':
        return '.xls', "application/vnd.ms-excel"

    try:
        file_content.decode('utf-8')
    except UnicodeDecodeError:
        return None, None

    return '.csv', "text/csv"
