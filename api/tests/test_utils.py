"""
Unit tests for API utilities.

This module contains tests for API utility functions, including key validation,
user authentication, request data handling, and file type detection.
"""

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.settings import MAX_API_KEY_LENGTH, MAX_LANGUAGE_CODE_LENGTH
from api.utils import (
    detect_glossary_file_type,
    extract_and_validate_api_key,
    get_api_user,
    get_request_data,
    get_user_and_data,
)
from api.views.error.error_messages import (
    API_KEY_REQUIRED_AFTER_BEARER,
    API_KEY_TOO_LONG,
    AUTHORIZATION_HEADER_FORMAT,
    AUTHORIZATION_HEADER_REQUIRED,
    INVALID_JSON,
    NO_ACTIVE_SUBSCRIPTION,
    SOURCE_LANGUAGE_TOO_LONG,
)
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group, create_test_user_subscription

from .settings import (
    CSV_EXTENSION,
    CSV_FILE_CONTENT,
    CSV_MIME_TYPE,
    ENGLISH_LANG_CODE,
    FRENCH_LANG_CODE,
    INVALID_API_KEY,
    INVALID_BINARY_CONTENT,
    JSON_CONTENT_TYPE,
    SUBSCRIPTION_PRICE,
    TEST_API_KEY,
    TEST_EMAIL,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_REQUEST_DATA,
    TEST_SUBSCRIPTION_NAME,
    TEST_USERNAME,
    XLS_EXTENSION,
    XLS_FILE_SIGNATURE,
    XLS_MIME_TYPE,
    XLSX_EXTENSION,
    XLSX_FILE_SIGNATURE,
    XLSX_MIME_TYPE,
    get_auth_headers,
)

User = get_user_model()


