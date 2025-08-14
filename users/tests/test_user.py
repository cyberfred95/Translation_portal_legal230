"""
Tests for User model functionality.
"""

from django.test import TestCase

from users.models import User, UserGroup
from tests.mock import create_test_user_group

# Import des constantes centralisées
from .settings import (
    TEST_USERNAME,
    TEST_USERNAME_1,
    TEST_USERNAME_2,
    TEST_EMAIL,
    TEST_EMAIL_1,
    TEST_EMAIL_2,
    TEST_PASSWORD,
    TEST_GROUP_NAME,
    TEST_STRIPE_CUSTOMER_ID,
)


class UserModelTestCase(TestCase):
    """Test case for User model."""

    def test_user_creation(self):
        """Test basic user creation."""
        
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        
        self.assertEqual(user.username, TEST_USERNAME)
        self.assertEqual(user.email, TEST_EMAIL)
        self.assertIsNotNone(user.uuid)
        self.assertIsNone(user.stripe_customer_id)
        self.assertIsNone(user.group)

    def test_user_with_group(self):
        """Test user creation with a group."""
        
        group = create_test_user_group(name=TEST_GROUP_NAME)
        
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        user.group = group
        user.save()
        
        self.assertEqual(user.group, group)
        self.assertEqual(user.group.name, TEST_GROUP_NAME)

    def test_user_uuid_uniqueness(self):
        """Test that each user gets a unique UUID."""
        
        user1 = User.objects.create_user(
            username=TEST_USERNAME_1,
            email=TEST_EMAIL_1,
            password=TEST_PASSWORD
        )
        
        user2 = User.objects.create_user(
            username=TEST_USERNAME_2,
            email=TEST_EMAIL_2,
            password=TEST_PASSWORD
        )
        
        self.assertNotEqual(user1.uuid, user2.uuid)

    def test_user_stripe_customer_id(self):
        """Test Stripe customer ID functionality."""
        
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        
        # Initially should be None
        self.assertIsNone(user.stripe_customer_id)
        
        # Set Stripe customer ID
        user.stripe_customer_id = TEST_STRIPE_CUSTOMER_ID
        user.save()
        
        # Verify it's saved
        user.refresh_from_db()
        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)

    def test_user_language_default(self):
        """Test that user language defaults to settings default."""
        
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        
        from django.conf import settings
        self.assertEqual(user.language, settings.LANGUAGE_CODE)
