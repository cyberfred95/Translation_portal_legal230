"""
Unit tests for API glossary views.

This module contains comprehensive tests for glossary-related API endpoints,
including glossary creation, retrieval, validation, and deletion.
"""

import logging
import json
from datetime import timedelta
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory, TestCase
from django.utils import timezone

from api.views.error.error import error_message
from api.views.error.error_messages import (
    ID_MUST_BE_INTEGER,
    ID_OUT_OF_RANGE_GLOSSARY,
    INVALID_API_KEY,
    USER_GLOSSARY_NOT_FOUND,
)
from api.views.glossary import (
    GlossaryAPIView,
    GlossaryExistAPIView,
    validate_glossary_id,
    validate_glossary_request,
)
from domains.models import Domain, DomainGroup
from glossaries.models import Glossary
from languages.models import Language
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import UserGroup

from .settings import (
    ANOTHER_INVALID_LANGUAGE_CODE,
    ENGLISH_LANG_CODE,
    ENGLISH_LANG_NAME,
    FRENCH_LANG_CODE,
    FRENCH_LANG_NAME,
    INVALID_LANGUAGE_CODE,
    SUBSCRIPTION_PRICE,
    TEST_API_KEY,
    TEST_CONTENT_TYPE,
    TEST_DOMAIN_GROUP_NAME,
    TEST_DOMAIN_NAME,
    TEST_EMAIL,
    TEST_FILE_CONTENT,
    TEST_FILE_NAME,
    TEST_GLOSSARY_NAME,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_SUBSCRIPTION_NAME,
    TEST_USERNAME,
    get_auth_headers,
)

User = get_user_model()


class GlossaryAPITestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        logging.getLogger('django.request').setLevel(logging.CRITICAL)
    """Test case for glossary API views."""

    def setUp(self):
        """Set up test data for glossary API tests."""
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
        self.domain_group = DomainGroup.objects.create(
            name=TEST_DOMAIN_GROUP_NAME
        )
        self.domain = Domain.objects.create(
            name=TEST_DOMAIN_NAME,
            domain_group=self.domain_group
        )

        # Create API group
        self.group = UserGroup.objects.create(
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

        # Create test glossary with mock file
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
            user=self.user,
            file=test_file
        )

    def test_validate_glossary_id_valid(self):
        """Test glossary ID validation with valid ID."""
        result = validate_glossary_id(self.glossary.id)
        self.assertIsNone(result)

    def test_validate_glossary_id_invalid_type(self):
        """Test glossary ID validation with invalid type."""
        result = validate_glossary_id("invalid")

        self.assertIsNotNone(result)
        self.assertEqual(
            result['detail'],
            ID_MUST_BE_INTEGER.format(field="id_glossary")
        )

    def test_validate_glossary_id_out_of_range(self):
        """Test glossary ID validation with out of range value."""
        result = validate_glossary_id(-1)

        self.assertIsNotNone(result)
        self.assertEqual(
            result['detail'],
            ID_OUT_OF_RANGE_GLOSSARY.format(field="id_glossary")
        )

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_get_all(self, mock_get_user_and_data):
        """Test retrieval of all user glossaries."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get('/api/v1/glossaries/')
        request.META.update(get_auth_headers())

        view = GlossaryExistAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_get_specific(self, mock_get_user_and_data):
        """Test retrieval of a specific glossary."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.get(f'/api/v1/glossary/{self.glossary.id}/')
        request.META.update(get_auth_headers())

        view = GlossaryExistAPIView()
        response = view.get(request, id_glossary=self.glossary.id)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIsInstance(data, dict)
        self.assertIn('name', data)

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_get_not_found(self, mock_get_user_and_data):
        """Test retrieval of non-existent glossary."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        non_existent_id = 99999
        request = self.factory.get(f'/api/v1/glossary/{non_existent_id}/')
        request.META.update(get_auth_headers())

        view = GlossaryExistAPIView()
        response = view.get(request, id_glossary=non_existent_id)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], USER_GLOSSARY_NOT_FOUND)

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_delete_success(self, mock_get_user_and_data):
        """Test successful glossary deletion."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        request = self.factory.delete(f'/api/v1/glossary/{self.glossary.id}/')
        request.META.update(get_auth_headers())

        view = GlossaryExistAPIView()
        response = view.delete(request, id_glossary=self.glossary.id)

        self.assertEqual(response.status_code, 204)

        # Verify glossary was deleted
        self.assertFalse(Glossary.objects.filter(id=self.glossary.id).exists())

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_delete_not_found(self, mock_get_user_and_data):
        """Test deletion of non-existent glossary."""
        mock_get_user_and_data.return_value = (self.user, None, None)

        non_existent_id = 99999
        request = self.factory.delete(f'/api/v1/glossary/{non_existent_id}/')
        request.META.update(get_auth_headers())

        view = GlossaryExistAPIView()
        response = view.delete(request, id_glossary=non_existent_id)

        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], USER_GLOSSARY_NOT_FOUND)

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_exist_api_auth_error(self, mock_get_user_and_data):
        """Test glossary API with authentication error."""
        mock_get_user_and_data.return_value = (
            None, None, error_message(INVALID_API_KEY))

        request = self.factory.get('/api/v1/glossaries/')
        request.META['HTTP_AUTHORIZATION'] = 'Bearer invalid-key'

        view = GlossaryExistAPIView()
        response = view.get(request)

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertEqual(data['detail'], INVALID_API_KEY)

    def test_validate_glossary_request_missing_fields(self):
        """Test glossary request validation with missing fields."""
        mock_request = Mock()
        mock_request.content_type = 'application/json'

        data = {
            'name': TEST_GLOSSARY_NAME
            # Missing source_language, target_language, etc.
        }

        result = validate_glossary_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertIn('detail', result)

    def test_validate_glossary_request_invalid_languages(self):
        """Test glossary request validation with invalid languages."""
        mock_request = Mock()
        mock_request.content_type = 'application/json'

        data = {
            'name': TEST_GLOSSARY_NAME,
            'source_language': INVALID_LANGUAGE_CODE,
            'target_language': ANOTHER_INVALID_LANGUAGE_CODE
        }

        result = validate_glossary_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertIn('detail', result)

    def test_validate_glossary_request_same_languages(self):
        """Test glossary request validation with identical source and target languages."""
        mock_request = Mock()
        mock_request.content_type = 'application/json'

        data = {
            'name': TEST_GLOSSARY_NAME,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': ENGLISH_LANG_CODE  # Same language
        }

        result = validate_glossary_request(mock_request, data)

        self.assertIsNotNone(result)
        self.assertIn('detail', result)

    @patch('api.views.glossary.get_user_and_data')
    @patch('api.views.glossary.validate_glossary_request')
    @patch('api.views.glossary.handle_add_glossary_post')
    def test_glossary_api_post_json(
        self,
        mock_handle_post,
        mock_validate,
        mock_get_user_and_data
    ):
        """Test glossary creation via JSON API."""
        mock_get_user_and_data.return_value = (
            self.user,
            {
                'name': 'New Glossary',
                'source_language': 'en',
                'target_language': 'fr'
            },
            None
        )
        mock_validate.return_value = None  # No validation error
        mock_handle_post.return_value = Mock(status_code=201)

        data = {
            'name': 'New Glossary',
            'source_language': 'en',
            'target_language': 'fr'
        }

        request = self.factory.post(
            '/api/v1/glossary/',
            data=json.dumps(data),
            content_type='application/json'
        )
        request.META.update(get_auth_headers())

        view = GlossaryAPIView()
        response = view.post(request)

        # Verify functions were called
        mock_get_user_and_data.assert_called_once()
        mock_validate.assert_called_once()
        mock_handle_post.assert_called_once()

    @patch('api.views.glossary.get_user_and_data')
    def test_glossary_api_post_validation_error(self, mock_get_user_and_data):
        """Test glossary creation with validation error."""
        mock_get_user_and_data.return_value = (
            self.user,
            {
                'name': 'New Glossary'
                # Incomplete data
            },
            None
        )

        data = {'name': 'New Glossary'}

        request = self.factory.post(
            '/api/v1/glossary/',
            data=json.dumps(data),
            content_type='application/json'
        )
        request.META.update(get_auth_headers())

        view = GlossaryAPIView()
        response = view.post(request)

        self.assertEqual(response.status_code, 400)

    def test_glossary_user_isolation(self):
        """Test that users can only see their own glossaries."""
        # Create another user
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )

        # Create glossary for the other user
        other_test_file = SimpleUploadedFile(
            name='other_test_glossary.csv',
            content=b'en,fr\ntest,test\nother,autre',
            content_type='text/csv'
        )

        other_glossary = Glossary.objects.create(
            name='Other User Glossary',
            source_language=self.english,
            target_language=self.french,
            domain=self.domain,
            user=other_user,
            file=other_test_file
        )

        with patch('api.views.glossary.get_user_and_data') as mock_get_user_and_data:
            mock_get_user_and_data.return_value = (self.user, None, None)

            request = self.factory.get('/api/v1/glossaries/')
            request.META['HTTP_AUTHORIZATION'] = f'Bearer {TEST_API_KEY}'

            view = GlossaryExistAPIView()
            response = view.get(request)

            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)

            # User should only see their own glossary
            self.assertEqual(len(data), 1)
            self.assertEqual(
                data[0]['name'] if 'name' in data[0] else data[0].get('name'),
                TEST_GLOSSARY_NAME
            )
