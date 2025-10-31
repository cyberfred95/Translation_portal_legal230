"""
Tests for UserGroup model functionality.
"""

from django.test import TestCase

from users.models import UserGroup

# Import des constantes centralisées
from .settings import (
    TEST_GROUP_NAME,
    USER_GROUP_VERBOSE_NAME,
    USER_GROUP_VERBOSE_NAME_PLURAL,
)


class UserGroupTestCase(TestCase):
    """Test case for UserGroup model functionality."""

    def test_generate_quoting_number(self):
        """Test that quoting number generation works correctly."""
        
        group = UserGroup(name=TEST_GROUP_NAME)
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
        
        group = UserGroup(name=TEST_GROUP_NAME)
        self.assertEqual(str(group), TEST_GROUP_NAME)

    def test_user_group_meta(self):
        """Test UserGroup meta information."""
        
        self.assertEqual(UserGroup._meta.verbose_name, USER_GROUP_VERBOSE_NAME)
        self.assertEqual(UserGroup._meta.verbose_name_plural, USER_GROUP_VERBOSE_NAME_PLURAL)
