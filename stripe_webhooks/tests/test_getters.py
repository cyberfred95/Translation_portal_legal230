"""
Unit tests for stripe_webhooks getter utilities.

This module contains tests for getter functions used to retrieve data from
the database and payload parsing functions.
"""

from unittest.mock import patch

from django.test import TestCase

from stripe_webhooks.tasks_handlers.getter.get_data import (
    get_subscriptionType_by_stripe_product_id,
    get_user_by_stripe_customer_id,
    get_user_count_from_userGroup_by_group_id,
    get_userGroup_by_group_name,
    get_userGroup_by_id,
    get_userSubscriptions_list_by_stripe_subscription_id,
)
from stripe_webhooks.tasks_handlers.getter.get_payload import (
    get_payload_customer_id,
    get_payload_email,
    get_payload_id,
    get_payload_item_data,
    get_payload_language,
    get_payload_name,
    get_payload_status,
    get_payload_cancel_at,
    get_payload_ended_at,
    get_item_data_current_period_end,
    get_item_data_current_period_start,
    get_item_data_product_id,
    get_item_data_quantity,
)
from stripe_webhooks.tests.settings import (
    ENGLISH_LANG_CODE,
    ERROR_NOT_FOUND_CUSTOMER_ID,
    ERROR_NOT_FOUND_EMAIL,
    ERROR_NOT_FOUND_ID,
    ERROR_NOT_FOUND_LANGUAGE,
    ERROR_NOT_FOUND_NAME,
    ERROR_NOT_FOUND_STATUS,
    ERROR_NOT_FOUND_SUBSCRIPTION_TYPE,
    ERROR_NOT_FOUND_USER,
    ERROR_NOT_FOUND_USER_GROUP,
    ERROR_NOT_FOUND_USER_SUBSCRIPTION,
    FRENCH_LANG_CODE,
    INVALID_CUSTOMER_PAYLOAD,
    INVALID_STRIPE_CUSTOMER_ID,
    INVALID_STRIPE_PRODUCT_ID,
    INVALID_STRIPE_SUBSCRIPTION_ID,
    STRIPE_STATUS_ACTIVE,
    TEST_CUSTOMER_PAYLOAD,
    TEST_CUSTOMER_PAYLOAD_NO_EMAIL,
    TEST_CUSTOMER_PAYLOAD_NO_LANGUAGE,
    TEST_CUSTOMER_PAYLOAD_NO_NAME,
    TEST_EMAIL,
    TEST_FULL_NAME,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_STRIPE_PRODUCT_ID,
    TEST_STRIPE_SUBSCRIPTION_ID,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PAYLOAD,
    TEST_SUBSCRIPTION_PRICE,
    TEST_TIMESTAMP,
    TEST_TIMESTAMP_2,
    TEST_USERNAME,
)
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup


