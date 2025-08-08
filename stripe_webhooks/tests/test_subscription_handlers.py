"""
Unit tests for stripe_webhooks subscription handlers.

This module contains tests for subscription-related webhook handlers including
subscription creation, updates, and cancellations.
"""

from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from stripe_webhooks.tasks_handlers.customer_subscription_handlers import (
    handle_customer_subscription_created,
    handle_customer_subscription_deleted,
    handle_customer_subscription_updated,
)
from stripe_webhooks.tests.settings import (
    ERROR_NOT_FOUND_CUSTOMER_ID,
    ERROR_NOT_FOUND_ID,
    ERROR_NOT_FOUND_STATUS,
    INVALID_SUBSCRIPTION_PAYLOAD,
    STRIPE_STATUS_ACTIVE,
    STRIPE_STATUS_CANCELED,
    TEST_EMAIL_2,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_STRIPE_CUSTOMER_ID_2,
    TEST_STRIPE_PRODUCT_ID_2,
    TEST_STRIPE_SUBSCRIPTION_ID_2,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PAYLOAD,
    TEST_SUBSCRIPTION_PRICE,
    TEST_USERNAME,
    get_test_subscription_payload_with_missing_field,
)
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup

# Test payload for subscription handlers (to avoid conflicts with other tests)
TEST_SUBSCRIPTION_PAYLOAD_HANDLERS = {
    'id': TEST_STRIPE_SUBSCRIPTION_ID_2,
    'customer': TEST_STRIPE_CUSTOMER_ID_2,
    'status': STRIPE_STATUS_ACTIVE,
    'items': {
        'data': [{
            'price': {
                'product': TEST_STRIPE_PRODUCT_ID_2
            },
            'plan': {
                'product': TEST_STRIPE_PRODUCT_ID_2
            },
            'quantity': 1,
            'current_period_start': 1640995200,  # 2022-01-01 00:00:00 UTC
            'current_period_end': 1672531200     # 2023-01-01 00:00:00 UTC
        }]
    }
}


def get_test_subscription_payload_handlers_with_missing_field(field_name):
    """Return a test subscription payload for handlers with a specific field missing."""
    payload = TEST_SUBSCRIPTION_PAYLOAD_HANDLERS.copy()
    if field_name in payload:
        del payload[field_name]
    return payload


