"""
API Settings for Legal230 Application

This module contains configuration constants for the API endpoints,
including validation limits, file size constraints, allowed file types,
and other security-related settings.
"""

# Django imports
from django.conf import settings


# Text field limits
MAX_TEXT_LENGTH = 2000  # Maximum characters for translation text
MAX_LANGUAGE_CODE_LENGTH = 10  # Short language codes (e.g., "en", "fr")
MAX_DOMAIN_NAME_LENGTH = 128  # Reasonable domain name length
MAX_ACTION_LENGTH = 32  # Limited action name (e.g., "text_translate")
MAX_API_KEY_LENGTH = 36  # Maximum API key length

# Glossary limits
MAX_GLOSSARY_NAME_LENGTH = 128  # Glossary name length

# File size limits
MAX_TOTAL_FILE_SIZE = 50 * 1024 * 1024  # 50MB maximum total for all files
MAX_GLOSSARY_FILE_SIZE = 10 * 1024 * 1024  # 10MB maximum for glossaries
MAX_FILES_COUNT = 10  # Maximum 10 files per request

# Domain and ID limits
MAX_INT = 2147483647
MAX_DOMAIN_ID = MAX_INT
MAX_GLOSSARY_ID = MAX_INT

# Allowed file extensions
ALLOWED_FILE_EXTENSIONS = ('.txt', '.docx', '.xlsx', '.pptx', '.pdf')
ALLOWED_GLOSSARY_EXTENSIONS = ('.csv', '.xlsx')

# File signatures for content validation
ALLOWED_FILE_SIGNATURES = {
    '.txt': [b''],
    '.docx': [b'PK', b'\x50\x4B\x03\x04'],
    '.xlsx': [b'PK', b'\x50\x4B\x03\x04'],
    '.pptx': [b'PK', b'\x50\x4B\x03\x04'],
    '.pdf': [b'%PDF'],
}
