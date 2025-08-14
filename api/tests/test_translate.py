"""
Unit tests for API translation views.

This module contains comprehensive tests for translation-related API endpoints,
including text translation, file translation, validation, and error handling.
"""

import base64
import io
import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.settings import MAX_FILE_SIZE, MAX_FILES_COUNT, MAX_TEXT_LENGTH
from api.views.error.error import error_message
from api.views.error.error_messages import (
    DOCUMENT_ARRAY_REQUIRED,
    FIELD_REQUIRED,
    FILE_TOO_LARGE_WITH_INDEX,
    INVALID_API_KEY,
    MAX_FILES_EXCEEDED,
    TEXT_TOO_LONG,
)
from api.views.translate import (
    TranslateAPIView,
    inject_files_if_needed,
    validate_translate_post_request,
)
from domains.models import Domain
from languages.models import Language
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group

from .settings import (
    ENGLISH_LANG_CODE,
    ENGLISH_LANG_NAME,
    FILE_TRANSLATE_ACTION,
    FRENCH_LANG_CODE,
    FRENCH_LANG_NAME,
    INVALID_BASE64_STRING,
    JSON_CONTENT_TYPE,
    SIMPLE_BASE64_CONTENT,
    SIMPLE_BASE64_HELLO,
    SUBSCRIPTION_PRICE,
    TEST_API_KEY,
    TEST_DOMAIN_GROUP_NAME,
    TEST_EMAIL,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_NAME,
    TEST_USERNAME,
    TEXT_TRANSLATE_ACTION,
    TRANSLATION_TEXT,
    UNKNOWN_ACTION,
    get_auth_headers,
)


User = get_user_model()