class CustomerSubscriptionHandlersTestCase(TestCase):
    """Test case for customer subscription webhook handlers."""

    def setUp(self):
        """Set up test data."""
        # Create test user group
        self.group = UserGroup.objects.create(name=TEST_GROUP_NAME)

        # Create test user
        self.user = User.objects.create_user(
            username=TEST_USERNAME + "_sub",  # Make unique
            email=TEST_EMAIL_2,
            password=TEST_PASSWORD,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID_2
        )
        self.user.group = self.group
        self.user.save()

        # Create test subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME + "_sub",  # Make unique
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=TEST_STRIPE_PRODUCT_ID_2
        )

    def tearDown(self):
        """Clean up test data after each test."""
        # Clean up any UserSubscriptions that might have been created during tests
        UserSubscription.objects.all().delete()
        # The rest will be cleaned up automatically by Django's TestCase

    def test_handle_customer_subscription_created_success(self):
        """Test successful customer subscription creation."""
        response = handle_customer_subscription_created(
            TEST_SUBSCRIPTION_PAYLOAD_HANDLERS)

        # Check response - 201 Created is correct for creation
        self.assertEqual(response.code, 201)

        # Check subscription was created
        subscription = UserSubscription.objects.get(
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID_2
        )
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.subscription, self.subscription_type)
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)

    def test_handle_customer_subscription_created_missing_id(self):
        """Test subscription creation with missing ID."""
        payload = get_test_subscription_payload_handlers_with_missing_field(
            'id')
        response = handle_customer_subscription_created(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_subscription_created_missing_customer_id(self):
        """Test subscription creation with missing customer ID."""
        payload = get_test_subscription_payload_handlers_with_missing_field(
            'customer')
        response = handle_customer_subscription_created(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_subscription_created_missing_status(self):
        """Test subscription creation with missing status."""
        payload = get_test_subscription_payload_handlers_with_missing_field(
            'status')
        response = handle_customer_subscription_created(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_subscription_created_user_not_found(self):
        """Test subscription creation with non-existent user."""
        payload = TEST_SUBSCRIPTION_PAYLOAD.copy()
        payload['customer'] = 'cus_nonexistent'

        response = handle_customer_subscription_created(payload)

        self.assertEqual(response.code, 404)

    def test_handle_customer_subscription_created_subscription_type_not_found(self):
        """Test subscription creation with non-existent subscription type."""
        payload = TEST_SUBSCRIPTION_PAYLOAD.copy()
        payload['items']['data'][0]['price']['product'] = 'prod_nonexistent'
        payload['items']['data'][0]['plan']['product'] = 'prod_nonexistent'

        response = handle_customer_subscription_created(payload)

        self.assertEqual(response.code, 404)

    def test_handle_customer_subscription_updated_success(self):
        """Test successful customer subscription update."""
        # Use a different subscription ID for update test to avoid conflicts
        update_subscription_id = 'sub_update_test123456789'

        # Create existing subscription
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=update_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        # Update payload with new status and different subscription ID
        updated_payload = TEST_SUBSCRIPTION_PAYLOAD_HANDLERS.copy()
        updated_payload['id'] = update_subscription_id
        updated_payload['status'] = STRIPE_STATUS_CANCELED

        response = handle_customer_subscription_updated(updated_payload)

        # Check response
        self.assertEqual(response.code, 200)

        # Check subscription was updated
        subscription.refresh_from_db()
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.TERMINATED)

    def test_handle_customer_subscription_updated_subscription_not_found(self):
        """Test subscription update with non-existent subscription."""
        response = handle_customer_subscription_updated(
            TEST_SUBSCRIPTION_PAYLOAD)

        self.assertEqual(response.code, 404)

    def test_handle_customer_subscription_updated_missing_id(self):
        """Test subscription update with missing ID."""
        payload = get_test_subscription_payload_with_missing_field('id')
        response = handle_customer_subscription_updated(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_subscription_updated_missing_status(self):
        """Test subscription update with missing status."""
        payload = get_test_subscription_payload_with_missing_field('status')
        response = handle_customer_subscription_updated(payload)

        self.assertEqual(response.code, 404)

    def test_handle_customer_subscription_deleted_success(self):
        """Test successful customer subscription deletion."""
        # Use a different subscription ID for deletion test to avoid conflicts
        delete_subscription_id = 'sub_delete_test123456789'

        # Create existing subscription
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=delete_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        # Create payload for deletion with required ended_at field
        deletion_payload = TEST_SUBSCRIPTION_PAYLOAD.copy()
        deletion_payload['id'] = delete_subscription_id
        deletion_payload['ended_at'] = 1672531200  # Unix timestamp

        response = handle_customer_subscription_deleted(deletion_payload)

        # Check response
        self.assertEqual(response.code, 200)

        # Check subscription was canceled
        subscription.refresh_from_db()
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.TERMINATED)

    def test_handle_customer_subscription_deleted_subscription_not_found(self):
        """Test subscription deletion with non-existent subscription."""
        response = handle_customer_subscription_deleted(
            TEST_SUBSCRIPTION_PAYLOAD)

        self.assertEqual(response.code, 404)

    def test_handle_customer_subscription_deleted_missing_id(self):
        """Test subscription deletion with missing ID."""
        payload = get_test_subscription_payload_with_missing_field('id')
        response = handle_customer_subscription_deleted(payload)

        self.assertEqual(response.code, 400)

    def test_handle_customer_subscription_created_with_timestamps(self):
        """Test subscription creation with period timestamps."""
        response = handle_customer_subscription_created(
            TEST_SUBSCRIPTION_PAYLOAD_HANDLERS)

        # Check response - 201 Created is correct for creation
        self.assertEqual(response.code, 201)

        # Check subscription was created with timestamps
        subscription = UserSubscription.objects.get(
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID_2
        )
        self.assertIsNotNone(subscription.start_date)
        self.assertIsNotNone(subscription.end_date)

    def test_handle_customer_subscription_updated_multiple_subscriptions(self):
        """Test subscription update with multiple subscriptions having same stripe ID.

        Note: Current business logic does not support multiple buyers per subscription,
        so this should return an error.
        """
        # Use a different subscription ID for multiple subscriptions test
        multi_subscription_id = 'sub_multi_test123456789'

        # Create multiple subscriptions with same stripe_subscription_id
        subscription1 = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=multi_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        # Create another user and subscription
        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password=TEST_PASSWORD,
            stripe_customer_id='cus_test2'
        )
        subscription2 = UserSubscription.objects.create(
            user=user2,
            subscription=self.subscription_type,
            stripe_subscription_id=multi_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        # Update status
        updated_payload = {
            'id': multi_subscription_id,
            'status': STRIPE_STATUS_CANCELED,
            'items': {
                'data': [{
                    'price': {
                        'product': TEST_STRIPE_PRODUCT_ID_2
                    },
                    'plan': {
                        'product': TEST_STRIPE_PRODUCT_ID_2
                    },
                    'quantity': 1,
                    'current_period_start': 1640995200,
                    'current_period_end': 1672531200
                }]
            }
        }

        response = handle_customer_subscription_updated(updated_payload)

        # Check response - should be error due to multiple buyers
        self.assertEqual(response.code, 500)
        self.assertIn("buyer(s) found", response.message)

        # Verify subscriptions were not updated due to error
        subscription1.refresh_from_db()
        subscription2.refresh_from_db()
        self.assertEqual(subscription1.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)
        self.assertEqual(subscription2.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)
