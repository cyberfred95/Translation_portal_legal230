"""
Unit tests for stripe_webhooks customer tax ID handlers.

This module contains tests for customer tax ID related webhook handlers.
"""

from unittest.mock import MagicMock, patch

from django.test import TestCase

from stripe_webhooks.tasks_handlers.customer_tax_id_handlers import (
    handle_customer_tax_id_created,
)
from stripe_webhooks.tests.settings import (
    ERROR_NOT_FOUND_CUSTOMER_ID,
    ERROR_NOT_FOUND_ID,
    TEST_EMAIL,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_USERNAME,
)
from users.models import User, UserGroup


class CustomerTaxIdHandlersTestCase(TestCase):
    """Test case for customer tax ID webhook handlers."""

    def setUp(self):
        """Set up test data."""
        # Create test user group
        self.group = UserGroup.objects.create(name=TEST_GROUP_NAME)

        # Create test user
        self.user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID
        )
        self.user.group = self.group
        self.user.save()

    def test_handle_customer_tax_id_created_success(self):
        """Test successful customer tax ID creation handling."""
        payload = {
            'customer': TEST_STRIPE_CUSTOMER_ID,
            'id': 'txi_test123',
            'type': 'eu_vat',
            'value': 'DE123456789'
        }

        response = handle_customer_tax_id_created(payload)

        # Should return success response
        self.assertEqual(response.code, 201)

    def test_handle_customer_tax_id_created_missing_customer_id(self):
        """Test tax ID creation with missing customer ID."""
        payload = {
            'id': 'txi_test123',
            'type': 'eu_vat',
            'value': 'DE123456789'
        }

        response = handle_customer_tax_id_created(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_tax_id_created_user_not_found(self):
        """Test tax ID creation with non-existent user."""
        payload = {
            'customer': 'cus_nonexistent',
            'id': 'txi_test123',
            'type': 'eu_vat',
            'value': 'DE123456789'
        }

        response = handle_customer_tax_id_created(payload)

        # Should return success response (creates temporary user group)
        self.assertEqual(response.code, 201)

    @patch('stripe_webhooks.tasks_handlers.customer_tax_id_handlers.get_user_by_stripe_customer_id')
    def test_handle_customer_tax_id_created_exception_handling(self, mock_get_user):
        """Test exception handling in tax ID handler."""
        # Mock exception in get_user function
        mock_error = MagicMock()
        mock_error.code = 500
        mock_error.exception = Exception("Database error")
        mock_get_user.return_value = (mock_error, None)

        payload = {
            'customer': TEST_STRIPE_CUSTOMER_ID,
            'id': 'txi_test123',
            'type': 'eu_vat',
            'value': 'DE123456789'
        }

        response = handle_customer_tax_id_created(payload)

        self.assertEqual(response.code, 500)

    def test_tax_id_created_with_different_types(self):
        """Test tax ID creation with different tax ID types."""
        tax_id_types = [
            {'type': 'eu_vat', 'value': 'DE123456789'},
            {'type': 'us_ein', 'value': '12-3456789'},
            {'type': 'ca_bn', 'value': '123456789RT0001'},
            {'type': 'gb_vat', 'value': 'GB123456789'}
        ]

        for tax_data in tax_id_types:
            payload = {
                'customer': TEST_STRIPE_CUSTOMER_ID,
                'id': f'txi_test_{tax_data["type"]}',
                'type': tax_data['type'],
                'value': tax_data['value']
            }

            # Test creation
            response = handle_customer_tax_id_created(payload)
            self.assertEqual(response.code, 201)
