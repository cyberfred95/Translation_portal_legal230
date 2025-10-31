"""
Tests simplifiés et fonctionnels pour stripe_webhooks.

Cette version corrige les problèmes identifiés dans les tests précédents.
"""

from datetime import datetime, timezone

from django.test import TestCase

from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group, mock_api_key_generation

# Import des constantes centralisées
from .settings import (
    TEST_STRIPE_CUSTOMER_ID,
    INVALID_STRIPE_CUSTOMER_ID,
    TEST_STRIPE_PRODUCT_ID,
    INVALID_STRIPE_PRODUCT_ID,
    TEST_STRIPE_SUBSCRIPTION_ID,
    INVALID_STRIPE_SUBSCRIPTION_ID,
    TEST_USERNAME,
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_GROUP_NAME,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PRICE,
    ENGLISH_LANG_CODE,
    TEST_FULL_NAME,
    TEST_CUSTOMER_PAYLOAD,
    TEST_CUSTOMER_PAYLOAD_NO_EMAIL,
    TEST_CUSTOMER_PAYLOAD_NO_NAME,
    INVALID_CUSTOMER_PAYLOAD,
)


class SimpleGettersTestCase(TestCase):
    """Test case simplifié pour les getters."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)

        self.user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD,
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID
        )
        self.user.group = self.group
        self.user.save()

        self.subscription_type = SubscriptionType.objects.create(
            name=TEST_SUBSCRIPTION_NAME,
            product_type=SubscriptionType.ProductChoices.WORD_ADD_IN,
            price=TEST_SUBSCRIPTION_PRICE,
            stripe_product_id=TEST_STRIPE_PRODUCT_ID
        )

        # Créer avec les dates obligatoires
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
        from stripe_webhooks.tasks_handlers.getter.get_data import get_user_by_stripe_customer_id

        error, user = get_user_by_stripe_customer_id(TEST_STRIPE_CUSTOMER_ID)

        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.username, TEST_USERNAME)

    def test_get_user_by_stripe_customer_id_not_found(self):
        """Test user retrieval with non-existent stripe customer ID."""
        from stripe_webhooks.tasks_handlers.getter.get_data import get_user_by_stripe_customer_id

        error, user = get_user_by_stripe_customer_id(
            INVALID_STRIPE_CUSTOMER_ID)

        self.assertIsNotNone(error)
        self.assertIsNone(user)
        self.assertEqual(error.code, 404)

    def test_get_subscriptionType_by_stripe_product_id_success(self):
        """Test successful subscription type retrieval by stripe product ID."""
        from stripe_webhooks.tasks_handlers.getter.get_data import get_subscriptionType_by_stripe_product_id

        error, subscription_type = get_subscriptionType_by_stripe_product_id(
            TEST_STRIPE_PRODUCT_ID)

        self.assertIsNone(error)
        self.assertIsNotNone(subscription_type)
        self.assertEqual(subscription_type.stripe_product_id,
                         TEST_STRIPE_PRODUCT_ID)

    def test_get_payload_id_success(self):
        """Test successful ID extraction from payload."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_id

        error, payload_id = get_payload_id(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(payload_id, TEST_STRIPE_CUSTOMER_ID)

    def test_get_payload_id_missing(self):
        """Test ID extraction with missing ID field."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_id

        error, payload_id = get_payload_id(INVALID_CUSTOMER_PAYLOAD)

        self.assertIsNotNone(error)
        self.assertIsNone(payload_id)
        self.assertEqual(error.code, 400)

    def test_get_payload_email_success(self):
        """Test successful email extraction from payload."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_email

        error, email = get_payload_email(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(email, TEST_EMAIL)

    def test_get_payload_email_missing_returns_empty(self):
        """Test email extraction with missing email field returns empty string."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_email

        error, email = get_payload_email(TEST_CUSTOMER_PAYLOAD_NO_EMAIL)

        # The function returns an empty string instead of an error
        self.assertIsNone(error)
        self.assertEqual(email, "")

    def test_get_payload_name_success(self):
        """Test successful name extraction from payload."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_name

        error, name = get_payload_name(TEST_CUSTOMER_PAYLOAD)

        self.assertIsNone(error)
        self.assertEqual(name, TEST_FULL_NAME)

    def test_get_payload_name_missing(self):
        """Test name extraction with missing name field."""
        from stripe_webhooks.tasks_handlers.getter.get_payload import get_payload_name

        error, name = get_payload_name(TEST_CUSTOMER_PAYLOAD_NO_NAME)

        self.assertIsNotNone(error)
        self.assertIsNone(name)
        self.assertEqual(error.code, 400)


class SimpleSettersTestCase(TestCase):
    """Test case simplifié pour les setters."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)

    def test_create_user_success(self):
        """Test successful user creation."""
        from stripe_webhooks.tasks_handlers.setter.set_user import create_user

        error, user, password = create_user(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            email=TEST_EMAIL,
            language=ENGLISH_LANG_CODE,
            group=self.group,
            is_buyer=True
        )

        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertIsNotNone(password)

        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.email, TEST_EMAIL)
        self.assertEqual(user.language, ENGLISH_LANG_CODE)
        self.assertEqual(user.group_id, self.group.id)
        self.assertTrue(user.username.startswith('lexa'))

    @mock_api_key_generation
    def test_create_userGroup_success(self, mock_requests_post):
        """Test successful user group creation."""
        from stripe_webhooks.tasks_handlers.setter.set_userGroup import create_userGroup

        error, group = create_userGroup("NEW GROUP")

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(group.name, "NEW GROUP")
        # api_key has been moved to UserSubscription; group no longer carries an api_key


class SimpleHelpersTestCase(TestCase):
    """Test case simplifié pour les helpers."""

    def test_string_to_UserSubscriptionChoices_success(self):
        """Test successful conversion of subscription choices."""
        from stripe_webhooks.tasks_handlers.helper.convertor import string_to_UserSubscriptionChoices

        result = string_to_UserSubscriptionChoices('active')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.ACTIVE)

        result = string_to_UserSubscriptionChoices('canceled')
        self.assertEqual(
            result, UserSubscription.UserSubscriptionChoices.TERMINATED)

    def test_dict_to_pair_list_success(self):
        """Test successful conversion of dictionary to pair list."""
        from stripe_webhooks.tasks_handlers.helper.convertor import dict_to_pair_list

        test_dict = {'key1': 'value1', 'key2': 'value2'}
        result = dict_to_pair_list(test_dict)

        expected = [
            {'key': 'key1', 'value': 'value1'},
            {'key': 'key2', 'value': 'value2'}
        ]

        self.assertEqual(len(result), 2)
        self.assertIn({'key': 'key1', 'value': 'value1'}, result)
        self.assertIn({'key': 'key2', 'value': 'value2'}, result)

    def test_group_name_to_user_name_success(self):
        """Test successful conversion of group name to user name."""
        from stripe_webhooks.tasks_handlers.helper.convertor import group_name_to_user_name

        result = group_name_to_user_name("John Doe")
        self.assertEqual(result, ("John", "Doe"))

        result = group_name_to_user_name("John")
        self.assertEqual(result, ("John", ""))


class SimpleFunctionalTestCase(TestCase):
    """Tests fonctionnels de base."""

    def test_error_handling_structure(self):
        """Test basic error handling."""
        from stripe_webhooks.tasks_handlers.error.error import error_message

        error = error_message("not_found_id")

        self.assertIsNotNone(error)
        self.assertEqual(error.code, 400)
        self.assertIsNotNone(error.message)
        self.assertIn("not found", error.message.lower())

    def test_success_case_basic(self):
        """Test basic success case."""
        # Test que les modules peuvent être importés
        try:
            from stripe_webhooks.tasks_handlers.getter import get_data, get_payload
            from stripe_webhooks.tasks_handlers.setter import set_user, set_userGroup
            from stripe_webhooks.tasks_handlers.helper import convertor

            self.assertTrue(True)  # Si on arrive ici, les imports ont réussi
        except ImportError as e:
            self.fail(f"Import failed: {e}")
