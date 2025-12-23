"""
Error message constants for API views.

This module contains all error messages used across the API views
to ensure consistency and ease of maintenance.
"""

# Import constants from settings
from api.settings import (
    MAX_TEXT_LENGTH,
    MAX_LANGUAGE_CODE_LENGTH,
    MAX_DOMAIN_NAME_LENGTH,
    MAX_ACTION_LENGTH,
    MAX_GLOSSARY_NAME_LENGTH,
    MAX_TOTAL_FILE_SIZE,
    MAX_GLOSSARY_FILE_SIZE,
    MAX_FILES_COUNT,
    MAX_DOMAIN_ID,
    MAX_GLOSSARY_ID,
    MAX_API_KEY_LENGTH,
)

# Field validation error messages
FIELD_REQUIRED = "'{field}' (string) is required"
FIELD_REQUIRED_IF_PROVIDED = "'{field}' (string) is required if provided"

# Field length error messages (specific to field types)
FIELD_TOO_LONG_ACTION = f"'{{field}}' must be less than {MAX_ACTION_LENGTH} characters"
FIELD_TOO_LONG_LANGUAGE = f"'{{field}}' must be less than {MAX_LANGUAGE_CODE_LENGTH} characters"
FIELD_TOO_LONG_GLOSSARY_NAME = f"'{{field}}' must be less than {MAX_GLOSSARY_NAME_LENGTH} characters"

# Specific field error messages
DOMAIN_NAME_REQUIRED_IF_PROVIDED = "'domain_name' (string) is required if provided"
DOMAIN_NAME_TOO_LONG = f"'domain_name' must be less than {MAX_DOMAIN_NAME_LENGTH} characters"
TEXT_REQUIRED_FOR_TEXT_TRANSLATE = "'text' (string) is required for action 'text_translate'"
TEXT_TOO_LONG = f"'text' must be less than {MAX_TEXT_LENGTH} characters"

# Document/File validation error messages
DOCUMENT_ARRAY_REQUIRED = "'document' (array of base64 string) is required for action 'file_translate'"
DOCUMENT_FILE_REQUIRED = "'document' (at least one file) is required for action 'file_translate'"
FILE_BASE64_REQUIRED = "'file' (base64 string) is required"
FILE_UPLOAD_REQUIRED = "'file' (file) is required"
FILE_INVALID_BASE64 = "'file' is not valid base64"
FILE_TOO_LARGE_GLOSSARY = f"File is too large. Maximum size is {MAX_GLOSSARY_FILE_SIZE // (1024*1024)}MB"
TOTAL_FILES_TOO_LARGE = f"Total file size exceeds the maximum allowed size of {MAX_TOTAL_FILE_SIZE // (1024*1024)}MB"
FILE_INVALID_TYPE_CSV_XLSX = "'file' must be a CSV or XLSX file (base64)"
FILE_INVALID_TYPE_CSV_XLSX_UPLOAD = "'file' must be a CSV or XLSX file"
FILE_INVALID_TYPE_DOCUMENTS = "Element {index} in 'document' is not a valid TXT, DOCX, XLSX, PPTX or PDF file"
FILE_INVALID_TYPE_WITH_NAME = "File {filename} is not a TXT, DOCX, XLSX, PPTX or PDF file"
ELEMENT_INVALID_BASE64 = "Element {index} in 'document' is not valid base64"

# Limit validation error messages
MAX_FILES_EXCEEDED = f"Maximum {MAX_FILES_COUNT} files allowed"

# ID validation error messages
ID_MUST_BE_INTEGER = "'{field}' must be an integer"
ID_OUT_OF_RANGE_DOMAIN = f"'{{field}}' must be between 0 and {MAX_DOMAIN_ID}"
ID_OUT_OF_RANGE_GLOSSARY = f"'{{field}}' must be between 0 and {MAX_GLOSSARY_ID}"
DOMAIN_ID_MUST_BE_INTEGER = "id_domain must be an integer"
GLOSSARY_ID_MUST_BE_INTEGER = "'id_glossary' must be an integer"

# Resource not found error messages
SOURCE_LANGUAGE_NOT_FOUND = "Source language '{language}' not found."
TARGET_LANGUAGE_NOT_FOUND = "Target language '{language}' not found"
USER_GLOSSARY_NOT_FOUND = "No user glossary found with this ID"

# Glossary validation error messages (Custom.mt error)
SAME_SOURCE_TARGET_LANGUAGE = "Source and target languages cannot be the same"
INVALID_LANGUAGE_CODE = "Invalid language code: {language}"

# API Key validation error messages
INVALID_API_KEY = "Invalid API key"
AUTHORIZATION_HEADER_REQUIRED = "Authorization header is required"
AUTHORIZATION_HEADER_FORMAT = "Authorization header must be in format: Bearer <api_key>"
API_KEY_REQUIRED_AFTER_BEARER = "API key is required after Bearer"
API_KEY_TOO_LONG = f"API key too long. Maximum {MAX_API_KEY_LENGTH} characters"

# API user authentication error messages
API_PRODUCT_NOT_FOUND = "Cannot find any API Product, please contact support"
API_PRODUCT_ERROR = "Error retrieving API Product, please contact support: {error}"
NO_ACTIVE_SUBSCRIPTION = "No user found with an active subscription for this API Key"
MULTIPLE_ACTIVE_SUBSCRIPTIONS = "Multiple users found with an active subscription for this API Key, please contact support"

# Request data validation error messages
SOURCE_LANGUAGE_TOO_LONG = "source_language parameter too long"
TARGET_LANGUAGE_TOO_LONG = "target_language parameter too long"
INVALID_JSON = "Invalid JSON"

# Action error messages
UNKNOWN_ACTION = "Unknown action: {action}"
