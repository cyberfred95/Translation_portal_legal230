"""
Unit tests for API domain views.

This module contains comprehensive tests for domain-related API endpoints,
including domain listing and domain-specific glossary filtering.
"""

import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.views.domain import (
    DomainDefaultGlossariesAPIView,
    DomainListAPIView,
    filter_glossaries,
    partial_domain_to_json,
    validate_domain_default_glossaries_get_request,
)
from api.views.error.error import error_message
from api.views.error.error_messages import (
    DOMAIN_ID_MUST_BE_INTEGER,
    FIELD_REQUIRED_IF_PROVIDED,
    FIELD_TOO_LONG_LANGUAGE,
    ID_MUST_BE_INTEGER,
    ID_OUT_OF_RANGE_DOMAIN,
    INVALID_API_KEY,
    SOURCE_LANGUAGE_NOT_FOUND,
    TARGET_LANGUAGE_NOT_FOUND,
)
from domains.models import Domain, DomainGroup
from glossaries.models import Glossary
from languages.models import Language
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group

from .settings import (
    ENGLISH_LANG_CODE,
    ENGLISH_LANG_NAME,
    FRENCH_LANG_CODE,
    FRENCH_LANG_NAME,
    SUBSCRIPTION_PRICE,
    TEST_API_KEY,
    TEST_CONTENT_TYPE,
    TEST_DOMAIN_FRENCH_NAME,
    TEST_DOMAIN_GROUP_FRENCH_NAME,
    TEST_DOMAIN_GROUP_NAME,
    TEST_DOMAIN_NAME,
    TEST_DOMAIN_NO_GROUP_NAME,
    TEST_EMAIL,
    TEST_FILE_CONTENT,
    TEST_FILE_NAME,
    TEST_GLOSSARY_NAME,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_NAME,
    TEST_USERNAME,
    get_auth_headers,
    setup_glossary_service_patches,
    teardown_glossary_service_patches,
)

User = get_user_model()


