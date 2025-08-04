"""
Unit tests for stripe_webhooks helper utilities.

This module contains tests for helper functions including converters
and Stripe session management.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase

from stripe_webhooks.tasks_handlers.helper.convertor import (
    dict_to_pair_list,
    group_name_to_user_name,
    int_to_DateTimeField,
    string_to_UserSubscriptionChoices,
    user_name_to_group_name,
)
from stripe_webhooks.tasks_handlers.helper.stripe_session import (
    get_stripe_customer_session_url,
)
from stripe_webhooks.tests.settings import (
    CONVERTER_EXPECTED_PAIRS,
    CONVERTER_TEST_DICT,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_CANCELED,
    SUBSCRIPTION_STATUS_UNKNOWN,
    TEST_FIRST_NAME,
    TEST_FULL_NAME,
    TEST_GROUP_NAME,
    TEST_LAST_NAME,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_STRIPE_SESSION_URL,
    TEST_TIMESTAMP,
    TEST_TIMESTAMP_2,
    USER_SUBSCRIPTION_CHOICES,
)
from subscriptions.models import UserSubscription
from users.models import User, UserGroup


class ConvertorTestCase(TestCase):
    """Test case for convertor utility functions."""

    def test_string_to_UserSubscriptionChoices_active(self):
        """Test conversion of 'active' status."""
        result = string_to_UserSubscriptionChoices('active')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.ACTIVE)

    def test_string_to_UserSubscriptionChoices_canceled(self):
        """Test conversion of 'canceled' status."""
        result = string_to_UserSubscriptionChoices('canceled')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.TERMINATED)

    def test_string_to_UserSubscriptionChoices_with_hyphens(self):
        """Test conversion of status with hyphens."""
        result = string_to_UserSubscriptionChoices('past-due')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.PAST_DUE)

    def test_string_to_UserSubscriptionChoices_case_insensitive(self):
        """Test case insensitive conversion."""
        result = string_to_UserSubscriptionChoices('ACTIVE')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.ACTIVE)

        result = string_to_UserSubscriptionChoices('Active')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.ACTIVE)

    def test_string_to_UserSubscriptionChoices_with_whitespace(self):
        """Test conversion with leading/trailing whitespace."""
        result = string_to_UserSubscriptionChoices('  active  ')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.ACTIVE)

    def test_string_to_UserSubscriptionChoices_unknown(self):
        """Test conversion of unknown status."""
        result = string_to_UserSubscriptionChoices('unknown_status')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.UNKNOWN)

    def test_string_to_UserSubscriptionChoices_empty_string(self):
        """Test conversion of empty string."""
        result = string_to_UserSubscriptionChoices('')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.UNKNOWN)

    def test_int_to_DateTimeField_valid_timestamp(self):
        """Test conversion of valid timestamp."""
        result = int_to_DateTimeField(TEST_TIMESTAMP)

        self.assertIsInstance(result, datetime)
        self.assertTrue(result.tzinfo is not None)

    def test_int_to_DateTimeField_none(self):
        """Test conversion of None timestamp."""
        result = int_to_DateTimeField(None)
        self.assertIsNone(result)

    def test_int_to_DateTimeField_zero(self):
        """Test conversion of zero timestamp."""
        result = int_to_DateTimeField(0)

        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 1970)
        self.assertEqual(result.month, 1)
        self.assertEqual(result.day, 1)

    def test_dict_to_pair_list_success(self):
        """Test successful conversion of dictionary to pair list."""
        result = dict_to_pair_list(CONVERTER_TEST_DICT)

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), len(CONVERTER_TEST_DICT))

        # Check if all expected pairs are present
        for expected_pair in CONVERTER_EXPECTED_PAIRS:
            self.assertIn(expected_pair, result)

    def test_dict_to_pair_list_empty_dict(self):
        """Test conversion of empty dictionary."""
        result = dict_to_pair_list({})

        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_dict_to_pair_list_single_item(self):
        """Test conversion of dictionary with single item."""
        test_dict = {'single_key': 'single_value'}
        result = dict_to_pair_list(test_dict)

        expected = [{'key': 'single_key', 'value': 'single_value'}]
        self.assertEqual(result, expected)

    def test_user_name_to_group_name_with_last_name(self):
        """Test conversion of user name to group name with both first and last name."""
        # Create a mock user object
        user = MagicMock()
        user.first_name = TEST_FIRST_NAME
        user.last_name = TEST_LAST_NAME

        result = user_name_to_group_name(user)

        expected = f"{TEST_FIRST_NAME} {TEST_LAST_NAME}".upper()
        self.assertEqual(result, expected)

    def test_user_name_to_group_name_without_last_name(self):
        """Test conversion of user name to group name with only first name."""
        # Create a mock user object
        user = MagicMock()
        user.first_name = TEST_FIRST_NAME
        user.last_name = ""

        result = user_name_to_group_name(user)

        self.assertEqual(result, TEST_FIRST_NAME.upper())

    def test_user_name_to_group_name_no_last_name_attribute(self):
        """Test conversion when last_name is None."""
        # Create a mock user object
        user = MagicMock()
        user.first_name = TEST_FIRST_NAME
        user.last_name = None

        result = user_name_to_group_name(user)

        self.assertEqual(result, TEST_FIRST_NAME.upper())

    def test_group_name_to_user_name_with_space(self):
        """Test conversion of group name to user name with space."""
        result = group_name_to_user_name(TEST_FULL_NAME)

        expected = (TEST_FIRST_NAME, TEST_LAST_NAME)
        self.assertEqual(result, expected)

    def test_group_name_to_user_name_without_space(self):
        """Test conversion of group name to user name without space."""
        result = group_name_to_user_name(TEST_FIRST_NAME)

        expected = (TEST_FIRST_NAME, "")
        self.assertEqual(result, expected)

    def test_group_name_to_user_name_empty_string(self):
        """Test conversion of empty group name."""
        result = group_name_to_user_name("")

        expected = ("", "")
        self.assertEqual(result, expected)

    def test_group_name_to_user_name_none(self):
        """Test conversion of None group name."""
        result = group_name_to_user_name(None)

        expected = (None, "")
        self.assertEqual(result, expected)

    def test_group_name_to_user_name_multiple_spaces(self):
        """Test conversion with multiple spaces (should split on first space only)."""
        test_name = "John Doe Smith"
        result = group_name_to_user_name(test_name)

        expected = ("John", "Doe Smith")
        self.assertEqual(result, expected)


class StripeSessionTestCase(TestCase):
    """Test case for Stripe session utility functions."""

    @patch('stripe_webhooks.tasks_handlers.helper.stripe_session.stripe.billing_portal.Session.create')
    def test_get_stripe_customer_session_url_success(self, mock_create):
        """Test successful Stripe customer session URL generation."""
        # Mock Stripe response
        mock_session = MagicMock()
        mock_session.url = TEST_STRIPE_SESSION_URL
        mock_create.return_value = mock_session

        result = get_stripe_customer_session_url(TEST_STRIPE_CUSTOMER_ID)

        self.assertEqual(result[1], TEST_STRIPE_SESSION_URL)
        mock_create.assert_called_once()

    @patch('stripe_webhooks.tasks_handlers.helper.stripe_session.stripe.billing_portal.Session.create')
    def test_get_stripe_customer_session_url_exception(self, mock_create):
        """Test Stripe customer session URL generation with exception."""
        # Mock Stripe exception
        mock_create.side_effect = Exception("Stripe API error")

        result = get_stripe_customer_session_url(TEST_STRIPE_CUSTOMER_ID)

        self.assertIsNotNone(result[0])
        mock_create.assert_called_once()

    @patch('stripe_webhooks.tasks_handlers.helper.stripe_session.stripe.billing_portal.Session.create')
    def test_get_stripe_customer_session_url_empty_customer_id(self, mock_create):
        """Test Stripe customer session URL generation with empty customer ID."""
        result = get_stripe_customer_session_url("")

        # Should not call Stripe API with empty customer ID
        mock_create.assert_not_called()
        self.assertIsNotNone(result[0])

    @patch('stripe_webhooks.tasks_handlers.helper.stripe_session.stripe.billing_portal.Session.create')
    def test_get_stripe_customer_session_url_none_customer_id(self, mock_create):
        """Test Stripe customer session URL generation with None customer ID."""
        result = get_stripe_customer_session_url(None)

        # Should not call Stripe API with None customer ID
        mock_create.assert_not_called()
        self.assertIsNotNone(result[0])
