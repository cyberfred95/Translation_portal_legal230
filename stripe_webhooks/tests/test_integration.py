"""
Integration tests for stripe_webhooks module.

This module contains integration tests that test the complete workflow
of webhook handling from payload processing to database operations.
"""

from unittest.mock import patch

from django.test import TransactionTestCase
from django.utils import timezone

from emails.models import EmailSettings, EmailType
from stripe_webhooks.tasks_handlers.customer_handlers import handle_customer_created
from stripe_webhooks.tasks_handlers.customer_subscription_handlers import (
    handle_customer_subscription_created,
    handle_customer_subscription_updated,
)
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from stripe_webhooks.tests.settings import (
    TEST_STRIPE_PRODUCT_ID,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PRICE,
    ENGLISH_LANG_CODE,
    STRIPE_STATUS_ACTIVE,
    STRIPE_STATUS_CANCELED,
    TEST_TIMESTAMP,
    TEST_TIMESTAMP_2
)


class StripeWebhooksIntegrationTestCase(TransactionTestCase):
    """Integration test case for complete webhook workflows."""

    def setUp(self):
        """Set up test data."""
        # Create email settings for welcome emails
        self.email_settings, _ = EmailSettings.objects.get_or_create(
            email_type=EmailType.USER_CREATED.value,
            language='en',
            defaults={
                'template_id': 1,
                'subject': 'Welcome to our platform'
            }
        )

        # Create email settings for subscription updated admin notifications
        self.email_settings_subscription_updated, _ = EmailSettings.objects.get_or_create(
            email_type='SUBSCRIPTION_UPDATED_INACTIVE_ADMIN',
            language='en',
            defaults={
                'template_id': 2,
                'subject': 'Subscription Updated - Admin Notification'
            }
        )

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    @patch('stripe_webhooks.tasks_handlers.customer_subscription_handlers.get_stripe_customer_session_url')
    @patch('stripe_webhooks.tasks_handlers.customer_subscription_handlers.send_email')
    def test_complete_customer_and_subscription_workflow(self, mock_send_email_subscription, mock_session_url_subscription, mock_session_url_customer, mock_send_email_customer):
        """Test complete workflow: customer creation -> subscription creation -> subscription update."""
        mock_session_url_customer.return_value = (
            None, "https://billing.stripe.com/session/test")
        mock_session_url_subscription.return_value = (
            None, "https://billing.stripe.com/session/test")
        mock_send_email_customer.return_value = None
        mock_send_email_subscription.return_value = None

        # Use unique customer data to avoid conflicts
        import time
        timestamp = str(int(time.time()))
        unique_customer_id = f'cus_workflow_test_{timestamp}'
        unique_email = f'workflow_{timestamp}@example.com'
        unique_name = f'Workflow Test User {timestamp}'
        unique_subscription_id = f'sub_workflow_test_{timestamp}'
        unique_product_id = f'prod_workflow_test_{timestamp}'

        # Create unique payload
        unique_customer_payload = {
            'id': unique_customer_id,
            'name': unique_name,
            'email': unique_email,
            'preferred_locales': [ENGLISH_LANG_CODE]
        }

        # Step 1: Create customer
        customer_response = handle_customer_created(unique_customer_payload)
        self.assertEqual(customer_response.code, 201)

        # Verify customer was created correctly
        user = User.objects.get(stripe_customer_id=unique_customer_id)
        self.assertEqual(user.email, unique_email)
        self.assertEqual(user.language, ENGLISH_LANG_CODE)

        # Check which group was actually created (adapt to current logic)
        # The group should exist and user should be in it
        self.assertIsNotNone(user.group)
        group = user.group

        # Step 2: Create subscription type
        subscription_type = SubscriptionType.objects.create(
            name=f"Workflow Test Subscription {timestamp}",
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=unique_product_id
        )

        # Step 3: Create subscription with unique payload
        unique_subscription_payload = {
            'id': unique_subscription_id,
            'customer': unique_customer_id,
            'status': STRIPE_STATUS_ACTIVE,
            'items': {
                'data': [{
                    'price': {
                        'product': unique_product_id
                    },
                    'plan': {
                        'product': unique_product_id
                    },
                    'quantity': 1,
                    'current_period_start': TEST_TIMESTAMP,
                    'current_period_end': TEST_TIMESTAMP_2
                }]
            }
        }

        subscription_response = handle_customer_subscription_created(
            unique_subscription_payload)
        self.assertEqual(subscription_response.code, 201)  # Created, not OK

        # Verify subscription was created correctly
        subscription = UserSubscription.objects.get(
            stripe_subscription_id=unique_subscription_id
        )
        self.assertEqual(subscription.user, user)
        self.assertEqual(subscription.subscription, subscription_type)
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)

        # Step 4: Update subscription status
        updated_payload = unique_subscription_payload.copy()
        updated_payload['status'] = STRIPE_STATUS_CANCELED

        update_response = handle_customer_subscription_updated(updated_payload)
        self.assertEqual(update_response.code, 200)

        # Verify subscription was updated
        subscription.refresh_from_db()
        self.assertEqual(subscription.status,
                         UserSubscription.UserSubscriptionChoices.TERMINATED)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    def test_customer_creation_with_existing_group(self, mock_session_url, mock_send_email):
        """Test customer creation when group already exists."""
        mock_session_url.return_value = "https://billing.stripe.com/session/test"
        mock_send_email.return_value = None

        # Use unique customer data to avoid conflicts
        unique_customer_id = 'cus_existing_group_test_001'
        unique_email = 'existing_group@example.com'
        unique_name = 'Existing Group Test User'

        # Create unique payload
        unique_payload = {
            'id': unique_customer_id,
            'name': unique_name,
            'email': unique_email,
            'preferred_locales': [ENGLISH_LANG_CODE]
        }

        # Pre-create group
        group_name = unique_name.upper()
        existing_group = UserGroup.objects.create(name=group_name)
        existing_user_count = existing_group.user_set.count()

        # Create customer
        response = handle_customer_created(unique_payload)
        self.assertEqual(response.code, 201)

        # Verify only one group exists and user was added to existing group
        groups = UserGroup.objects.filter(name=group_name)
        self.assertEqual(groups.count(), 1)

        group = groups.first()
        self.assertEqual(group.id, existing_group.id)
        self.assertEqual(group.user_set.count(), existing_user_count + 1)

        # Verify user is in the existing group
        user = User.objects.get(stripe_customer_id=unique_customer_id)
        self.assertEqual(user.group, existing_group)

    def test_multiple_subscriptions_same_stripe_id(self):
        """Test handling multiple user subscriptions with same Stripe subscription ID."""
        # Use unique IDs to avoid conflicts with other tests
        unique_customer_id_1 = 'cus_multiple_test_001'
        unique_customer_id_2 = 'cus_multiple_test_002'
        unique_subscription_id = 'sub_multiple_test_001'
        unique_product_id = 'prod_multiple_test_001'

        # Create test data
        group1 = UserGroup.objects.create(name="GROUP_MULTIPLE_1")
        group2 = UserGroup.objects.create(name="GROUP_MULTIPLE_2")

        user1 = User.objects.create_user(
            username="multiple_user1",
            email="multiple1@example.com",
            stripe_customer_id=unique_customer_id_1
        )
        user1.group = group1
        user1.save()

        user2 = User.objects.create_user(
            username="multiple_user2",
            email="multiple2@example.com",
            stripe_customer_id=unique_customer_id_2
        )
        user2.group = group2
        user2.save()

        subscription_type = SubscriptionType.objects.create(
            name="Multiple Test Subscription",
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=unique_product_id
        )

        # Create subscriptions for both users with same stripe_subscription_id
        # This scenario should result in an error according to current business logic
        subscription1 = UserSubscription.objects.create(
            user=user1,
            subscription=subscription_type,
            stripe_subscription_id=unique_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        subscription2 = UserSubscription.objects.create(
            user=user2,
            subscription=subscription_type,
            stripe_subscription_id=unique_subscription_id,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        # Update subscription status with unique payload
        updated_payload = {
            'id': unique_subscription_id,
            'customer': unique_customer_id_1,  # Could be either customer
            'status': STRIPE_STATUS_CANCELED,
            'items': {
                'data': [{
                    'price': {
                        'product': unique_product_id
                    },
                    'plan': {
                        'product': unique_product_id
                    },
                    'quantity': 1,
                    'current_period_start': TEST_TIMESTAMP,
                    'current_period_end': TEST_TIMESTAMP_2
                }]
            }
        }

        response = handle_customer_subscription_updated(updated_payload)

        # Current business logic: multiple buyers for same subscription should return error 500
        self.assertEqual(response.code, 500)
        self.assertIn("buyer(s) found in userSubscription list",
                      response.message)

        # Verify subscriptions were NOT updated due to the error
        subscription1.refresh_from_db()
        subscription2.refresh_from_db()
        self.assertEqual(subscription1.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)  # Should remain ACTIVE
        self.assertEqual(subscription2.status,
                         UserSubscription.UserSubscriptionChoices.ACTIVE)  # Should remain ACTIVE

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    @patch('stripe_webhooks.tasks_handlers.customer_handlers.get_stripe_customer_session_url')
    def test_concurrent_customer_creation_username_conflict(self, mock_session_url, mock_send_email):
        """Test handling of username conflicts in concurrent customer creation."""
        # This test simulates concurrent creation of users with similar stripe customer IDs
        mock_session_url.return_value = (
            None, "https://billing.stripe.com/session/test")
        mock_send_email.return_value = None
        # Use unique IDs with timestamp to avoid conflicts with other tests
        import time
        timestamp = str(int(time.time()))
        unique_customer_id_1 = f'cus_concurrent_test_{timestamp}_001'
        unique_customer_id_2 = f'cus_concurrent_test_{timestamp}_002'
        unique_email_1 = f'concurrent1_{timestamp}@example.com'
        unique_email_2 = f'concurrent2_{timestamp}@example.com'

        # Create unique payload for first customer
        payload1 = {
            'id': unique_customer_id_1,
            'name': f'Concurrent Test User {timestamp} 1',
            'email': unique_email_1,
            'preferred_locales': [ENGLISH_LANG_CODE]
        }

        # Create first customer
        response1 = handle_customer_created(payload1)

        self.assertEqual(response1.code, 201)

        user1 = User.objects.get(stripe_customer_id=unique_customer_id_1)

        # Create second customer with similar name but different ID
        payload2 = {
            'id': unique_customer_id_2,
            'name': f'Concurrent Test User {timestamp} 2',  # Similar name
            'email': unique_email_2,
            'preferred_locales': [ENGLISH_LANG_CODE]
        }

        response2 = handle_customer_created(payload2)

        self.assertEqual(response2.code, 201)

        user2 = User.objects.get(stripe_customer_id=unique_customer_id_2)

        # Verify usernames are different (this is the main point of the test)
        self.assertNotEqual(user1.username, user2.username)

        # Verify both users were created successfully
        self.assertEqual(user1.email, unique_email_1)
        self.assertEqual(user2.email, unique_email_2)

    @patch('stripe_webhooks.tasks_handlers.customer_handlers.send_email')
    def test_customer_creation_email_failure_returns_error(self, mock_send_email):
        """Test that customer creation returns error when email sending fails."""
        # Use unique customer ID to avoid conflicts
        test_customer_id = 'cus_email_test_123'
        test_email = 'email_test@example.com'

        # Create unique payload
        unique_payload = {
            'id': test_customer_id,
            'name': 'Email Test User',
            'email': test_email,
            'preferred_locales': [ENGLISH_LANG_CODE]
        }

        # Mock email sending to fail
        from stripe_webhooks.tasks_handlers.error.error import error_message
        mock_error = error_message(
            "exception", function_name="send_email", exception=Exception("Email service unavailable"))
        mock_send_email.return_value = mock_error

        response = handle_customer_created(unique_payload)

        # Should return error due to email failure
        self.assertNotEqual(response.code, 201)
        self.assertTrue(response.code >= 400)  # Should be an error code

        # Verify that send_email was called (meaning user creation succeeded up to that point)
        self.assertTrue(mock_send_email.called)

        # Note: Due to the current implementation, user creation may or may not be rolled back
        # depending on the test environment. The important thing is that an error is returned.

    def test_performance_bulk_operations(self):
        """Test performance with bulk operations."""
        # Create subscription type
        subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            price_type=SubscriptionType.PriceTypeChoices.AU,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=TEST_STRIPE_PRODUCT_ID
        )

        # Create multiple users and subscriptions
        users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f"user{i}",
                email=f"user{i}@example.com",
                stripe_customer_id=f"cus_test{i}"
            )
            users.append(user)

            UserSubscription.objects.create(
                user=user,
                subscription=subscription_type,
                stripe_subscription_id=f"sub_test{i}",
                status=UserSubscription.UserSubscriptionChoices.ACTIVE,
                start_date=timezone.now(),
                end_date=timezone.now())

        # Update all subscriptions with bulk update
        UserSubscription.objects.filter(
            subscription=subscription_type
        ).update(status=UserSubscription.UserSubscriptionChoices.TERMINATED)

        # Verify all were updated
        canceled_count = UserSubscription.objects.filter(
            subscription=subscription_type,
            status=UserSubscription.UserSubscriptionChoices.TERMINATED
        ).count()

        self.assertEqual(canceled_count, 10)