class GetDataTestCase(TestCase):
    """Test case for get_data functions."""

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

        # Create test subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=TEST_STRIPE_PRODUCT_ID
        )

        # Create test user subscription
        from datetime import datetime, timezone

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc)
        )

    def test_get_user_by_stripe_customer_id_success(self):
        """Test successful user retrieval by stripe customer ID."""
        error, user = get_user_by_stripe_customer_id(TEST_STRIPE_CUSTOMER_ID)

        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.username, TEST_USERNAME)

    def test_get_user_by_stripe_customer_id_not_found(self):
        """Test user retrieval with non-existent stripe customer ID."""
        error, user = get_user_by_stripe_customer_id(
            INVALID_STRIPE_CUSTOMER_ID)

        self.assertIsNotNone(error)
        self.assertIsNone(user)
        self.assertEqual(error.code, 404)  # CODE_NOT_FOUND
        self.assertIn("not found", error.message)

    def test_get_subscriptionType_by_stripe_product_id_success(self):
        """Test successful subscription type retrieval by stripe product ID."""
        error, subscription_type = get_subscriptionType_by_stripe_product_id(
            TEST_STRIPE_PRODUCT_ID)

        self.assertIsNone(error)
        self.assertIsNotNone(subscription_type)
        self.assertEqual(subscription_type.stripe_product_id,
                         TEST_STRIPE_PRODUCT_ID)
        self.assertEqual(subscription_type.name, TEST_SUBSCRIPTION_NAME)

    def test_get_subscriptionType_by_stripe_product_id_not_found(self):
        """Test subscription type retrieval with non-existent stripe product ID."""
        error, subscription_type = get_subscriptionType_by_stripe_product_id(
            INVALID_STRIPE_PRODUCT_ID)

        self.assertIsNotNone(error)
        self.assertIsNone(subscription_type)
        self.assertEqual(error.code, 404)  # CODE_NOT_FOUND
        self.assertIn("not found", error.message)

    def test_get_userSubscriptions_list_by_stripe_subscription_id_success(self):
        """Test successful user subscriptions retrieval by stripe subscription ID."""
        error, subscriptions = get_userSubscriptions_list_by_stripe_subscription_id(
            TEST_STRIPE_SUBSCRIPTION_ID)

        self.assertIsNone(error)
        self.assertIsNotNone(subscriptions)
        self.assertIsInstance(subscriptions, list)
        self.assertEqual(len(subscriptions), 1)
        self.assertEqual(
            subscriptions[0].stripe_subscription_id, TEST_STRIPE_SUBSCRIPTION_ID)

    def test_get_userSubscriptions_list_by_stripe_subscription_id_not_found(self):
        """Test user subscriptions retrieval with non-existent stripe subscription ID."""
        error, subscriptions = get_userSubscriptions_list_by_stripe_subscription_id(
            INVALID_STRIPE_SUBSCRIPTION_ID)

        self.assertIsNotNone(error)
        self.assertIsNone(subscriptions)
        self.assertEqual(error.code, 404)  # not found code

    def test_get_userGroup_by_group_name_success(self):
        """Test successful user group retrieval by group name."""
        error, group = get_userGroup_by_group_name(TEST_GROUP_NAME)

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(group.name, TEST_GROUP_NAME)

    def test_get_userGroup_by_group_name_not_found(self):
        """Test user group retrieval with non-existent group name."""
        error, group = get_userGroup_by_group_name("NON_EXISTENT_GROUP")

        self.assertIsNotNone(error)
        self.assertIsNone(group)
        self.assertEqual(error.code, 404)  # not found code

    def test_get_user_count_from_userGroup_by_group_id_success(self):
        """Test successful user count retrieval from user group."""
        error, count = get_user_count_from_userGroup_by_group_id(self.group.id)

        self.assertIsNone(error)
        self.assertIsNotNone(count)
        self.assertEqual(count, 1)

    def test_get_userGroup_by_id_success(self):
        """Test successful user group retrieval by ID."""
        error, group = get_userGroup_by_id(self.group.id)

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(group.id, self.group.id)
        self.assertEqual(group.name, TEST_GROUP_NAME)

    @patch('stripe_webhooks.tasks_handlers.getter.get_data.UserGroup.objects.get')
    def test_get_data_functions_exception_handling(self, mock_get):
        """Test exception handling in get_data functions."""
        # Configure mock to raise an exception
        mock_get.side_effect = Exception("Database error")

        # Test exception handling in get_userGroup_by_id
        error, group = get_userGroup_by_id(999)

        self.assertIsNotNone(error)
        self.assertIsNone(group)
        self.assertEqual(error.code, 500)  # exception code


