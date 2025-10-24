"""
Centralized test constants and settings for users tests.

This module contains all constants used across users test files
to ensure consistency and ease of maintenance.
"""

# User Information
TEST_USERNAME = 'testuser'
TEST_USERNAME_1 = 'testuser1'
TEST_USERNAME_2 = 'testuser2'
TEST_EMAIL = 'test@example.com'
TEST_EMAIL_1 = 'test1@example.com'
TEST_EMAIL_2 = 'test2@example.com'
TEST_PASSWORD = 'testpass123'

# Group Information
TEST_GROUP_NAME = 'Test Group'

# API Keys
TEST_API_KEY = 'test-key'
EXISTING_API_KEY = 'existing-api-key-123'
GENERATED_API_KEY = 'generated-api-key-12345'

# Stripe Information
TEST_STRIPE_CUSTOMER_ID = 'cus_test123456'

# Model Meta Information
USER_GROUP_VERBOSE_NAME = 'Group'
USER_GROUP_VERBOSE_NAME_PLURAL = 'Groups'

# Expected API Response
EXPECTED_API_TIMEOUT = 30
EXPECTED_LABEL_ID = '1'  # Group ID used in API call

# API Endpoints
import os
from django.conf import settings

# Use environment variable only
CUSTOM_MT_CONSOLE_URL = os.environ.get('CUSTOM_MT_CONSOLE_URL')
if CUSTOM_MT_CONSOLE_URL:
    API_CREATE_KEY_ENDPOINT = f"{CUSTOM_MT_CONSOLE_URL.rstrip('/')}/cabinet_api/create_api_key/"
else:
    API_CREATE_KEY_ENDPOINT = None

# Headers
API_HEADERS_CONTENT_TYPE = 'application/json'
API_TOKEN_KEY = 'token'
API_MAIN_TOKEN = 'main-api-key-123'