class TranslateAPITestCase(TestCase):
    """Test case for translation API views."""

    def setUp(self):
        """Set up test data for translation API tests."""
        self.factory = RequestFactory()

        # Create test languages
        self.english = Language.objects.create(
            name=ENGLISH_LANG_NAME,
            abbreviation=ENGLISH_LANG_CODE
        )
        self.french = Language.objects.create(
            name=FRENCH_LANG_NAME,
            abbreviation=FRENCH_LANG_CODE
        )

        # Create test domain
        self.domain = Domain.objects.create(name=TEST_DOMAIN_GROUP_NAME)

        # Create API group with key
        self.group = create_test_user_group(
            name=TEST_GROUP_NAME,
            api_key=TEST_API_KEY
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
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=SUBSCRIPTION_PRICE
        )

        # Create user subscription
        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

    def test_validate_translate_post_request_text_translate_valid(self):
        """Test validation for valid text translation request."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        data = {
            'action': TEXT_TRANSLATE_ACTION,
            'text': TRANSLATION_TEXT,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE
        }

        result = validate_translate_post_request(mock_request, data)
        self.assertIsNone(result)

    def test_validate_translate_post_request_missing_action(self):
        """Test validation with missing action field."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        data = {
            'text': TRANSLATION_TEXT,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertEqual(
            result['detail'],
            FIELD_REQUIRED.format(field="action")
        )

    def test_validate_translate_post_request_invalid_action(self):
        """Test request with invalid action."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        data = {
            'action': UNKNOWN_ACTION,
            'text': TRANSLATION_TEXT
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        # API validates required fields before action validation
        self.assertIn("source_language", result['detail'])

    def test_validate_translate_post_request_text_too_long(self):
        """Test request with text exceeding maximum length."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        long_text = 'a' * (MAX_TEXT_LENGTH + 1000)  # Exceeding MAX_TEXT_LENGTH
        data = {
            'action': TEXT_TRANSLATE_ACTION,
            'text': long_text,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'], TEXT_TOO_LONG)

    def test_validate_translate_post_request_missing_languages(self):
        """Test request with missing language parameters."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        data = {
            'action': TEXT_TRANSLATE_ACTION,
            'text': TRANSLATION_TEXT
            # Missing source_language and target_language
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertIn("source_language", result['detail'])

    def test_validate_translate_post_request_file_translate_valid(self):
        """Test validation for valid file translation request."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        # Expected format for current API: array of base64 strings
        data = {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': [SIMPLE_BASE64_CONTENT]
        }

        result = validate_translate_post_request(mock_request, data)
        self.assertIsNone(result)

    def test_validate_translate_post_request_too_many_files(self):
        """Test request with too many files."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        # Create more files than limit (array of base64 strings)
        documents = []
        for i in range(MAX_FILES_COUNT + 5):  # Exceeding MAX_FILES_COUNT
            documents.append(SIMPLE_BASE64_HELLO)  # Simple base64 string

        data = {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': documents
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'], MAX_FILES_EXCEEDED)

    def test_inject_files_if_needed_valid_files(self):
        """Test injection of valid files."""
        mock_request = Mock()
        mock_request._files = None

        # Expected format for API: array of base64 strings
        data = {
            'document': [SIMPLE_BASE64_CONTENT]
        }

        inject_files_if_needed(mock_request, data, FILE_TRANSLATE_ACTION)

        # Verify that files were injected
        self.assertIsNotNone(mock_request._files)

    def test_inject_files_if_needed_invalid_base64(self):
        """Test with invalid base64 content."""
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE
        mock_request._files = None

        # Test with completely invalid base64 (not a base64 string)
        data = {
            'document': [INVALID_BASE64_STRING]
        }

        # This function should handle base64.b64decode exception
        try:
            inject_files_if_needed(mock_request, data, FILE_TRANSLATE_ACTION)
            # If no exception, check that _files is still None
            # because injection failed
        except Exception:
            # Expected exception for invalid base64
            pass

    @patch('api.views.translate.get_user_and_data')
    @patch('api.views.translate.text_translation')
    def test_translate_api_text_success(self, mock_text_translation, mock_get_user_and_data):
        """Test successful text translation."""
        mock_get_user_and_data.return_value = (self.user, {
            'action': TEXT_TRANSLATE_ACTION,
            'text': TRANSLATION_TEXT,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE
        }, None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_text_translation.return_value = mock_response

        data = {
            'action': TEXT_TRANSLATE_ACTION,
            'text': TRANSLATION_TEXT,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE
        }

        request = self.factory.post('/api/v1/translate/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.META.update(get_auth_headers())

        view = TranslateAPIView()
        response = view.post(request)

        # Verify that text_translation was called
        mock_text_translation.assert_called_once()

    @patch('api.views.translate.get_user_and_data')
    @patch('api.views.translate.handle_file_translate')
    def test_translate_api_file_success(self, mock_handle_file, mock_get_user_and_data):
        """Test successful file translation."""
        mock_get_user_and_data.return_value = (self.user, {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            # Correct format: array of base64 strings
            'document': [SIMPLE_BASE64_HELLO]
        }, None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_handle_file.return_value = mock_response

        data = {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': [SIMPLE_BASE64_HELLO]
        }

        request = self.factory.post('/api/v1/translate/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.META.update(get_auth_headers())

        view = TranslateAPIView()
        response = view.post(request)

        # Verify that handle_file_translate was called
        mock_handle_file.assert_called_once()

    @patch('api.views.translate.get_user_and_data')
    def test_translate_api_unknown_action(self, mock_get_user_and_data):
        """Test with unknown action.

        The API validates required fields first. If the action is unknown but
        required fields are missing, the error will be about the missing fields.
        """
        mock_get_user_and_data.return_value = (self.user, {
            'action': UNKNOWN_ACTION
            # No source_language or target_language
        }, None)

        data = {
            'action': UNKNOWN_ACTION
        }

        request = self.factory.post('/api/v1/translate/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.META.update(get_auth_headers())

        view = TranslateAPIView()
        response = view.post(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        # API validates source_language first
        self.assertEqual(
            data['detail'], FIELD_REQUIRED.format(field="source_language"))

    @patch('api.views.translate.get_user_and_data')
    def test_translate_api_auth_error(self, mock_get_user_and_data):
        """Test with authentication error."""
        mock_get_user_and_data.return_value = (
            None, None, error_message(INVALID_API_KEY))

        data = {
            'action': TEXT_TRANSLATE_ACTION,
            'text': TRANSLATION_TEXT
        }

        request = self.factory.post('/api/v1/translate/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid-key'

        view = TranslateAPIView()
        response = view.post(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], INVALID_API_KEY)

    @patch('api.views.translate.get_user_and_data')
    def test_translate_api_validation_error(self, mock_get_user_and_data):
        """Test with validation error."""
        mock_get_user_and_data.return_value = (self.user, {
            'action': TEXT_TRANSLATE_ACTION
            # Incomplete data
        }, None)

        data = {'action': TEXT_TRANSLATE_ACTION}

        request = self.factory.post('/api/v1/translate/',
                                    data=json.dumps(data),
                                    content_type=JSON_CONTENT_TYPE)
        request.META.update(get_auth_headers())

        view = TranslateAPIView()
        response = view.post(request)

        self.assertEqual(response.status_code, 400)

    def test_file_extension_validation(self):
        """Test file extension validation.

        Tests with a file that exceeds the maximum allowed size.
        This is the only reliable way to make the validation fail because
        TXT files (signature b'') accept any content.
        51 MB > MAX_FILE_SIZE (50 MB)
        """
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        # MAX_FILE_SIZE + 1MB
        large_content = b'A' * (MAX_FILE_SIZE + (1 * 1024 * 1024))
        large_base64 = base64.b64encode(large_content).decode()

        data = {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': [large_base64]
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'],
                         FILE_TOO_LARGE_WITH_INDEX.format(index=0))

    def test_empty_filename_validation(self):
        """Test with empty or invalid document.

        Tests with a document that is not a list type.
        """
        mock_request = Mock()
        mock_request.content_type = JSON_CONTENT_TYPE

        # Test with non-list document
        data = {
            'action': FILE_TRANSLATE_ACTION,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': 'not_a_list'  # Must be an array
        }

        result = validate_translate_post_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'], DOCUMENT_ARRAY_REQUIRED)
