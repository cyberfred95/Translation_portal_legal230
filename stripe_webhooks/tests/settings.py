"""
Centralized test constants and settings for stripe_webhooks tests.

This module contains all constants used across stripe_webhooks test files
to ensure consistency and ease of maintenance.
"""

# Stripe Customer IDs
TEST_STRIPE_CUSTOMER_ID = 'cus_test123456789'
TEST_STRIPE_CUSTOMER_ID_2 = 'cus_test987654321'
INVALID_STRIPE_CUSTOMER_ID = 'cus_invalid'

# Stripe Subscription IDs
TEST_STRIPE_SUBSCRIPTION_ID = 'sub_test123456789'
TEST_STRIPE_SUBSCRIPTION_ID_2 = 'sub_test987654321'
INVALID_STRIPE_SUBSCRIPTION_ID = 'sub_invalid'

# Stripe Product IDs
TEST_STRIPE_PRODUCT_ID = 'prod_test123456789'
TEST_STRIPE_PRODUCT_ID_2 = 'prod_test987654321'
INVALID_STRIPE_PRODUCT_ID = 'prod_invalid'

# User Information
TEST_USERNAME = 'testuser'
TEST_EMAIL = 'test@example.com'
TEST_EMAIL_2 = 'test2@example.com'
TEST_PASSWORD = 'testpass123'
TEST_FIRST_NAME = 'John'
TEST_LAST_NAME = 'Doe'
TEST_FULL_NAME = 'John Doe'
TEST_COMPANY_NAME = 'Test Company'

# Group Names
TEST_GROUP_NAME = 'TEST GROUP'
TEST_GROUP_NAME_2 = 'ANOTHER TEST GROUP'
TEST_GROUP_NAME_LOWER = 'test group'

# Language Constants
ENGLISH_LANG_CODE = 'en'
FRENCH_LANG_CODE = 'fr'
SPANISH_LANG_CODE = 'es'
INVALID_LANG_CODE = 'xx'

# Subscription Constants
TEST_SUBSCRIPTION_NAME = 'Test Subscription'
TEST_SUBSCRIPTION_PRICE = 99.99
SUBSCRIPTION_STATUS_ACTIVE = 'ACTIVE'
SUBSCRIPTION_STATUS_CANCELED = 'CANCELED'
SUBSCRIPTION_STATUS_INACTIVE = 'INACTIVE'
SUBSCRIPTION_STATUS_UNKNOWN = 'UNKNOWN'

# Stripe Webhook Statuses
STRIPE_STATUS_ACTIVE = 'active'
STRIPE_STATUS_CANCELED = 'canceled'
STRIPE_STATUS_INCOMPLETE = 'incomplete'
STRIPE_STATUS_PAST_DUE = 'past_due'

# Timestamps
TEST_TIMESTAMP = 1640995200  # 2022-01-01 00:00:00 UTC
TEST_TIMESTAMP_2 = 1672531200  # 2023-01-01 00:00:00 UTC
INVALID_TIMESTAMP = None

# Test Payloads
TEST_CUSTOMER_PAYLOAD = {
    'id': TEST_STRIPE_CUSTOMER_ID,
    'name': TEST_FULL_NAME,
    'email': TEST_EMAIL,
    'preferred_locales': [ENGLISH_LANG_CODE]
}

TEST_CUSTOMER_PAYLOAD_NO_EMAIL = {
    'id': TEST_STRIPE_CUSTOMER_ID,
    'name': TEST_FULL_NAME,
    'preferred_locales': [ENGLISH_LANG_CODE]
}

TEST_CUSTOMER_PAYLOAD_NO_NAME = {
    'id': TEST_STRIPE_CUSTOMER_ID,
    'email': TEST_EMAIL,
    'preferred_locales': [ENGLISH_LANG_CODE]
}

TEST_CUSTOMER_PAYLOAD_NO_LANGUAGE = {
    'id': TEST_STRIPE_CUSTOMER_ID,
    'name': TEST_FULL_NAME,
    'email': TEST_EMAIL
}

TEST_SUBSCRIPTION_PAYLOAD = {
    'id': TEST_STRIPE_SUBSCRIPTION_ID,
    'customer': TEST_STRIPE_CUSTOMER_ID,
    'status': STRIPE_STATUS_ACTIVE,
    'items': {
        'data': [{
            'price': {
                'product': TEST_STRIPE_PRODUCT_ID
            },
            'plan': {
                'product': TEST_STRIPE_PRODUCT_ID
            },
            'quantity': 1,
            'current_period_start': TEST_TIMESTAMP,
            'current_period_end': TEST_TIMESTAMP_2
        }]
    }
}

INVALID_CUSTOMER_PAYLOAD = {
    'name': TEST_FULL_NAME,
    'email': TEST_EMAIL
}

INVALID_SUBSCRIPTION_PAYLOAD = {
    'customer': TEST_STRIPE_CUSTOMER_ID,
    'status': STRIPE_STATUS_ACTIVE
}

# Email Constants
EMAIL_TYPE_WELCOME = 'welcome'
EMAIL_TYPE_PASSWORD_RESET = 'password_reset'

# Random Password Constants
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 12

# API Keys
TEST_API_KEY = 'test-api-key-123'
DEFAULT_API_KEY = 'default-api-key'

# Expected Error Messages
ERROR_NOT_FOUND_ID = 'not_found_id'
ERROR_NOT_FOUND_NAME = 'not_found_name'
ERROR_NOT_FOUND_EMAIL = 'not_found_email'
ERROR_NOT_FOUND_LANGUAGE = 'not_found_language'
ERROR_NOT_FOUND_STATUS = 'not_found_status'
ERROR_NOT_FOUND_CUSTOMER_ID = 'not_found_customer_id'
ERROR_NOT_FOUND_USER = 'not_found_user_by_stripe_customer_id'
ERROR_NOT_FOUND_SUBSCRIPTION_TYPE = 'not_found_subscriptionType_by_stripe_product_id'
ERROR_NOT_FOUND_USER_SUBSCRIPTION = 'not_found_userSubscription_by_stripe_subscription_id'
ERROR_NOT_FOUND_USER_GROUP = 'not_found_userGroup_by_group_name'
ERROR_EXCEPTION = 'exception'

# Test Data Helpers


def get_test_payload_with_missing_field(field_name):
    """Return a test payload with a specific field missing."""
    payload = TEST_CUSTOMER_PAYLOAD.copy()
    if field_name in payload:
        del payload[field_name]
    return payload


def get_test_subscription_payload_with_missing_field(field_name):
    """Return a test subscription payload with a specific field missing."""
    payload = TEST_SUBSCRIPTION_PAYLOAD.copy()
    if field_name in payload:
        del payload[field_name]
    return payload


# Group Creation Constants
GROUP_ALREADY_EXISTS = True
GROUP_NEWLY_CREATED = False

# User Subscription Choices for Testing
USER_SUBSCRIPTION_CHOICES = {
    'active': 'ACTIVE',
    'canceled': 'CANCELED',
    'incomplete': 'INCOMPLETE',
    'past-due': 'PAST_DUE',
    'unknown': 'UNKNOWN'
}

# Converter Test Data
CONVERTER_TEST_DICT = {
    'key1': 'value1',
    'key2': 'value2',
    'key3': 'value3'
}

CONVERTER_EXPECTED_PAIRS = [
    {'key': 'key1', 'value': 'value1'},
    {'key': 'key2', 'value': 'value2'},
    {'key': 'key3', 'value': 'value3'}
]

# Stripe Session URLs
TEST_STRIPE_SESSION_URL = 'https://billing.stripe.com/p/session/test_session_123'
