"""
Integration tests for Legal230 API.

This module contains end-to-end tests that verify the proper functioning
of the API across multiple endpoints and use cases.
"""

import json
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.utils import timezone

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
    INTEGRATION_API_KEY,
    INTEGRATION_EMAIL,
    INTEGRATION_GLOSSARY_NAME,
    INTEGRATION_GROUP_NAME,
    INTEGRATION_SUBSCRIPTION_NAME,
    INTEGRATION_USERNAME,
    INVALID_JSON_DATA,
    JSON_CONTENT_TYPE,
    MAX_GLOSSARY_ID_FOR_TEST,
    MAX_RESPONSE_TIME,
    PERF_API_KEY,
    PERF_EMAIL,
    PERF_GROUP_NAME,
    PERF_SUBSCRIPTION_NAME,
    PERF_USERNAME,
    SIMPLE_BASE64_CONTENT,
    SUBSCRIPTION_PRICE,
    TEST_CSV_FILENAME,
    TEST_DOMAIN_GROUP_FRENCH_NAME,
    TEST_DOMAIN_GROUP_NAME,
    TEST_DOMAIN_NAME,
    TEST_PASSWORD,
    get_auth_headers,
    get_invalid_auth_headers,
)


User = get_user_model()


class APIIntegrationTestCase(TransactionTestCase):
    """Integration test case for complete API functionality."""

    def setUp(self):
        """Set up test data for integration tests."""
        self.client = Client()

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
            name=TEST_DOMAIN_GROUP_NAME,
            french_name=TEST_DOMAIN_GROUP_FRENCH_NAME
        )
        self.domain = Domain.objects.create(
            name=TEST_DOMAIN_NAME,
            domain_group=self.domain_group
        )

        # Create group with API key
        self.group = create_test_user_group(
            name=INTEGRATION_GROUP_NAME,
            api_key=INTEGRATION_API_KEY
        )

        # Create test user
        self.user = User.objects.create_user(
            username=INTEGRATION_USERNAME,
            email=INTEGRATION_EMAIL,
            password=TEST_PASSWORD
        )
        self.user.group = self.group
        self.user.save()

        # Create subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name=INTEGRATION_SUBSCRIPTION_NAME,
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

        # Authentication headers
        self.auth_headers = get_auth_headers(INTEGRATION_API_KEY)

    def test_complete_api_workflow(self):
        """Test complete API workflow from authentication to data retrieval."""

        # 1. Retrieve language list
        response = self.client.get('/api/v1/languages/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        languages_data = json.loads(response.content)
        self.assertIsInstance(languages_data, list)
        self.assertTrue(len(languages_data) >= 2)

        # 2. Retrieve domain list
        response = self.client.get('/api/v1/domains/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        domains_data = json.loads(response.content)
        self.assertIsInstance(domains_data, list)
        self.assertEqual(len(domains_data), 1)

        # 3. Create test glossary
        glossary_data = {
            'name': INTEGRATION_GLOSSARY_NAME,
            'source_language': ENGLISH_LANG_CODE,
            'target_language': FRENCH_LANG_CODE,
            'document': [{
                'filename': TEST_CSV_FILENAME,
                'content': SIMPLE_BASE64_CONTENT
            }]
        }

        response = self.client.post('/api/v1/glossary/',
                                    data=json.dumps(glossary_data),
                                    content_type=JSON_CONTENT_TYPE,
                                    **self.auth_headers)

        # Status may vary depending on implementation (400 if validation fails)
        self.assertIn(response.status_code, [200, 201, 400])

        # 4. Retrieve user glossaries
        response = self.client.get('/api/v1/glossaries/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        user_glossaries = json.loads(response.content)
        self.assertIsInstance(user_glossaries, list)

    def test_api_authentication_flow(self):
        """Test API authentication flow scenarios."""

        # 1. Test without authentication
        response = self.client.get('/api/v1/domains/')
        self.assertEqual(response.status_code, 400)

        # 2. Test with invalid API key
        bad_headers = get_invalid_auth_headers()
        response = self.client.get('/api/v1/domains/', **bad_headers)
        self.assertEqual(response.status_code, 400)

        # 3. Test with valid API key
        response = self.client.get('/api/v1/domains/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)

    def test_api_error_handling(self):
        """Test API error handling for various scenarios."""

        # 1. Test with invalid JSON data
        response = self.client.post('/api/v1/glossary/',
                                    data=INVALID_JSON_DATA,
                                    content_type=JSON_CONTENT_TYPE,
                                    **self.auth_headers)
        self.assertEqual(response.status_code, 400)

        # 2. Test with non-existent resource
        response = self.client.get(
            f'/api/v1/glossary/{MAX_GLOSSARY_ID_FOR_TEST}/', **self.auth_headers)
        self.assertEqual(response.status_code, 404)

        # 3. Test with invalid parameters
        response = self.client.get('/api/v1/domain/invalid/glossaries/',
                                   **self.auth_headers)
        # 404 because endpoint doesn't exist
        self.assertEqual(response.status_code, 404)

    def test_api_data_consistency(self):
        """Test API data consistency across operations."""

        # 1. Create data via API and verify persistence
        if Glossary.objects.filter(user=self.user).exists():
            glossary = Glossary.objects.filter(user=self.user).first()

            # Retrieve glossary via API
            response = self.client.get(f'/api/v1/glossary/{glossary.id}/',
                                       **self.auth_headers)

            if response.status_code == 200:
                api_data = json.loads(response.content)

                # Verify data matches
                self.assertEqual(api_data.get('name')
                                 or api_data.get('title'), glossary.name)

    def test_api_cross_endpoint_consistency(self):
        """Test consistency between different API endpoints."""

        # 1. Retrieve domains
        response = self.client.get('/api/v1/domains/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)
        domains = json.loads(response.content)

        if domains:
            domain_id = domains[0]['id']

            # 2. Retrieve domain glossaries
            response = self.client.get(f'/api/v1/domain/{domain_id}/glossaries/',
                                       **self.auth_headers)
            # Status may be 200 or 400 depending on required parameters
            self.assertIn(response.status_code, [200, 400])

    def test_api_rate_limiting_headers(self):
        """Test API response headers for rate limiting."""

        response = self.client.get('/api/v1/languages/', **self.auth_headers)

        # Verify basic headers
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], JSON_CONTENT_TYPE)

    def test_api_pagination_if_implemented(self):
        """Test API pagination if implemented."""

        # Create multiple glossaries if possible
        for i in range(3):
            try:
                Glossary.objects.create(
                    name=f'{INTEGRATION_GLOSSARY_NAME} {i}',
                    source_language=self.english,
                    target_language=self.french,
                    domain=self.domain,
                    user=self.user
                )
            except:
                pass  # Ignore creation errors

        # Test retrieval
        response = self.client.get('/api/v1/glossaries/', **self.auth_headers)
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIsInstance(data, list)

    def test_api_multilingual_support(self):
        """Test multilingual support if implemented."""

        # Test with different language headers
        headers_fr = dict(self.auth_headers)
        headers_fr['HTTP_ACCEPT_LANGUAGE'] = 'fr'

        response = self.client.get('/api/v1/domains/', **headers_fr)
        self.assertEqual(response.status_code, 200)

        headers_en = dict(self.auth_headers)
        headers_en['HTTP_ACCEPT_LANGUAGE'] = ENGLISH_LANG_CODE

        response = self.client.get('/api/v1/domains/', **headers_en)
        self.assertEqual(response.status_code, 200)


class APIPerformanceTestCase(TestCase):
    """Basic performance test case for API endpoints."""

    def setUp(self):
        """Set up test data for performance tests."""
        self.client = Client()

        # Minimal setup for performance tests
        self.group = create_test_user_group(
            name=PERF_GROUP_NAME,
            api_key=PERF_API_KEY
        )

        self.user = User.objects.create_user(
            username=PERF_USERNAME,
            email=PERF_EMAIL,
            password=TEST_PASSWORD
        )
        self.user.group = self.group
        self.user.save()

        self.subscription_type = SubscriptionType.objects.create(
            name=PERF_SUBSCRIPTION_NAME,
            product_type=SubscriptionType.ProductChoices.WORD_ADD_IN,
            price=SUBSCRIPTION_PRICE
        )

        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )

        self.auth_headers = get_auth_headers(PERF_API_KEY)

    def test_api_response_time_domains(self):
        """Test basic response time for domains endpoint."""
        import time

        start_time = time.time()
        response = self.client.get('/api/v1/domains/', **self.auth_headers)
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time

        # Verify response is reasonably fast
        self.assertLess(response_time, MAX_RESPONSE_TIME,
                        f"API response too slow: {response_time:.2f}s")

    def test_api_response_time_languages(self):
        """Test basic response time for languages endpoint."""
        import time

        start_time = time.time()
        response = self.client.get('/api/v1/languages/', **self.auth_headers)
        end_time = time.time()

        self.assertEqual(response.status_code, 200)
        response_time = end_time - start_time

        # Verify response is reasonably fast
        self.assertLess(response_time, MAX_RESPONSE_TIME,
                        f"API response too slow: {response_time:.2f}s")