class APIUtilsTestCase(TestCase):
    """Test case for API utility functions."""

    def setUp(self):
        """Set up test data for API utilities tests."""
        self.factory = RequestFactory()

        # Create API group
        self.group = create_test_user_group(
            name=TEST_GROUP_NAME
        )

        # Create test user
        self.user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        self.user.group = self.group
        self.user.save()

        # Create subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            product_type=SubscriptionType.ProductChoices.WORD_ADD_IN,
            price=SUBSCRIPTION_PRICE
        )

        # Create active subscription with API key
        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            api_key=TEST_API_KEY,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

    def test_extract_and_validate_api_key_success(self):
        """Test successful API key extraction."""
        auth_header = f'Bearer {TEST_API_KEY}'
        api_key, error = extract_and_validate_api_key(auth_header)

        self.assertEqual(api_key, TEST_API_KEY)
        self.assertIsNone(error)

    def test_extract_and_validate_api_key_no_header(self):
        """Test with missing authorization header."""
        api_key, error = extract_and_validate_api_key(None)

        self.assertIsNone(api_key)
        self.assertEqual(error, AUTHORIZATION_HEADER_REQUIRED)

    def test_extract_and_validate_api_key_invalid_format(self):
        """Test with invalid header format."""
        auth_header = f'Invalid {TEST_API_KEY}'
        api_key, error = extract_and_validate_api_key(auth_header)

        self.assertIsNone(api_key)
        self.assertEqual(
            error, AUTHORIZATION_HEADER_FORMAT)

    def test_extract_and_validate_api_key_empty_key(self):
        """Test with empty API key."""
        auth_header = 'Bearer '
        api_key, error = extract_and_validate_api_key(auth_header)

        self.assertIsNone(api_key)
        self.assertEqual(error, API_KEY_REQUIRED_AFTER_BEARER)

    def test_extract_and_validate_api_key_too_long(self):
        """Test with API key that exceeds maximum length."""
        # Exceeding MAX_API_KEY_LENGTH
        long_key = 'a' * (MAX_API_KEY_LENGTH + 64)
        auth_header = f'Bearer {long_key}'
        api_key, error = extract_and_validate_api_key(auth_header)

        self.assertIsNone(api_key)
        self.assertEqual(error, API_KEY_TOO_LONG)

    def test_get_api_user_success(self):
        """Test successful API user retrieval."""
        request = self.factory.get('/')
        request.headers = {'Authorization': f'Bearer {TEST_API_KEY}'}

        user, error = get_api_user(request)

        self.assertIsNone(error)
        self.assertEqual(user, self.user)

    def test_get_api_user_invalid_key(self):
        """Test with invalid API key."""
        request = self.factory.get('/')
        request.headers = {'Authorization': f'Bearer {INVALID_API_KEY}'}

        user, error = get_api_user(request)

        self.assertIsNone(user)
        self.assertEqual(
            error, NO_ACTIVE_SUBSCRIPTION)

    def test_get_api_user_no_subscription(self):
        """Test with user lacking API subscription."""
        # Delete the subscription
        self.user_subscription.delete()

        request = self.factory.get('/')
        request.headers = {'Authorization': f'Bearer {TEST_API_KEY}'}

        user, error = get_api_user(request)

        self.assertIsNone(user)
        self.assertEqual(
            error, NO_ACTIVE_SUBSCRIPTION)

    def test_get_request_data_json(self):
        """Test JSON data retrieval."""
        data = TEST_REQUEST_DATA
        request = self.factory.post('/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)

        result_data, error = get_request_data(request)

        self.assertIsNone(error)
        self.assertEqual(result_data, data)

    def test_get_request_data_json_invalid(self):
        """Test with invalid JSON."""
        request = self.factory.post('/',
                                    data='invalid json',
                                    content_type=JSON_CONTENT_TYPE)

        result_data, error = get_request_data(request)

        self.assertIsNone(result_data)
        self.assertEqual(error, INVALID_JSON)

    def test_get_request_data_query_params(self):
        """Test query parameter retrieval."""
        request = self.factory.get(
            f'/?source_language={ENGLISH_LANG_CODE}&target_language={FRENCH_LANG_CODE}')

        result_data, error = get_request_data(request, from_query=True)

        self.assertIsNone(error)
        self.assertEqual(result_data['source_language'], ENGLISH_LANG_CODE)
        self.assertEqual(result_data['target_language'], FRENCH_LANG_CODE)

    def test_get_request_data_query_params_too_long(self):
        """Test with query parameters exceeding length limits."""
        # Exceeding MAX_LANGUAGE_CODE_LENGTH
        long_lang = 'a' * (MAX_LANGUAGE_CODE_LENGTH + 5)
        request = self.factory.get(f'/?source_language={long_lang}')

        result_data, error = get_request_data(request, from_query=True)

        self.assertIsNone(result_data)
        self.assertEqual(error, SOURCE_LANGUAGE_TOO_LONG)

    def test_get_user_and_data_success(self):
        """Test successful retrieval of user and data."""
        data = {'test': 'data'}
        request = self.factory.post('/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.headers = {'Authorization': f'Bearer {TEST_API_KEY}'}

        user, result_data, error = get_user_and_data(request)

        self.assertIsNone(error)
        self.assertEqual(user, self.user)
        self.assertEqual(result_data, data)

    def test_get_user_and_data_auth_error(self):
        """Test with authentication error."""
        request = self.factory.post('/')
        request.headers = {'Authorization': f'Bearer {INVALID_API_KEY}'}

        user, result_data, error = get_user_and_data(request)

        self.assertIsNone(user)
        self.assertIsNone(result_data)
        self.assertIsNotNone(error)
        self.assertIn('detail', error)

    def test_detect_glossary_file_type_xlsx(self):
        """Test Excel XLSX file detection."""
        xlsx_content = XLSX_FILE_SIGNATURE

        extension, mime_type = detect_glossary_file_type(xlsx_content)

        self.assertEqual(extension, XLSX_EXTENSION)
        self.assertEqual(mime_type, XLSX_MIME_TYPE)

    def test_detect_glossary_file_type_xls(self):
        """Test Excel XLS file detection."""
        xls_content = XLS_FILE_SIGNATURE

        extension, mime_type = detect_glossary_file_type(xls_content)

        self.assertEqual(extension, XLS_EXTENSION)
        self.assertEqual(mime_type, XLS_MIME_TYPE)

    def test_detect_glossary_file_type_csv(self):
        """Test CSV file detection."""
        csv_content = CSV_FILE_CONTENT

        extension, mime_type = detect_glossary_file_type(csv_content)

        self.assertEqual(extension, CSV_EXTENSION)
        self.assertEqual(mime_type, CSV_MIME_TYPE)

    def test_detect_glossary_file_type_invalid(self):
        """Test with invalid binary file."""
        invalid_content = INVALID_BINARY_CONTENT

        extension, mime_type = detect_glossary_file_type(invalid_content)

        self.assertIsNone(extension)
        self.assertIsNone(mime_type)
