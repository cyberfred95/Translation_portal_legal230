"""
Unit tests for stripe_webhooks customer handlers.

This module contains tests for customer-related webhook handlers including
customer creation, updates, and deletions.
"""

from unittest.mock import MagicMock, patch

from django.db import transaction
from django.test import TestCase

from emails.models import EmailSettings, EmailType
from stripe_webhooks.tasks_handlers.customer_handlers import (
    handle_customer_created,
    handle_customer_updated,
)
from stripe_webhooks.tests.settings import (
    ENGLISH_LANG_CODE,
    ERROR_NOT_FOUND_EMAIL,
    ERROR_NOT_FOUND_ID,
    ERROR_NOT_FOUND_LANGUAGE,
    ERROR_NOT_FOUND_NAME,
    INVALID_CUSTOMER_PAYLOAD,
    TEST_CUSTOMER_PAYLOAD,
    TEST_CUSTOMER_PAYLOAD_NO_EMAIL,
    TEST_CUSTOMER_PAYLOAD_NO_LANGUAGE,
    TEST_CUSTOMER_PAYLOAD_NO_NAME,
    TEST_EMAIL,
    TEST_FULL_NAME,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_USERNAME,
)
from users.models import User, UserGroup


class CustomerHandlersTestCase(TestCase):
    """Test case for customer webhook handlers."""

    def setUp(self):
        """Set up test data."""
        # Create email settings
        self.email_settings, _ = EmailSettings.objects.get_or_create(
            email_type=EmailType.USER_CREATED.value,
            language='en',
            defaults={
                'template_id': 1,
                'subject': 'Welcome'
            }
        )

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    def test_handle_customer_created_success_new_group(
        self, mock_session_url, mock_send_email
    ):
        """Test successful customer creation with new group."""
        mock_session_url.return_value = "https://billing.stripe.com/session/test"
        mock_send_email.return_value = None

        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD)

        # Check response
        self.assertEqual(response.code, 201)  # Created

        # Check user was created
        user = User.objects.get(stripe_customer_id=TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.email, TEST_EMAIL)
        self.assertEqual(user.language, ENGLISH_LANG_CODE)

        # Check group was created with customer ID as name (actual behavior)
        group = UserGroup.objects.get(name=TEST_STRIPE_CUSTOMER_ID.upper())
        self.assertEqual(user.group, group)

        # Check email was sent
        mock_send_email.assert_called_once()

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    def test_handle_customer_created_success_existing_group(
        self, mock_session_url, mock_send_email
    ):
        """Test successful customer creation with existing group."""
        # Create existing group
        group_name = TEST_FULL_NAME.upper()
        existing_group = UserGroup.objects.create(name=group_name)

        mock_session_url.return_value = "https://billing.stripe.com/session/test"
        mock_send_email.return_value = None

        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD)

        # Check response
        self.assertEqual(response.code, 201)  # Created

        # Check user was created with existing group
        user = User.objects.get(stripe_customer_id=TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.group, existing_group)

        # Check only one group exists
        self.assertEqual(UserGroup.objects.filter(name=group_name).count(), 1)

    def test_handle_customer_created_missing_id(self):
        """Test customer creation with missing ID."""
        response = handle_customer_created(INVALID_CUSTOMER_PAYLOAD)

        self.assertEqual(response.code, 400)
        self.assertIn("Id in payload not found", response.message)

    def test_handle_customer_created_missing_name(self):
        """Test customer creation with missing name."""
        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD_NO_NAME)

        self.assertEqual(response.code, 400)
        self.assertIn("Name in payload not found", response.message)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    def test_handle_customer_created_missing_email(
        self, mock_session_url, mock_send_email
    ):
        """Test customer creation with missing email should succeed with empty email."""
        mock_session_url.return_value = "https://billing.stripe.com/session/test"
        mock_send_email.return_value = None

        # Use unique ID to avoid conflicts with other tests
        import time
        timestamp = str(int(time.time()))
        unique_customer_id = f'cus_no_email_test_{timestamp}'

        # Create payload without email but with unique ID
        payload_no_email = {
            'id': unique_customer_id,
            'name': f'No Email Test User {timestamp}',
            'preferred_locales': ['en']
        }

        response = handle_customer_created(payload_no_email)

        # Email is optional, so missing email should not cause an error
        self.assertEqual(response.code, 201)

        # Verify user was created with empty email
        from users.models import User
        user = User.objects.get(stripe_customer_id=unique_customer_id)
        self.assertEqual(user.email, "")  # Should be empty string

    def test_handle_customer_created_missing_language(self):
        """Test customer creation with missing language."""
        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD_NO_LANGUAGE)

        self.assertEqual(response.code, 400)
        self.assertIn("Language in payload not found", response.message)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.create_user')
    def test_handle_customer_created_user_creation_error(self, mock_create_user):
        """Test customer creation with user creation error."""
        # Mock user creation error
        mock_error = MagicMock()
        mock_error.code = 500
        mock_create_user.return_value = (mock_error, None, None)

        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD)

        self.assertEqual(response.code, 500)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.create_userGroup_if_not_exists')
    def test_handle_customer_created_group_creation_error(self, mock_create_group):
        """Test customer creation with group creation error."""
        # Mock group creation error
        mock_error = MagicMock()
        mock_error.code = 500
        mock_error.exception = Exception("Database error")
        mock_create_group.return_value = (mock_error, None, None)

        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD)

        self.assertEqual(response.code, 500)

    def test_handle_customer_updated_success(self):
        """Test successful customer update."""
        # Create existing user
        group = UserGroup.objects.create(name=TEST_GROUP_NAME)
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID
        )
        user.group = group
        user.save()

        # Update payload with new email
        updated_payload = TEST_CUSTOMER_PAYLOAD.copy()
        updated_payload['email'] = 'newemail@example.com'

        response = handle_customer_updated(updated_payload)

        # Check response
        self.assertEqual(response.code, 200)

        # Check user was updated
        user.refresh_from_db()
        self.assertEqual(user.email, 'newemail@example.com')

    def test_handle_customer_updated_user_not_found(self):
        """Test customer update with non-existent user."""
        response = handle_customer_updated(TEST_CUSTOMER_PAYLOAD)

        self.assertEqual(response.code, 404)

    def test_handle_customer_updated_missing_id(self):
        """Test customer update with missing ID."""
        response = handle_customer_updated(INVALID_CUSTOMER_PAYLOAD)

        self.assertEqual(response.code, 400)
        self.assertIn("Id in payload not found", response.message)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.transaction.atomic')
    def test_handle_customer_created_transaction_rollback(self, mock_atomic):
        """Test transaction rollback on error during customer creation."""
        # Mock transaction to raise exception
        mock_atomic.side_effect = Exception("Transaction error")

        response = handle_customer_created(TEST_CUSTOMER_PAYLOAD)

        # Should handle the exception gracefully
        self.assertNotEqual(response.code, 200)

        # Check no user was created
        self.assertEqual(
            User.objects.filter(
                stripe_customer_id=TEST_STRIPE_CUSTOMER_ID
            ).count(),
            0
        )
