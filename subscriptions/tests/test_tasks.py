"""
Tests for subscription management tasks.

This module contains tests for the daily subscription renewal task
for offline subscriptions.
"""

from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.utils import timezone

from subscriptions.models import UserSubscription, SubscriptionType, CountHistory
from subscriptions.tasks import process_daily_subscription_renewals
from users.models import User, UserGroup
from tests.mock import create_test_user_group


class ProcessDailySubscriptionRenewalsTestCase(TestCase):
    """Test case for the process_daily_subscription_renewals task."""

    def setUp(self):
        """Set up test data."""
        # Create a user group
        self.group = create_test_user_group(name="Test Group")

        # Create a user
        self.user = User.objects.create(
            username='testuser',
            email='test@example.com',
            group=self.group,
            language='en'
        )

        # Create a subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name='Test Subscription',
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=99.99,
            max_symbols_count=1000,
            max_words_count=500,
            max_files_count=10,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

    def test_process_daily_subscription_renewals_success(self):
        """Test successful renewal of an offline subscription."""
        # Fixed test date
        test_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Create an offline subscription (without stripe_subscription_id)
        # that expires today
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,  # Offline subscription
            start_date=test_date - timedelta(days=30),
            end_date=test_date,  # Expires today
            translated_symbols_count=100,
            translated_words_count=50,
            translated_files_count=2
        )

        # Mock timezone.now() and reset_subscriptions
        with patch('subscriptions.tasks.timezone.now') as mock_now, \
                patch('subscriptions.tasks.reset_subscriptions') as mock_reset:

            mock_now.return_value = test_date
            # No error, list of CountHistory
            mock_reset.return_value = (None, [MagicMock()])

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result['renewed_count'], 1)
            self.assertEqual(result['error_count'], 0)
            self.assertEqual(result['total_processed'], 1)

            # Verify that reset_subscriptions was called
            mock_reset.assert_called_once_with([user_subscription])

            # Verify that the end date was updated (+1 month)
            user_subscription.refresh_from_db()
            expected_end_date = datetime(
                2025, 2, 15, 12, 0, 0, tzinfo=timezone.utc)
            self.assertEqual(user_subscription.end_date, expected_end_date)

    def test_process_daily_subscription_renewals_with_stripe_id_ignored(self):
        """Test that subscriptions with stripe_subscription_id are ignored."""
        test_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Create a subscription with stripe_subscription_id
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id='sub_test123',  # Stripe subscription
            start_date=test_date - timedelta(days=30),
            end_date=test_date,  # Expires today
        )

        # Mock timezone.now()
        with patch('subscriptions.tasks.timezone.now') as mock_now:
            mock_now.return_value = test_date

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result['renewed_count'], 0)
            self.assertEqual(result['error_count'], 0)
            self.assertEqual(result['total_processed'], 0)

    def test_process_daily_subscription_renewals_inactive_status_ignored(self):
        """Test that inactive subscriptions are ignored."""
        test_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Create an inactive subscription
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.TERMINATED,  # Inactive
            stripe_subscription_id=None,
            start_date=test_date - timedelta(days=30),
            end_date=test_date,  # Expires today
        )

        # Mock timezone.now()
        with patch('subscriptions.tasks.timezone.now') as mock_now:
            mock_now.return_value = test_date

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result['renewed_count'], 0)
            self.assertEqual(result['error_count'], 0)
            self.assertEqual(result['total_processed'], 0)

    def test_process_daily_subscription_renewals_wrong_end_date_ignored(self):
        """Test that subscriptions not expiring today are ignored."""
        test_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Create a subscription that expires tomorrow
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=test_date - timedelta(days=30),
            end_date=test_date + timedelta(days=1),  # Expires tomorrow
        )

        # Mock timezone.now()
        with patch('subscriptions.tasks.timezone.now') as mock_now:
            mock_now.return_value = test_date

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result['renewed_count'], 0)
            self.assertEqual(result['error_count'], 0)
            self.assertEqual(result['total_processed'], 0)

    def test_process_daily_subscription_renewals_december_to_january(self):
        """Test transition from December to January for next month calculation."""
        test_date = datetime(2025, 12, 31, 12, 0, 0, tzinfo=timezone.utc)

        # Create a subscription that expires on December 31st
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=test_date - timedelta(days=30),
            end_date=test_date,  # Expires today (December 31st)
        )

        # Mock timezone.now() and reset_subscriptions
        with patch('subscriptions.tasks.timezone.now') as mock_now, \
                patch('subscriptions.tasks.reset_subscriptions') as mock_reset:

            mock_now.return_value = test_date
            mock_reset.return_value = (None, [MagicMock()])

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result['renewed_count'], 1)

            # Verify that the end date was updated (January 31st of next year)
            user_subscription.refresh_from_db()
            expected_end_date = datetime(
                2026, 1, 31, 12, 0, 0, tzinfo=timezone.utc)
            self.assertEqual(user_subscription.end_date, expected_end_date)

    def test_process_daily_subscription_renewals_reset_error_handling(self):
        """Test error handling during subscription reset."""
        test_date = datetime(2025, 1, 15, 12, 0, 0, tzinfo=timezone.utc)

        # Create an offline subscription
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=test_date - timedelta(days=30),
            end_date=test_date,
        )

        # Mock reset_subscriptions that returns an error
        error_response = MagicMock()
        error_response.__str__ = lambda x: "Test error"

        # Mock timezone.now() and reset_subscriptions
        with patch('subscriptions.tasks.timezone.now') as mock_now, \
                patch('subscriptions.tasks.reset_subscriptions') as mock_reset:

            mock_now.return_value = test_date
            mock_reset.return_value = (error_response, None)  # Error

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result['renewed_count'], 0)
            self.assertEqual(result['error_count'], 1)
            self.assertEqual(result['total_processed'], 1)

            # Verify that the end date was not modified
            user_subscription.refresh_from_db()
            self.assertEqual(user_subscription.end_date, test_date)