class GetPayloadTestCase(TestCase):
    """Test case for get_payload functions."""

    def test_get_payload_id_success(self):
        """Test successful ID extraction from payload."""
        error, payload_id = get_payload_id(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(payload_id, TEST_STRIPE_CUSTOMER_ID)

    def test_get_payload_id_missing(self):
        """Test ID extraction with missing ID field."""
        error, payload_id = get_payload_id(INVALID_CUSTOMER_PAYLOAD)

        self.assertIsNotNone(error)
        self.assertIsNone(payload_id)
        self.assertEqual(error.code, 400)  # bad request code

    def test_get_payload_name_success(self):
        """Test successful name extraction from payload."""
        error, name = get_payload_name(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(name, TEST_FULL_NAME)

    def test_get_payload_name_missing(self):
        """Test name extraction with missing name field."""
        error, name = get_payload_name(TEST_CUSTOMER_PAYLOAD_NO_NAME)

        self.assertIsNotNone(error)
        self.assertIsNone(name)
        self.assertEqual(error.code, 400)  # bad request code

    def test_get_payload_name_empty_string(self):
        """Test name extraction with empty name field."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['name'] = ""

        error, name = get_payload_name(payload)

        self.assertIsNone(error)
        self.assertEqual(name, "")

    def test_get_payload_name_whitespace_normalization(self):
        """Test name extraction with multiple whitespaces."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['name'] = "  John    Doe  "

        error, name = get_payload_name(payload)

        self.assertIsNone(error)
        self.assertEqual(name, "John Doe")

    def test_get_payload_email_success(self):
        """Test successful email extraction from payload."""
        error, email = get_payload_email(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(email, TEST_EMAIL)

    def test_get_payload_email_missing(self):
        """Test email extraction with missing email field."""
        error, email = get_payload_email(TEST_CUSTOMER_PAYLOAD_NO_EMAIL)

        self.assertIsNone(error)
        # get_payload_email returns empty string for missing email
        self.assertEqual(email, "")

    def test_get_payload_email_empty(self):
        """Test email extraction with empty email field."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['email'] = ""

        error, email = get_payload_email(payload)

        self.assertIsNone(error)
        self.assertEqual(email, "")

    def test_get_payload_language_success(self):
        """Test successful language extraction from payload."""
        error, language = get_payload_language(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(language, ENGLISH_LANG_CODE)

    def test_get_payload_language_missing(self):
        """Test language extraction with missing preferred_locales field."""
        error, language = get_payload_language(
            TEST_CUSTOMER_PAYLOAD_NO_LANGUAGE)

        self.assertIsNotNone(error)
        self.assertIsNone(language)
        self.assertEqual(error.code, 400)  # bad request code

    def test_get_payload_language_multiple_locales(self):
        """Test language extraction with multiple preferred locales."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['preferred_locales'] = [FRENCH_LANG_CODE, ENGLISH_LANG_CODE]

        error, language = get_payload_language(payload)

        self.assertIsNone(error)
        self.assertEqual(language, FRENCH_LANG_CODE)

    def test_get_payload_language_empty_list(self):
        """Test language extraction with empty preferred_locales list."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['preferred_locales'] = []

        error, language = get_payload_language(payload)

        self.assertIsNone(error)
        # Should return default language code when no valid locales found
        self.assertIsNotNone(language)

    def test_get_payload_language_invalid_type(self):
        """Test language extraction with invalid preferred_locales type."""
        payload = TEST_CUSTOMER_PAYLOAD.copy()
        payload['preferred_locales'] = "en"  # Should be a list

        error, language = get_payload_language(payload)

        self.assertIsNotNone(error)
        self.assertIsNone(language)
        self.assertEqual(error.code, 400)  # bad request code

    def test_get_payload_status_success(self):
        """Test successful status extraction from payload."""
        error, status = get_payload_status(TEST_SUBSCRIPTION_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(status, STRIPE_STATUS_ACTIVE)

    def test_get_payload_status_missing(self):
        """Test status extraction with missing status field."""
        payload = {'id': 'test'}
        error, status = get_payload_status(payload)

        # get_payload_status should return an error when status is missing
        self.assertIsNotNone(error)
        self.assertEqual(error.code, 400)
        self.assertIsNone(status)

    def test_get_payload_customer_id_success(self):
        """Test successful customer ID extraction from payload."""
        error, customer_id = get_payload_customer_id(TEST_SUBSCRIPTION_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(customer_id, TEST_STRIPE_CUSTOMER_ID)

    def test_get_payload_customer_id_missing(self):
        """Test customer ID extraction with missing customer field."""
        payload = {'id': 'test'}
        error, customer_id = get_payload_customer_id(payload)

        self.assertIsNotNone(error)
        self.assertIsNone(customer_id)
        self.assertEqual(error.code, 400)  # bad request code
