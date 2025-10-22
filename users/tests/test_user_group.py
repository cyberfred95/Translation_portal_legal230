"""
Tests for UserGroup model functionality.
"""

from django.test import TestCase
from unittest.mock import patch

from users.models import UserGroup
from tests.mock import mock_api_key_generation, mock_api_key_generation_failure, mock_no_settings

# Import des constantes centralisées
from .settings import (
    TEST_GROUP_NAME,
    TEST_API_KEY,
    EXISTING_API_KEY,
    GENERATED_API_KEY,
    USER_GROUP_VERBOSE_NAME,
    USER_GROUP_VERBOSE_NAME_PLURAL,
    EXPECTED_API_TIMEOUT,
    EXPECTED_LABEL_ID,
    API_CREATE_KEY_ENDPOINT,
    API_HEADERS_CONTENT_TYPE,
    API_TOKEN_KEY,
    API_MAIN_TOKEN,
)


class UserGroupAPIKeyTestCase(TestCase):
    """Test case for UserGroup API key auto-generation."""

    @patch('django.conf.settings.CLOUDSTORAGE_API_KEY', API_MAIN_TOKEN)
    @patch('django.conf.settings.CUSTOM_MT_CONSOLE_URL', 'https://console.custom.mt/')
    @mock_api_key_generation(GENERATED_API_KEY)
    def test_api_key_auto_generation_success(self, mock_post):
        """Test that API key is auto-generated when UserGroup is saved without one."""
        
        # Create UserGroup without api_key
        group = UserGroup(name=TEST_GROUP_NAME)
        
        # Save should trigger API key generation
        group.save()
        
        # Verify API key was set
        self.assertEqual(group.api_key, GENERATED_API_KEY)
        
        # Verify API call was made correctly
        mock_post.assert_called_once_with(
            API_CREATE_KEY_ENDPOINT,
            json={'label': EXPECTED_LABEL_ID},  # Now uses the group ID
            headers={
                API_TOKEN_KEY: API_MAIN_TOKEN,
                'Content-Type': API_HEADERS_CONTENT_TYPE
            },
            timeout=EXPECTED_API_TIMEOUT
        )

    @mock_api_key_generation_failure()
    def test_api_key_auto_generation_failure_fallback(self, mock_post):
        """Test that UUID fallback is used when API call fails."""
        
        # Create UserGroup without api_key
        group = UserGroup(name=TEST_GROUP_NAME)
        
        # Save should trigger API key generation with UUID fallback
        group.save()
        
        # Verify API key was set (should be a UUID)
        self.assertIsNotNone(group.api_key)
        self.assertTrue(len(group.api_key) > 0)
        # UUID format check (36 characters with hyphens)
        self.assertTrue(len(group.api_key.replace('-', '')) == 32)

    def test_existing_api_key_not_overwritten(self):
        """Test that existing API key is not overwritten."""
        
        # Create UserGroup with existing api_key
        group = UserGroup(name=TEST_GROUP_NAME, api_key=EXISTING_API_KEY)
        group.save()
        
        # Verify API key was not changed
        self.assertEqual(group.api_key, EXISTING_API_KEY)

    @mock_no_settings()
    def test_api_key_generation_no_settings(self):
        """Test fallback to UUID when main settings are not available."""
        
        # Create UserGroup without api_key
        group = UserGroup(name=TEST_GROUP_NAME)
        group.save()
        
        # Verify API key was set to UUID fallback
        self.assertIsNotNone(group.api_key)
        self.assertTrue(len(group.api_key) > 0)

    def test_generate_quoting_number(self):
        """Test that quoting number generation works correctly."""
        
        group = UserGroup(name=TEST_GROUP_NAME, api_key=TEST_API_KEY)
        group.save()
        
        # Test initial quoting number generation
        quote_number = group.generate_quoting_number()
        
        # Verify format: YYYY/MM/1
        from django.utils.timezone import now
        expected_prefix = now().strftime('%Y/%m')
        self.assertTrue(quote_number.startswith(expected_prefix))
        self.assertTrue(quote_number.endswith('/1'))
        
        # Test incremental generation
        quote_number_2 = group.generate_quoting_number()
        self.assertTrue(quote_number_2.endswith('/2'))

    def test_user_group_str_representation(self):
        """Test UserGroup string representation."""
        
        group = UserGroup(name=TEST_GROUP_NAME, api_key=TEST_API_KEY)
        self.assertEqual(str(group), TEST_GROUP_NAME)

    def test_user_group_meta(self):
        """Test UserGroup meta information."""
        
        self.assertEqual(UserGroup._meta.verbose_name, USER_GROUP_VERBOSE_NAME)
        self.assertEqual(UserGroup._meta.verbose_name_plural, USER_GROUP_VERBOSE_NAME_PLURAL)
