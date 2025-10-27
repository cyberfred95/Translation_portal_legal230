"""
Integration tests for count history functionality.

This module contains integration tests that verify the complete flow
of count history creation and user subscription reset functionality.
"""

from django.test import TestCase
from django.utils import timezone

from stripe_webhooks.tasks_handlers.setter.set_countHistory import (
    create_countHistory,
    reset_subscriptions,
)
from stripe_webhooks.tasks_handlers.setter.set_userSubscription import (
    reset_userSubscription_counts,
)
from stripe_webhooks.tests.settings import (
    ENGLISH_LANG_CODE,
    SUBSCRIPTION_STATUS_ACTIVE,
    TEST_GROUP_NAME,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_STRIPE_PRODUCT_ID,
    TEST_STRIPE_SUBSCRIPTION_ID,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PRICE,
    TEST_EMAIL,
)
from subscriptions.models import CountHistory, SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group


class CountHistoryIntegrationTestCase(TestCase):
    """Integration test case for count history functionality."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)
        self.user1 = User.objects.create(
            username='testuser1',
            email=TEST_EMAIL,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            language=ENGLISH_LANG_CODE,
            group=self.group
        )
        self.user2 = User.objects.create(
            username='testuser2',
            email='test2@example.com',
            stripe_customer_id='cus_test2',
            language=ENGLISH_LANG_CODE,
            group=self.group
        )

        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            stripe_product_id=TEST_STRIPE_PRODUCT_ID,
            max_symbols_count=1000,
            max_words_count=500,
            max_files_count=10,
            custom_glossaries_count=5,
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=TEST_SUBSCRIPTION_PRICE,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

        # Create multiple user subscriptions with the same stripe_subscription_id
        self.user_subscription1 = UserSubscription.objects.create(
            user=self.user1,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=150,
            translated_words_count=75,
            translated_files_count=3
        )

        self.user_subscription2 = UserSubscription.objects.create(
            user=self.user2,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=200,
            translated_words_count=100,
            translated_files_count=5
        )

    def test_reset_subscriptions_integration(self):
        """Test the complete reset subscriptions flow."""
        user_subscription_list = [
            self.user_subscription1, self.user_subscription2]

        # Verify initial state
        self.assertEqual(CountHistory.objects.count(), 0)
        self.assertEqual(self.user_subscription1.translated_symbols_count, 150)
        self.assertEqual(self.user_subscription1.translated_words_count, 75)
        self.assertEqual(self.user_subscription1.translated_files_count, 3)
        self.assertEqual(self.user_subscription2.translated_symbols_count, 200)
        self.assertEqual(self.user_subscription2.translated_words_count, 100)
        self.assertEqual(self.user_subscription2.translated_files_count, 5)

        # Execute reset_subscriptions
        error_response, count_histories = reset_subscriptions(
            user_subscription_list)

        # Verify success
        self.assertIsNone(error_response)
        self.assertIsNotNone(count_histories)
        self.assertEqual(len(count_histories), 2)

        # Verify CountHistory records were created
        db_count_histories = CountHistory.objects.all()
        self.assertEqual(db_count_histories.count(), 2)

        # Verify each CountHistory record
        history1 = CountHistory.objects.get(
            user_subscription=self.user_subscription1)
        self.assertEqual(history1.subscription_type, self.subscription_type)
        self.assertEqual(history1.start_date,
                         self.user_subscription1.start_date)
        self.assertEqual(history1.translated_symbols_count, 150)
        self.assertEqual(history1.translated_words_count, 75)
        self.assertEqual(history1.translated_files_count, 3)

        history2 = CountHistory.objects.get(
            user_subscription=self.user_subscription2)
        self.assertEqual(history2.subscription_type, self.subscription_type)
        self.assertEqual(history2.start_date,
                         self.user_subscription2.start_date)
        self.assertEqual(history2.translated_symbols_count, 200)
        self.assertEqual(history2.translated_words_count, 100)
        self.assertEqual(history2.translated_files_count, 5)

        # Verify user subscription counters were reset
        self.user_subscription1.refresh_from_db()
        self.user_subscription2.refresh_from_db()

        self.assertEqual(self.user_subscription1.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription1.translated_words_count, 0)
        self.assertEqual(self.user_subscription1.translated_files_count, 0)
        self.assertEqual(self.user_subscription2.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription2.translated_words_count, 0)
        self.assertEqual(self.user_subscription2.translated_files_count, 0)

    def test_create_countHistory_integration(self):
        """Test creation of CountHistory with real database operations."""
        # Verify initial state
        self.assertEqual(CountHistory.objects.count(), 0)

        # Create CountHistory
        error_response, count_history = create_countHistory(
            self.user_subscription1)

        # Verify success
        self.assertIsNone(error_response)
        self.assertIsNotNone(count_history)

        # Verify database state
        self.assertEqual(CountHistory.objects.count(), 1)

        # Verify the created record
        db_history = CountHistory.objects.get(id=count_history.id)
        self.assertEqual(db_history.user_subscription, self.user_subscription1)
        self.assertEqual(db_history.subscription_type, self.subscription_type)
        self.assertEqual(db_history.start_date,
                         self.user_subscription1.start_date)
        self.assertEqual(db_history.translated_symbols_count, 150)
        self.assertEqual(db_history.translated_words_count, 75)
        self.assertEqual(db_history.translated_files_count, 3)

    def test_reset_userSubscription_counts_integration(self):
        """Test reset of user subscription counts with real database operations."""
        # Verify initial state
        self.assertEqual(self.user_subscription1.translated_symbols_count, 150)
        self.assertEqual(self.user_subscription1.translated_words_count, 75)
        self.assertEqual(self.user_subscription1.translated_files_count, 3)

        # Reset counts
        error_response, updated_subscription = reset_userSubscription_counts(
            self.user_subscription1)

        # Verify success
        self.assertIsNone(error_response)
        self.assertIsNotNone(updated_subscription)

        # Verify database state
        self.user_subscription1.refresh_from_db()
        self.assertEqual(self.user_subscription1.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription1.translated_words_count, 0)
        self.assertEqual(self.user_subscription1.translated_files_count, 0)

    def test_multiple_reset_subscriptions_create_separate_histories(self):
        """Test that multiple reset operations create separate count histories."""
        user_subscription_list = [
            self.user_subscription1, self.user_subscription2]

        # First reset
        error_response1, count_histories1 = reset_subscriptions(
            user_subscription_list)
        self.assertIsNone(error_response1)
        self.assertEqual(CountHistory.objects.count(), 2)

        # Reset counters for second test
        self.user_subscription1.translated_symbols_count = 50
        self.user_subscription1.translated_words_count = 25
        self.user_subscription1.translated_files_count = 1
        self.user_subscription1.save()

        self.user_subscription2.translated_symbols_count = 75
        self.user_subscription2.translated_words_count = 35
        self.user_subscription2.translated_files_count = 2
        self.user_subscription2.save()

        # Second reset
        error_response2, count_histories2 = reset_subscriptions(
            user_subscription_list)
        self.assertIsNone(error_response2)

        # Should now have 4 CountHistory records (2 from each reset)
        self.assertEqual(CountHistory.objects.count(), 4)

        # Verify counters are reset again
        self.user_subscription1.refresh_from_db()
        self.user_subscription2.refresh_from_db()

        self.assertEqual(self.user_subscription1.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription1.translated_words_count, 0)
        self.assertEqual(self.user_subscription1.translated_files_count, 0)
        self.assertEqual(self.user_subscription2.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription2.translated_words_count, 0)
        self.assertEqual(self.user_subscription2.translated_files_count, 0)

    def test_count_history_relationships(self):
        """Test that CountHistory correctly links to UserSubscription and SubscriptionType."""
        user_subscription_list = [
            self.user_subscription1, self.user_subscription2]

        error_response, count_histories = reset_subscriptions(
            user_subscription_list)
        self.assertIsNone(error_response)

        # Verify relationships
        db_count_histories = CountHistory.objects.all()
        self.assertEqual(db_count_histories.count(), 2)

        for history in db_count_histories:
            self.assertIn(history.user_subscription, [
                          self.user_subscription1, self.user_subscription2])
            self.assertEqual(history.subscription_type, self.subscription_type)
            self.assertIsNotNone(history.start_date)

        # Verify reverse relationships
        self.assertEqual(self.user_subscription1.count_histories.count(), 1)
        self.assertEqual(self.user_subscription2.count_histories.count(), 1)
        self.assertEqual(self.subscription_type.count_histories.count(), 2)
