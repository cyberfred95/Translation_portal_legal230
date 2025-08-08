"""
Centralized test constants and settings.

This module contains all constants used across API test files
to ensure consistency and ease of maintenance.
"""

# API Keys and Authentication
TEST_API_KEY = 'test-api-key-123'
PERF_API_KEY = 'perf-test-key'
INVALID_API_KEY = 'invalid-key'
INTEGRATION_API_KEY = 'test-integration-api-key'

# User Information
TEST_USERNAME = 'testuser'
TEST_EMAIL = 'test@example.com'
TEST_PASSWORD = 'testpass123'
PERF_USERNAME = 'perfuser'
PERF_EMAIL = 'perf@example.com'
INTEGRATION_USERNAME = 'integrationuser'
INTEGRATION_EMAIL = 'integration@example.com'

# Group Names
TEST_GROUP_NAME = 'Test API Group'
PERF_GROUP_NAME = 'Perf Test Group'
INTEGRATION_GROUP_NAME = 'Test API Group'

# Language Constants
ENGLISH_LANG_CODE = 'en'
FRENCH_LANG_CODE = 'fr'
SPANISH_LANG_CODE = 'es'

ENGLISH_LANG_NAME = 'English'
FRENCH_LANG_NAME = 'French'
SPANISH_LANG_NAME = 'Spanish'

ENGLISH_FRENCH_NAME = 'Anglais'
FRENCH_FRENCH_NAME = 'Français'
SPANISH_FRENCH_NAME = 'Espagnol'

# Domain Constants
TEST_DOMAIN_NAME = 'Contract Law'
TEST_DOMAIN_FRENCH_NAME = 'Droit des contrats'
TEST_DOMAIN_GROUP_NAME = 'Legal'
TEST_DOMAIN_GROUP_FRENCH_NAME = 'Juridique'
TEST_DOMAIN_NO_GROUP_NAME = 'Test Domain'

# Glossary Constants
TEST_GLOSSARY_NAME = 'Test Glossary'
INTEGRATION_GLOSSARY_NAME = 'Integration Test Glossary'
TEST_LANGUAGE_NAME = 'Test Language'
TEST_LANGUAGE_FRENCH_NAME = 'Langue Test'

# File Constants
TEST_FILE_CONTENT = b'en,fr\nhello,bonjour\nworld,monde'
TEST_FILE_NAME = 'test_glossary.csv'
TEST_CSV_FILENAME = 'test.csv'
TEST_CONTENT_TYPE = 'text/csv'
SIMPLE_BASE64_CONTENT = 'SGVsbG8gd29ybGQ='  # "Hello world" in base64
SIMPLE_BASE64_HELLO = 'SGVsbG8='  # "Hello" in base64
INVALID_BASE64_STRING = 'invalid_base64_!!!'

# Translation Test Constants
TRANSLATION_TEXT = 'Hello world'
UNKNOWN_ACTION = 'unknown_action'
TEXT_TRANSLATE_ACTION = 'text_translate'
FILE_TRANSLATE_ACTION = 'file_translate'

# Test Data for Utils
TEST_REQUEST_DATA = {'key': 'value', 'number': 42}
TEST_QUERY_PARAMS = {'source_language': ENGLISH_LANG_CODE,
                     'target_language': FRENCH_LANG_CODE}

# File Type Test Content
XLSX_FILE_SIGNATURE = b'PK\x03\x04\x14\x00\x06\x00'  # XLSX signature
XLS_FILE_SIGNATURE = b'\xD0\xCF\x11\xE0\xA1\xB1\x1A\xE1'  # XLS signature
CSV_FILE_CONTENT = b'col1,col2\nvalue1,value2'
INVALID_BINARY_CONTENT = b'\xFF\xFE\x00\x00'  # Non-UTF8 binary content

# Expected MIME Types
XLSX_MIME_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
XLS_MIME_TYPE = "application/vnd.ms-excel"
CSV_MIME_TYPE = "text/csv"

# File Extensions
XLSX_EXTENSION = '.xlsx'
XLS_EXTENSION = '.xls'
CSV_EXTENSION = '.csv'

# Subscription Constants
TEST_SUBSCRIPTION_NAME = 'API Subscription'
PERF_SUBSCRIPTION_NAME = 'Perf API Subscription'
INTEGRATION_SUBSCRIPTION_NAME = 'API Integration Subscription'
SUBSCRIPTION_PRICE = 100.00

# Performance Constants
MAX_RESPONSE_TIME = 5.0  # seconds

# Invalid Values for Testing
INVALID_LANGUAGE_CODE = 'invalid_lang'
ANOTHER_INVALID_LANGUAGE_CODE = 'another_invalid_lang'
INVALID_JSON_DATA = 'invalid json'
INVALID_API_BEARER = 'Bearer invalid-key'

# Common Test Data
COMMON_TEST_LANGUAGES = [
    {
        'name': ENGLISH_LANG_NAME,
        'abbreviation': ENGLISH_LANG_CODE,
        'french_name': ENGLISH_FRENCH_NAME
    },
    {
        'name': FRENCH_LANG_NAME,
        'abbreviation': FRENCH_LANG_CODE,
        'french_name': FRENCH_FRENCH_NAME
    },
    {
        'name': SPANISH_LANG_NAME,
        'abbreviation': SPANISH_LANG_CODE,
        'french_name': SPANISH_FRENCH_NAME
    }
]

# HTTP Headers


def get_auth_headers(api_key=TEST_API_KEY):
    """Get authorization headers for testing."""
    return {'HTTP_AUTHORIZATION': f'Bearer {api_key}'}


def get_invalid_auth_headers():
    """Get invalid authorization headers for testing."""
    return {'HTTP_AUTHORIZATION': INVALID_API_BEARER}


# Content Types
JSON_CONTENT_TYPE = 'application/json'
CSV_CONTENT_TYPE = 'text/csv'

# Test IDs and Ranges
TEST_GLOSSARY_ID = 1
TEST_DOMAIN_ID = 1
MAX_GLOSSARY_ID_FOR_TEST = 99999
