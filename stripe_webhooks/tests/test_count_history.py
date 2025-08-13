"""
Unit tests for count history and invoice payment succeeded functionality.

This module contains tests for the new invoice payment succeeded handler
and related count history functions.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

from django.test import TestCase
from django.utils import timezone

from stripe_webhooks.tasks_handlers.invoice_payment_succeeded import (
    handle_invoice_payment_succeeded,
)
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


class InvoicePaymentSucceededTestCase(TestCase):
    """Test case for handle_invoice_payment_succeeded function."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)
        self.user = User.objects.create(
            username='testuser',
            email=TEST_EMAIL,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
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
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=TEST_SUBSCRIPTION_PRICE,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=100,
            translated_words_count=50,
            translated_files_count=2
        )

    def test_handle_invoice_payment_succeeded_success(self):
        """Test successful handling of invoice.payment.succeeded event."""
        payload = {
            'data': {
                'object': {
                    'customer': TEST_STRIPE_CUSTOMER_ID
                }
            }
        }

        with patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_payload_customer_id') as mock_get_customer_id, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_user_by_stripe_customer_id') as mock_get_user, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_stripe_subscription_id_from_user') as mock_get_subscription_id, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_userSubscriptions_list_by_stripe_subscription_id') as mock_get_subscriptions, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.reset_subscriptions') as mock_reset_subscriptions, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.success_message') as mock_success_message:

            # Mock return values
            mock_get_customer_id.return_value = (None, TEST_STRIPE_CUSTOMER_ID)
            mock_get_user.return_value = (None, self.user)
            mock_get_subscription_id.return_value = (
                None, TEST_STRIPE_SUBSCRIPTION_ID)
            mock_get_subscriptions.return_value = (
                None, [self.user_subscription])
            mock_reset_subscriptions.return_value = (None, [MagicMock()])
            mock_success_message.return_value = MagicMock()

            result = handle_invoice_payment_succeeded(payload)

            # Verify function calls
            mock_get_customer_id.assert_called_once_with(payload)
            mock_get_user.assert_called_once_with(TEST_STRIPE_CUSTOMER_ID)
            mock_get_subscription_id.assert_called_once_with(self.user)
            mock_get_subscriptions.assert_called_once_with(
                TEST_STRIPE_SUBSCRIPTION_ID)
            mock_reset_subscriptions.assert_called_once_with(
                [self.user_subscription])
            mock_success_message.assert_called_once_with(
                "invoice_payment_succeeded",
                stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
                countHistory_count=1
            )

    def test_handle_invoice_payment_succeeded_payload_error(self):
        """Test handling when payload parsing fails."""
        payload = {'invalid': 'payload'}
        error_response = MagicMock()

        with patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_payload_customer_id') as mock_get_customer_id:
            mock_get_customer_id.return_value = (error_response, None)

            result = handle_invoice_payment_succeeded(payload)

            self.assertEqual(result, error_response)

    def test_handle_invoice_payment_succeeded_subscription_not_found(self):
        """Test handling when subscription is not found."""
        payload = {
            'data': {
                'object': {
                    'customer': TEST_STRIPE_CUSTOMER_ID
                }
            }
        }
        error_response = MagicMock()

        with patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_payload_customer_id') as mock_get_customer_id, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_user_by_stripe_customer_id') as mock_get_user, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_stripe_subscription_id_from_user') as mock_get_subscription_id:

            mock_get_customer_id.return_value = (None, TEST_STRIPE_CUSTOMER_ID)
            mock_get_user.return_value = (None, self.user)
            mock_get_subscription_id.return_value = (error_response, None)

            result = handle_invoice_payment_succeeded(payload)

            self.assertEqual(result, error_response)

    def test_handle_invoice_payment_succeeded_reset_error(self):
        """Test handling when reset_subscriptions fails."""
        payload = {
            'data': {
                'object': {
                    'customer': TEST_STRIPE_CUSTOMER_ID
                }
            }
        }
        error_response = MagicMock()

        with patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_payload_customer_id') as mock_get_customer_id, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_user_by_stripe_customer_id') as mock_get_user, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_stripe_subscription_id_from_user') as mock_get_subscription_id, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.get_userSubscriptions_list_by_stripe_subscription_id') as mock_get_subscriptions, \
                patch('stripe_webhooks.tasks_handlers.invoice_payment_succeeded.reset_subscriptions') as mock_reset_subscriptions:

            mock_get_customer_id.return_value = (None, TEST_STRIPE_CUSTOMER_ID)
            mock_get_user.return_value = (None, self.user)
            mock_get_subscription_id.return_value = (
                None, TEST_STRIPE_SUBSCRIPTION_ID)
            mock_get_subscriptions.return_value = (
                None, [self.user_subscription])
            mock_reset_subscriptions.return_value = (error_response, None)

            result = handle_invoice_payment_succeeded(payload)

            self.assertEqual(result, error_response)


