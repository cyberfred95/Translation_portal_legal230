"""
Tests for User model functionality.
"""

from django.test import TestCase

from users.models import User, UserGroup
from tests.mock import create_test_user_group


class UserModelTestCase(TestCase):
    """Test case for User model."""

    def test_user_creation(self):
        """Test basic user creation."""
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertIsNotNone(user.uuid)
        self.assertIsNone(user.stripe_customer_id)
        self.assertIsNone(user.group)

    def test_user_with_group(self):
        """Test user creation with a group."""
        
        group = create_test_user_group(name='Test Group')
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        user.group = group
        user.save()
        
        self.assertEqual(user.group, group)
        self.assertEqual(user.group.name, 'Test Group')

    def test_user_uuid_uniqueness(self):
        """Test that each user gets a unique UUID."""
        
        user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        self.assertNotEqual(user1.uuid, user2.uuid)

    def test_user_stripe_customer_id(self):
        """Test Stripe customer ID functionality."""
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Initially should be None
        self.assertIsNone(user.stripe_customer_id)
        
        # Set Stripe customer ID
        user.stripe_customer_id = 'cus_test123456'
        user.save()
        
        # Verify it's saved
        user.refresh_from_db()
        self.assertEqual(user.stripe_customer_id, 'cus_test123456')

    def test_user_language_default(self):
        """Test that user language defaults to settings default."""
        
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        from django.conf import settings
        self.assertEqual(user.language, settings.LANGUAGE_CODE)