class DomainAPITestCase(TestCase):

    def setUp(self):
        # Set up patches using helper functions
        setup_glossary_service_patches(self)
        
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

        # Create user group with API key
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
            product_type=SubscriptionType.ProductChoices.WORD_ADD_IN,
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

        # Create domain group
        self.domain_group = DomainGroup.objects.create(
            name=TEST_DOMAIN_GROUP_NAME,
            french_name=TEST_DOMAIN_GROUP_FRENCH_NAME
        )

        # Create domain
        self.domain = Domain.objects.create(
            name=TEST_DOMAIN_NAME,
            french_name=TEST_DOMAIN_FRENCH_NAME,
            domain_group=self.domain_group
        )

        # Create test file and glossary
        test_file = SimpleUploadedFile(
            name=TEST_FILE_NAME,
            content=TEST_FILE_CONTENT,
            content_type=TEST_CONTENT_TYPE
        )

        self.glossary = Glossary.objects.create(
            name=TEST_GLOSSARY_NAME,
            source_language=self.english,
            target_language=self.french,
            domain=self.domain,
            group=None,
            file=test_file
        )

    def tearDown(self):
        """Clean up patches after each test."""
        teardown_glossary_service_patches(self)

    def test_partial_domain_to_json_with_group(self):
        """Test that partial_domain_to_json returns correct JSON for domain with group."""
        result = partial_domain_to_json(self.domain)

        expected = {
            "id": self.domain.id,
            "domain_group": TEST_DOMAIN_GROUP_NAME,
            "name": TEST_DOMAIN_NAME
        }
        self.assertEqual(result, expected)

    def test_partial_domain_to_json_without_group(self):
        """Test that partial_domain_to_json returns correct JSON for domain without group."""
        domain_no_group = Domain.objects.create(name=TEST_DOMAIN_NO_GROUP_NAME)
        result = partial_domain_to_json(domain_no_group)

        expected = {
            "id": domain_no_group.id,
            "domain_group": None,
            "name": TEST_DOMAIN_NO_GROUP_NAME
        }
        self.assertEqual(result, expected)

    def test_validate_domain_default_glossaries_valid_data(self):
        """Test that validation passes with valid language data and domain ID."""
        data = {
            "source_language": "en",
            "target_language": "fr"
        }

        result = validate_domain_default_glossaries_get_request(data, 1)
        self.assertIsNone(result)

    def test_validate_domain_default_glossaries_empty_language(self):
        """Test that validation fails when source language is empty string."""
        data = {
            "source_language": "",
            "target_language": "fr"
        }

        result = validate_domain_default_glossaries_get_request(data)

        self.assertIsNotNone(result)
        self.assertIn(FIELD_REQUIRED_IF_PROVIDED.split("'")
                      [0], result['detail'])

    def test_validate_domain_default_glossaries_language_too_long(self):
        """Test that validation fails when language code exceeds maximum length."""
        data = {
            "source_language": "a" * 15,
            "target_language": "fr"
        }

        result = validate_domain_default_glossaries_get_request(data)

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'], FIELD_TOO_LONG_LANGUAGE.format(
            field="source_language"))

    def test_validate_domain_default_glossaries_invalid_domain_id(self):
        """Test that validation fails when domain ID is not an integer."""
        data = {"source_language": "en", "target_language": "fr"}

        result = validate_domain_default_glossaries_get_request(
            data, "invalid")

        self.assertIsNotNone(result)
        self.assertEqual(result['detail'],
                         ID_MUST_BE_INTEGER.format(field="id_domain"))

    def test_validate_domain_default_glossaries_domain_id_out_of_range(self):
        """Test that validation fails when domain ID is out of valid range."""
        data = {"source_language": "en", "target_language": "fr"}

        result = validate_domain_default_glossaries_get_request(data, -1)

        self.assertIsNotNone(result)
        self.assertEqual(
            result['detail'], ID_OUT_OF_RANGE_DOMAIN.format(field="id_domain"))

    @patch('api.views.domain.get_user_and_data')
    def test_domain_list_api_success(self, mock_get_user_and_data):
        """Test successful retrieval of domain list through API endpoint."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get('/api/v1/domains/')
        request.META.update(get_auth_headers())

        view = DomainListAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Contract Law')
        self.assertEqual(data[0]['domain_group'], 'Legal')

    @patch('api.views.domain.get_user_and_data')
    def test_domain_list_api_auth_error(self, mock_get_user_and_data):
        """Test domain list API returns error with invalid authentication."""
        mock_get_user_and_data.return_value = (
            None, None, error_message(INVALID_API_KEY))

        request = self.factory.get('/api/v1/domains/')

        view = DomainListAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], INVALID_API_KEY)

    def test_filter_glossaries_with_valid_languages(self):
        """Test glossary filtering with valid source and target language codes."""
        mock_request = Mock()
        mock_request.user = self.user

        data = {
            "source_language": "en",
            "target_language": "fr"
        }

        glossaries, error = filter_glossaries(
            data, self.domain.id, mock_request)

        self.assertIsNone(error)
        self.assertIsInstance(glossaries, list)
        self.assertEqual(len(glossaries), 1)

    def test_filter_glossaries_invalid_source_language(self):
        """Test that glossary filtering fails with non-existent source language."""
        mock_request = Mock()
        mock_request.user = self.user

        data = {
            "source_language": "xx",  # Non-existent language
            "target_language": "fr"
        }

        glossaries, error = filter_glossaries(
            data, self.domain.id, mock_request)

        self.assertIsNone(glossaries)
        self.assertIsNotNone(error)
        self.assertEqual(error['detail'], SOURCE_LANGUAGE_NOT_FOUND)

    def test_filter_glossaries_invalid_target_language(self):
        """Test that glossary filtering fails with non-existent target language."""
        mock_request = Mock()
        mock_request.user = self.user

        data = {
            "source_language": "en",
            "target_language": "yy"  # Non-existent language
        }

        glossaries, error = filter_glossaries(
            data, self.domain.id, mock_request)

        self.assertIsNone(glossaries)
        self.assertIsNotNone(error)
        self.assertEqual(
            error['detail'], TARGET_LANGUAGE_NOT_FOUND.format(language='yy'))

    def test_filter_glossaries_invalid_domain_id(self):
        """Test that glossary filtering fails with invalid domain ID type."""
        mock_request = Mock()
        mock_request.user = self.user

        data = {
            "source_language": "en",
            "target_language": "fr"
        }

        glossaries, error = filter_glossaries(data, "invalid", mock_request)

        self.assertIsNone(glossaries)
        self.assertIsNotNone(error)
        self.assertEqual(error['detail'], DOMAIN_ID_MUST_BE_INTEGER)

    def test_filter_glossaries_user_without_group(self):
        """Test glossary filtering for user without assigned group returns public glossaries."""
        user_no_group = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        mock_request = Mock()
        mock_request.user = user_no_group

        data = {
            "source_language": "en",
            "target_language": "fr"
        }

        glossaries, error = filter_glossaries(
            data, self.domain.id, mock_request)

        self.assertIsNone(error)
        self.assertIsInstance(glossaries, list)
        # Should return only public glossaries

    @patch('api.views.domain.get_user_and_data')
    @patch('api.views.domain.filter_glossaries')
    def test_domain_default_glossaries_api_success(self, mock_filter_glossaries, mock_get_user_and_data):
        """Test successful retrieval of domain-specific glossaries through API endpoint."""
        mock_get_user_and_data.return_value = (
            self.user,
            {"source_language": "en", "target_language": "fr"},
            None
        )
        mock_filter_glossaries.return_value = (
            [{"id": 1, "name": TEST_GLOSSARY_NAME}], None)

        request = self.factory.get('/api/v1/domain/1/glossaries/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

        view = DomainDefaultGlossariesAPIView()
        response = view.get(request, id_domain=1)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], TEST_GLOSSARY_NAME)

    @patch('api.views.domain.get_user_and_data')
    def test_domain_default_glossaries_api_validation_error(self, mock_get_user_and_data):
        """Test domain glossaries API returns validation error with invalid data."""
        mock_get_user_and_data.return_value = (
            self.user,
            {"source_language": ""},
            None
        )

        request = self.factory.get('/api/v1/domain/1/glossaries/')
        request.META.update(get_auth_headers())

        view = DomainDefaultGlossariesAPIView()
        response = view.get(request, id_domain=1)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('detail', data)

    @patch('api.views.domain.get_user_and_data')
    @patch('api.views.domain.filter_glossaries')
    def test_domain_default_glossaries_api_filter_error(self, mock_filter_glossaries, mock_get_user_and_data):
        """Test domain glossaries API returns error when glossary filtering fails."""
        mock_get_user_and_data.return_value = (
            self.user,
            {"source_language": "en", "target_language": "fr"},
            None
        )
        mock_filter_glossaries.return_value = (
            None, error_message(SOURCE_LANGUAGE_NOT_FOUND.format(language='en')))

        request = self.factory.get('/api/v1/domain/1/glossaries/')
        request.META.update(get_auth_headers())

        view = DomainDefaultGlossariesAPIView()
        response = view.get(request, id_domain=1)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(
            data['detail'], SOURCE_LANGUAGE_NOT_FOUND.format(language='en'))
