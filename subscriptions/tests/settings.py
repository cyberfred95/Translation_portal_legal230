"""
Centralized test constants and settings for subscriptions tests.

This module contains all constants used across subscriptions test files
to ensure consistency and ease of maintenance.
"""

from datetime import datetime, timezone

# User Information
TEST_USERNAME = 'testuser'
TEST_EMAIL = 'test@example.com'
TEST_LANGUAGE = 'en'

# Group Information
TEST_GROUP_NAME = "Test Group"

# Subscription Type Information
TEST_SUBSCRIPTION_NAME = 'Test Subscription'
TEST_SUBSCRIPTION_PRICE = 99.99
TEST_MAX_SYMBOLS_COUNT = 1000
TEST_MAX_WORDS_COUNT = 500
TEST_MAX_FILES_COUNT = 10
TEST_ACCESS_TO_WRITING = True
TEST_ACCESS_TO_OFFICIAL_GLOSSARIES = True
TEST_ACCESS_TO_SSO = False

# Test Dates
TEST_DATE_JANUARY = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)
TEST_DATE_DECEMBER = datetime(2025, 12, 31, 12, 0, 0, tzinfo=timezone.utc)
EXPECTED_DATE_FEBRUARY = datetime(2025, 2, 15, 12, 0, 0, tzinfo=timezone.utc)
EXPECTED_DATE_JANUARY_NEXT_YEAR = datetime(2026, 1, 31, 12, 0, 0, tzinfo=timezone.utc)

# Subscription Counts
TEST_TRANSLATED_SYMBOLS_COUNT = 100
TEST_TRANSLATED_WORDS_COUNT = 50
TEST_TRANSLATED_FILES_COUNT = 2

# Time Deltas (in days)
SUBSCRIPTION_DURATION_DAYS = 30
NEXT_DAY_OFFSET = 1

# Stripe Information
TEST_STRIPE_SUBSCRIPTION_ID = 'sub_test123'

# Expected Results
EXPECTED_RENEWED_COUNT_SUCCESS = 1
EXPECTED_ERROR_COUNT_SUCCESS = 0
EXPECTED_TOTAL_PROCESSED_SUCCESS = 1
EXPECTED_RENEWED_COUNT_IGNORED = 0
EXPECTED_ERROR_COUNT_IGNORED = 0
EXPECTED_TOTAL_PROCESSED_IGNORED = 0
EXPECTED_RENEWED_COUNT_ERROR = 0
EXPECTED_ERROR_COUNT_ERROR = 1
EXPECTED_TOTAL_PROCESSED_ERROR = 1

# Patch Targets
PATCH_TIMEZONE_NOW = 'subscriptions.tasks.timezone.now'
PATCH_RESET_SUBSCRIPTIONS = 'subscriptions.tasks.reset_subscriptions'

# Error Messages
TEST_ERROR_MESSAGE = "Test error"

# Result Keys
RESULT_KEY_RENEWED_COUNT = 'renewed_count'
RESULT_KEY_ERROR_COUNT = 'error_count'
RESULT_KEY_TOTAL_PROCESSED = 'total_processed'