class ResetSubscriptionsTestCase(TestCase):
    """Test case for reset_subscriptions function."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)
        self.user = User.objects.create(
            username='testuser',
            email=TEST_EMAIL,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
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
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=TEST_SUBSCRIPTION_PRICE,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=100,
            translated_words_count=50,
            translated_files_count=2
        )

    def test_reset_subscriptions_success(self):
        """Test successful reset of subscriptions."""
        user_subscription_list = [self.user_subscription]

        with patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.create_countHistory') as mock_create_history, \
                patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.reset_userSubscription_counts') as mock_reset_counts:

            mock_count_history = MagicMock()
            mock_create_history.return_value = (None, mock_count_history)
            mock_reset_counts.return_value = (None, self.user_subscription)

            error_response, count_histories = reset_subscriptions(
                user_subscription_list)

            self.assertIsNone(error_response)
            self.assertEqual(len(count_histories), 1)
            self.assertEqual(count_histories[0], mock_count_history)

            mock_create_history.assert_called_once_with(self.user_subscription)
            mock_reset_counts.assert_called_once_with(self.user_subscription)

    def test_reset_subscriptions_create_history_error(self):
        """Test reset_subscriptions when create_countHistory fails."""
        user_subscription_list = [self.user_subscription]
        error_response = MagicMock()

        with patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.create_countHistory') as mock_create_history:
            mock_create_history.return_value = (error_response, None)

            result_error, count_histories = reset_subscriptions(
                user_subscription_list)

            self.assertEqual(result_error, error_response)
            self.assertIsNone(count_histories)

    def test_reset_subscriptions_reset_counts_error(self):
        """Test reset_subscriptions when reset_userSubscription_counts fails."""
        user_subscription_list = [self.user_subscription]
        error_response = MagicMock()

        with patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.create_countHistory') as mock_create_history, \
                patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.reset_userSubscription_counts') as mock_reset_counts:

            mock_count_history = MagicMock()
            mock_create_history.return_value = (None, mock_count_history)
            mock_reset_counts.return_value = (error_response, None)

            result_error, count_histories = reset_subscriptions(
                user_subscription_list)

            self.assertEqual(result_error, error_response)
            self.assertIsNone(count_histories)

    def test_reset_subscriptions_multiple_subscriptions(self):
        """Test reset_subscriptions with multiple subscriptions."""
        # Create second user and subscription
        user2 = User.objects.create(
            username='testuser2',
            email='test2@example.com',
            stripe_customer_id='cus_test2',
            language=ENGLISH_LANG_CODE,
            group=self.group
        )

        user_subscription2 = UserSubscription.objects.create(
            user=user2,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=200,
            translated_words_count=100,
            translated_files_count=3
        )

        user_subscription_list = [self.user_subscription, user_subscription2]

        with patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.create_countHistory') as mock_create_history, \
                patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.reset_userSubscription_counts') as mock_reset_counts:

            mock_count_history1 = MagicMock()
            mock_count_history2 = MagicMock()
            mock_create_history.side_effect = [
                (None, mock_count_history1),
                (None, mock_count_history2)
            ]
            mock_reset_counts.return_value = (None, MagicMock())

            error_response, count_histories = reset_subscriptions(
                user_subscription_list)

            self.assertIsNone(error_response)
            self.assertEqual(len(count_histories), 2)
            self.assertEqual(mock_create_history.call_count, 2)
            self.assertEqual(mock_reset_counts.call_count, 2)

    def test_reset_subscriptions_exception(self):
        """Test reset_subscriptions when an exception is raised."""
        user_subscription_list = [self.user_subscription]

        with patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.create_countHistory') as mock_create_history, \
                patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.exception_error') as mock_exception_error:

            test_exception = Exception("Test exception")
            mock_create_history.side_effect = test_exception
            mock_error_response = MagicMock()
            mock_exception_error.return_value = mock_error_response

            error_response, count_histories = reset_subscriptions(
                user_subscription_list)

            self.assertEqual(error_response, mock_error_response)
            self.assertIsNone(count_histories)
            mock_exception_error.assert_called_once_with(test_exception)


class CreateCountHistoryTestCase(TestCase):
    """Test case for create_countHistory function."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)
        self.user = User.objects.create(
            username='testuser',
            email=TEST_EMAIL,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
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
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=TEST_SUBSCRIPTION_PRICE,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=100,
            translated_words_count=50,
            translated_files_count=2
        )

    def test_create_countHistory_success(self):
        """Test successful creation of CountHistory."""
        error_response, count_history = create_countHistory(
            self.user_subscription)

        self.assertIsNone(error_response)
        self.assertIsNotNone(count_history)
        self.assertIsInstance(count_history, CountHistory)

        # Verify the CountHistory was saved to the database
        saved_history = CountHistory.objects.get(id=count_history.id)
        self.assertEqual(saved_history.user_subscription,
                         self.user_subscription)
        self.assertEqual(saved_history.subscription_type,
                         self.subscription_type)
        self.assertEqual(saved_history.start_date,
                         self.user_subscription.start_date)
        self.assertEqual(saved_history.translated_symbols_count, 100)
        self.assertEqual(saved_history.translated_words_count, 50)
        self.assertEqual(saved_history.translated_files_count, 2)

    def test_create_countHistory_database_error(self):
        """Test create_countHistory when database save fails."""
        with patch('subscriptions.models.CountHistory.objects.create') as mock_create, \
                patch('stripe_webhooks.tasks_handlers.setter.set_countHistory.exception_error') as mock_exception_error:

            test_exception = Exception("Database error")
            mock_create.side_effect = test_exception
            mock_error_response = MagicMock()
            mock_exception_error.return_value = mock_error_response

            error_response, count_history = create_countHistory(
                self.user_subscription)

            self.assertEqual(error_response, mock_error_response)
            self.assertIsNone(count_history)
            mock_exception_error.assert_called_once_with(test_exception)

    def test_create_countHistory_values(self):
        """Test that CountHistory is created with correct values."""
        start_date = timezone.now()
        self.user_subscription.start_date = start_date
        self.user_subscription.save()

        error_response, count_history = create_countHistory(
            self.user_subscription)

        self.assertIsNone(error_response)
        self.assertEqual(count_history.user_subscription,
                         self.user_subscription)
        self.assertEqual(count_history.subscription_type,
                         self.subscription_type)
        self.assertEqual(count_history.start_date, start_date)
        self.assertEqual(count_history.translated_symbols_count, 100)
        self.assertEqual(count_history.translated_words_count, 50)
        self.assertEqual(count_history.translated_files_count, 2)


