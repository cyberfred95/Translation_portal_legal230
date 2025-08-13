"""
Tests for UserGroup model functionality.
"""

from django.test import TestCase

from users.models import UserGroup
from tests.mock import mock_api_key_generation, mock_api_key_generation_failure, mock_no_settings


class UserGroupAPIKeyTestCase(TestCase):
    """Test case for UserGroup API key auto-generation."""

    @mock_api_key_generation('generated-api-key-12345')
    def test_api_key_auto_generation_success(self, mock_post, mock_get_settings):
        """Test that API key is auto-generated when UserGroup is saved without one."""
        
        # Create UserGroup without api_key
        group = UserGroup(name='Test Group')
        
        # Save should trigger API key generation
        group.save()
        
        # Verify API key was set
        self.assertEqual(group.api_key, 'generated-api-key-12345')
        
        # Verify API call was made correctly
        mock_post.assert_called_once_with(
            'https://console.custom.mt/cabinet_api/create_api_key/',
            json={'label': '1'},  # Now uses the group ID
            headers={
                'token': 'main-api-key-123',
                'Content-Type': 'application/json'
            },
            timeout=30
        )

    @mock_api_key_generation_failure()
    def test_api_key_auto_generation_failure_fallback(self, mock_post, mock_get_settings):
        """Test that UUID fallback is used when API call fails."""
        
        # Create UserGroup without api_key
        group = UserGroup(name='Test Group')
        
        # Save should trigger API key generation with UUID fallback
        group.save()
        
        # Verify API key was set (should be a UUID)
        self.assertIsNotNone(group.api_key)
        self.assertTrue(len(group.api_key) > 0)
        # UUID format check (36 characters with hyphens)
        self.assertTrue(len(group.api_key.replace('-', '')) == 32)

    def test_existing_api_key_not_overwritten(self):
        """Test that existing API key is not overwritten."""
        
        existing_key = 'existing-api-key-123'
        
        # Create UserGroup with existing api_key
        group = UserGroup(name='Test Group', api_key=existing_key)
        group.save()
        
        # Verify API key was not changed
        self.assertEqual(group.api_key, existing_key)

    @mock_no_settings()
    def test_api_key_generation_no_settings(self, mock_get_settings):
        """Test fallback to UUID when main settings are not available."""
        
        # Create UserGroup without api_key
        group = UserGroup(name='Test Group')
        group.save()
        
        # Verify API key was set to UUID fallback
        self.assertIsNotNone(group.api_key)
        self.assertTrue(len(group.api_key) > 0)

    def test_generate_quoting_number(self):
        """Test that quoting number generation works correctly."""
        
        group = UserGroup(name='Test Group', api_key='test-key')
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
        
        group = UserGroup(name='Test Group', api_key='test-key')
        self.assertEqual(str(group), 'Test Group')

    def test_user_group_meta(self):
        """Test UserGroup meta information."""
        
        self.assertEqual(UserGroup._meta.verbose_name, 'Group')
        self.assertEqual(UserGroup._meta.verbose_name_plural, 'Groups')
