"""
Tests for subscription management tasks.

This module contains tests for the daily subscription renewal task
for offline subscriptions.
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase

from subscriptions.models import UserSubscription, SubscriptionType, CountHistory
from subscriptions.tasks import process_daily_subscription_renewals
from users.models import User, UserGroup
from tests.mock import create_test_user_group

# Import des constantes centralisées
from .settings import (
    TEST_USERNAME,
    TEST_EMAIL,
    TEST_LANGUAGE,
    TEST_GROUP_NAME,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PRICE,
    TEST_MAX_SYMBOLS_COUNT,
    TEST_MAX_WORDS_COUNT,
    TEST_MAX_FILES_COUNT,
    TEST_ACCESS_TO_WRITING,
    TEST_ACCESS_TO_OFFICIAL_GLOSSARIES,
    TEST_ACCESS_TO_SSO,
    TEST_DATE_JANUARY,
    TEST_DATE_DECEMBER,
    EXPECTED_DATE_FEBRUARY,
    EXPECTED_DATE_JANUARY_NEXT_YEAR,
    TEST_TRANSLATED_SYMBOLS_COUNT,
    TEST_TRANSLATED_WORDS_COUNT,
    TEST_TRANSLATED_FILES_COUNT,
    SUBSCRIPTION_DURATION_DAYS,
    NEXT_DAY_OFFSET,
    TEST_STRIPE_SUBSCRIPTION_ID,
    EXPECTED_RENEWED_COUNT_SUCCESS,
    EXPECTED_ERROR_COUNT_SUCCESS,
    EXPECTED_TOTAL_PROCESSED_SUCCESS,
    EXPECTED_RENEWED_COUNT_IGNORED,
    EXPECTED_ERROR_COUNT_IGNORED,
    EXPECTED_TOTAL_PROCESSED_IGNORED,
    EXPECTED_RENEWED_COUNT_ERROR,
    EXPECTED_ERROR_COUNT_ERROR,
    EXPECTED_TOTAL_PROCESSED_ERROR,
    PATCH_TIMEZONE_NOW,
    PATCH_RESET_SUBSCRIPTIONS,
    TEST_ERROR_MESSAGE,
    RESULT_KEY_RENEWED_COUNT,
    RESULT_KEY_ERROR_COUNT,
    RESULT_KEY_TOTAL_PROCESSED,
)


class ProcessDailySubscriptionRenewalsTestCase(TestCase):
    """Test case for the process_daily_subscription_renewals task."""

    def setUp(self):
        """Set up test data."""
        # Create a user group
        self.group = create_test_user_group(name=TEST_GROUP_NAME)

        # Create a user
        self.user = User.objects.create(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            group=self.group,
            language=TEST_LANGUAGE
        )

        # Create a subscription type
        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=TEST_SUBSCRIPTION_PRICE,
            max_symbols_count=TEST_MAX_SYMBOLS_COUNT,
            max_words_count=TEST_MAX_WORDS_COUNT,
            max_files_count=TEST_MAX_FILES_COUNT,
            access_to_writing=TEST_ACCESS_TO_WRITING,
            access_to_official_glossaries=TEST_ACCESS_TO_OFFICIAL_GLOSSARIES,
            access_to_sso=TEST_ACCESS_TO_SSO
        )

    def test_process_daily_subscription_renewals_success(self):
        """Test successful renewal of an offline subscription."""
        # Create an offline subscription (without stripe_subscription_id)
        # that expires today
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,  # Offline subscription
            start_date=TEST_DATE_JANUARY - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_JANUARY,  # Expires today
            translated_symbols_count=TEST_TRANSLATED_SYMBOLS_COUNT,
            translated_words_count=TEST_TRANSLATED_WORDS_COUNT,
            translated_files_count=TEST_TRANSLATED_FILES_COUNT
        )

        # Mock timezone.now() and reset_subscriptions
        with patch(PATCH_TIMEZONE_NOW) as mock_now, \
                patch(PATCH_RESET_SUBSCRIPTIONS) as mock_reset:

            mock_now.return_value = TEST_DATE_JANUARY
            # No error, list of CountHistory
            mock_reset.return_value = (None, [MagicMock()])

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_SUCCESS)
            self.assertEqual(result[RESULT_KEY_ERROR_COUNT], EXPECTED_ERROR_COUNT_SUCCESS)
            self.assertEqual(result[RESULT_KEY_TOTAL_PROCESSED], EXPECTED_TOTAL_PROCESSED_SUCCESS)

            # Verify that reset_subscriptions was called
            mock_reset.assert_called_once_with([user_subscription])

            # Verify that the end date was updated (+1 month)
            user_subscription.refresh_from_db()
            self.assertEqual(user_subscription.end_date, EXPECTED_DATE_FEBRUARY)

    def test_process_daily_subscription_renewals_with_stripe_id_ignored(self):
        """Test that subscriptions with stripe_subscription_id are ignored."""
        # Create a subscription with stripe_subscription_id
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,  # Stripe subscription
            start_date=TEST_DATE_JANUARY - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_JANUARY,  # Expires today
        )

        # Mock timezone.now()
        with patch(PATCH_TIMEZONE_NOW) as mock_now:
            mock_now.return_value = TEST_DATE_JANUARY

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_ERROR_COUNT], EXPECTED_ERROR_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_TOTAL_PROCESSED], EXPECTED_TOTAL_PROCESSED_IGNORED)

    def test_process_daily_subscription_renewals_inactive_status_ignored(self):
        """Test that inactive subscriptions are ignored."""
        # Create an inactive subscription
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.TERMINATED,  # Inactive
            stripe_subscription_id=None,
            start_date=TEST_DATE_JANUARY - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_JANUARY,  # Expires today
        )

        # Mock timezone.now()
        with patch(PATCH_TIMEZONE_NOW) as mock_now:
            mock_now.return_value = TEST_DATE_JANUARY

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_ERROR_COUNT], EXPECTED_ERROR_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_TOTAL_PROCESSED], EXPECTED_TOTAL_PROCESSED_IGNORED)

    def test_process_daily_subscription_renewals_wrong_end_date_ignored(self):
        """Test that subscriptions not expiring today are ignored."""
        # Create a subscription that expires tomorrow
        UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=TEST_DATE_JANUARY - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_JANUARY + timedelta(days=NEXT_DAY_OFFSET),  # Expires tomorrow
        )

        # Mock timezone.now()
        with patch(PATCH_TIMEZONE_NOW) as mock_now:
            mock_now.return_value = TEST_DATE_JANUARY

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications - no subscription should be processed
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_ERROR_COUNT], EXPECTED_ERROR_COUNT_IGNORED)
            self.assertEqual(result[RESULT_KEY_TOTAL_PROCESSED], EXPECTED_TOTAL_PROCESSED_IGNORED)

    def test_process_daily_subscription_renewals_december_to_january(self):
        """Test transition from December to January for next month calculation."""
        # Create a subscription that expires on December 31st
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=TEST_DATE_DECEMBER - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_DECEMBER,  # Expires today (December 31st)
        )

        # Mock timezone.now() and reset_subscriptions
        with patch(PATCH_TIMEZONE_NOW) as mock_now, \
                patch(PATCH_RESET_SUBSCRIPTIONS) as mock_reset:

            mock_now.return_value = TEST_DATE_DECEMBER
            mock_reset.return_value = (None, [MagicMock()])

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_SUCCESS)

            # Verify that the end date was updated (January 31st of next year)
            user_subscription.refresh_from_db()
            self.assertEqual(user_subscription.end_date, EXPECTED_DATE_JANUARY_NEXT_YEAR)

    def test_process_daily_subscription_renewals_reset_error_handling(self):
        """Test error handling during subscription reset."""
        # Create an offline subscription
        user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            stripe_subscription_id=None,
            start_date=TEST_DATE_JANUARY - timedelta(days=SUBSCRIPTION_DURATION_DAYS),
            end_date=TEST_DATE_JANUARY,
        )

        # Mock reset_subscriptions that returns an error
        error_response = MagicMock()
        error_response.__str__ = lambda x: TEST_ERROR_MESSAGE

        # Mock timezone.now() and reset_subscriptions
        with patch(PATCH_TIMEZONE_NOW) as mock_now, \
                patch(PATCH_RESET_SUBSCRIPTIONS) as mock_reset:

            mock_now.return_value = TEST_DATE_JANUARY
            mock_reset.return_value = (error_response, None)  # Error

            # Execute the task
            result = process_daily_subscription_renewals()

            # Verifications
            self.assertEqual(result[RESULT_KEY_RENEWED_COUNT], EXPECTED_RENEWED_COUNT_ERROR)
            self.assertEqual(result[RESULT_KEY_ERROR_COUNT], EXPECTED_ERROR_COUNT_ERROR)
            self.assertEqual(result[RESULT_KEY_TOTAL_PROCESSED], EXPECTED_TOTAL_PROCESSED_ERROR)

            # Verify that the end date was not modified
            user_subscription.refresh_from_db()
            self.assertEqual(user_subscription.end_date, TEST_DATE_JANUARY)