class ResetUserSubscriptionCountsTestCase(TestCase):
    """Test case for reset_userSubscription_counts function."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)
        self.user = User.objects.create(
            username='testuser',
            email=TEST_EMAIL,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
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
            price_type=SubscriptionType.PriceTypeChoices.PUMP,
            price=TEST_SUBSCRIPTION_PRICE,
            access_to_writing=True,
            access_to_official_glossaries=True,
            access_to_sso=False
        )

        self.user_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            translated_symbols_count=100,
            translated_words_count=50,
            translated_files_count=2
        )

    def test_reset_userSubscription_counts_success(self):
        """Test successful reset of user subscription counts."""
        # Verify initial values
        self.assertEqual(self.user_subscription.translated_symbols_count, 100)
        self.assertEqual(self.user_subscription.translated_words_count, 50)
        self.assertEqual(self.user_subscription.translated_files_count, 2)

        error_response, updated_subscription = reset_userSubscription_counts(
            self.user_subscription)

        self.assertIsNone(error_response)
        self.assertIsNotNone(updated_subscription)
        self.assertEqual(updated_subscription, self.user_subscription)

        # Verify counts are reset
        self.user_subscription.refresh_from_db()
        self.assertEqual(self.user_subscription.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription.translated_words_count, 0)
        self.assertEqual(self.user_subscription.translated_files_count, 0)

    def test_reset_userSubscription_counts_database_error(self):
        """Test reset_userSubscription_counts when database save fails."""
        with patch.object(self.user_subscription, 'save') as mock_save, \
                patch('stripe_webhooks.tasks_handlers.setter.set_userSubscription.exception_error') as mock_exception_error:

            test_exception = Exception("Database error")
            mock_save.side_effect = test_exception
            mock_error_response = MagicMock()
            mock_exception_error.return_value = mock_error_response

            error_response, updated_subscription = reset_userSubscription_counts(
                self.user_subscription)

            self.assertEqual(error_response, mock_error_response)
            self.assertIsNone(updated_subscription)
            mock_exception_error.assert_called_once_with(test_exception)

    def test_reset_userSubscription_counts_zero_values(self):
        """Test reset when counts are already zero."""
        # Set counts to zero
        self.user_subscription.translated_symbols_count = 0
        self.user_subscription.translated_words_count = 0
        self.user_subscription.translated_files_count = 0
        self.user_subscription.save()

        error_response, updated_subscription = reset_userSubscription_counts(
            self.user_subscription)

        self.assertIsNone(error_response)
        self.assertIsNotNone(updated_subscription)

        # Verify counts remain zero
        self.user_subscription.refresh_from_db()
        self.assertEqual(self.user_subscription.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription.translated_words_count, 0)
        self.assertEqual(self.user_subscription.translated_files_count, 0)

    def test_reset_userSubscription_counts_high_values(self):
        """Test reset with high count values."""
        # Set high values
        self.user_subscription.translated_symbols_count = 999999
        self.user_subscription.translated_words_count = 555555
        self.user_subscription.translated_files_count = 1000
        self.user_subscription.save()

        error_response, updated_subscription = reset_userSubscription_counts(
            self.user_subscription)

        self.assertIsNone(error_response)
        self.assertIsNotNone(updated_subscription)

        # Verify counts are reset to zero
        self.user_subscription.refresh_from_db()
        self.assertEqual(self.user_subscription.translated_symbols_count, 0)
        self.assertEqual(self.user_subscription.translated_words_count, 0)
        self.assertEqual(self.user_subscription.translated_files_count, 0)
