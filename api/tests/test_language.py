"""
Unit tests for API language views.

This module contains comprehensive tests for language-related API endpoints,
including language listing and validation.
"""

import json
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.views.error.error import error_message
from api.views.error.error_messages import INVALID_API_KEY
from api.views.language import LanguageAPIView
from languages.models import Language
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group

from .settings import (
    ENGLISH_FRENCH_NAME,
    ENGLISH_LANG_CODE,
    ENGLISH_LANG_NAME,
    FRENCH_FRENCH_NAME,
    FRENCH_LANG_CODE,
    FRENCH_LANG_NAME,
    INVALID_API_BEARER,
    SPANISH_FRENCH_NAME,
    SPANISH_LANG_CODE,
    SPANISH_LANG_NAME,
    SUBSCRIPTION_PRICE,
    TEST_API_KEY,
    TEST_EMAIL,
    TEST_GROUP_NAME,
    TEST_LANGUAGE_FRENCH_NAME,
    TEST_LANGUAGE_NAME,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_NAME,
    TEST_USERNAME,
)

User = get_user_model()


class LanguageAPITestCase(TestCase):
    """Test case for language API views."""

    def setUp(self):
        """Set up test data for language API tests."""
        self.factory = RequestFactory()

        # Create test languages
        self.english = Language.objects.create(
            name=ENGLISH_LANG_NAME,
            abbreviation=ENGLISH_LANG_CODE,
            french_name=ENGLISH_FRENCH_NAME
        )
        self.french = Language.objects.create(
            name=FRENCH_LANG_NAME,
            abbreviation=FRENCH_LANG_CODE,
            french_name=FRENCH_FRENCH_NAME
        )
        self.spanish = Language.objects.create(
            name=SPANISH_LANG_NAME,
            abbreviation=SPANISH_LANG_CODE,
            french_name=SPANISH_FRENCH_NAME
        )

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

    @patch('api.views.language.get_user_and_data')
    def test_language_api_success(self, mock_get_user_and_data):
        """Test successful retrieval of language list."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get('/api/v1/languages/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

        view = LanguageAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify data structure
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 3)

        # Verify specific languages
        language_codes = [lang['language_code'] for lang in data]
        language_names = [lang['name'] for lang in data]

        self.assertIn(ENGLISH_LANG_CODE, language_codes)
        self.assertIn(FRENCH_LANG_CODE, language_codes)
        self.assertIn(SPANISH_LANG_CODE, language_codes)

        self.assertIn(ENGLISH_LANG_NAME, language_names)
        self.assertIn(FRENCH_LANG_NAME, language_names)
        self.assertIn(SPANISH_LANG_NAME, language_names)

    @patch('api.views.language.get_user_and_data')
    def test_language_api_auth_error(self, mock_get_user_and_data):
        """Test authentication error handling."""
        mock_get_user_and_data.return_value = (
            None, None, error_message(INVALID_API_KEY)
        )

        request = self.factory.get('/api/v1/languages/')
        request.META['HTTP_AUTHORIZATION'] = INVALID_API_BEARER

        view = LanguageAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], INVALID_API_KEY)

    @patch('api.views.language.get_user_and_data')
    def test_language_api_empty_database(self, mock_get_user_and_data):
        """Test behavior with empty database."""
        # Delete all languages
        Language.objects.all().delete()

        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get('/api/v1/languages/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

        view = LanguageAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 0)

    def test_language_api_data_format(self):
        """Test format of returned data."""
        with patch('api.views.language.get_user_and_data') as mock_get_user_and_data:
            mock_get_user_and_data.return_value = (self.user, None, None)

            request = self.factory.get('/api/v1/languages/')
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

            view = LanguageAPIView()
            response = view.get(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            # Verify that each language has the correct keys
            for language in data:
                self.assertIn('name', language)
                self.assertIn('language_code', language)
                self.assertIsInstance(language['name'], str)
                self.assertIsInstance(language['language_code'], str)

    def test_language_api_with_none_abbreviation(self):
        """Test language with None abbreviation."""
        # Create a language with None abbreviation
        Language.objects.create(
            name=TEST_LANGUAGE_NAME,
            abbreviation=None,
            french_name=TEST_LANGUAGE_FRENCH_NAME
        )

        with patch('api.views.language.get_user_and_data') as mock_get_user_and_data:
            mock_get_user_and_data.return_value = (self.user, None, None)

            request = self.factory.get('/api/v1/languages/')
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

            view = LanguageAPIView()
            response = view.get(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            # Verify language with None abbreviation is included
            test_language = next(
                (lang for lang in data if lang['name'] == TEST_LANGUAGE_NAME),
                None
            )
            self.assertIsNotNone(test_language)
            self.assertIsNone(test_language['language_code'])

    @patch('api.views.language.get_user_and_data')
    def test_language_api_ordering(self, mock_get_user_and_data):
        """Test ordering of returned languages."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get('/api/v1/languages/')
        request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

        view = LanguageAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify ordering (default order based on model ordering)
        language_names = [lang['name'] for lang in data]

        # Names should be in the order defined by the Language model
        # (based on Meta.ordering configuration in the model)
        expected_order = [
            ENGLISH_LANG_NAME,
            FRENCH_LANG_NAME,
            SPANISH_LANG_NAME
        ]
        self.assertEqual(language_names, expected_order)
