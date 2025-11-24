"""
Unit tests for stripe_webhooks setter utilities.

This module contains tests for setter functions used to create and modify
users, user groups, and user subscriptions.
"""

from unittest.mock import MagicMock, patch, Mock

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from stripe_webhooks.tasks_handlers.setter.set_user import (
    create_user,
    deactivate_user,
)
from stripe_webhooks.tasks_handlers.setter.set_userGroup import (
    create_userGroup,
    create_userGroup_if_not_exists,
)
from stripe_webhooks.tasks_handlers.setter.set_userSubscription import (
    create_userSubscriptions,
    deactivate_userSubscription,
    set_new_userSubscription_list_values,
)
from stripe_webhooks.tests.settings import (
    ENGLISH_LANG_CODE,
    GROUP_ALREADY_EXISTS,
    GROUP_NEWLY_CREATED,
    MAX_PASSWORD_LENGTH,
    MIN_PASSWORD_LENGTH,
    SUBSCRIPTION_STATUS_ACTIVE,
    SUBSCRIPTION_STATUS_CANCELED,
    TEST_API_KEY,
    TEST_EMAIL,
    TEST_GROUP_NAME,
    TEST_PASSWORD,
    TEST_STRIPE_CUSTOMER_ID,
    TEST_STRIPE_PRODUCT_ID,
    TEST_STRIPE_SUBSCRIPTION_ID,
    TEST_SUBSCRIPTION_NAME,
    TEST_SUBSCRIPTION_PRICE,
    TEST_USERNAME,
)
from subscriptions.models import SubscriptionType, UserSubscription
from users.models import User, UserGroup
from tests.mock import create_test_user_group, mock_api_key_generation


class SetUserTestCase(TestCase):
    """Test case for set_user functions."""

    def setUp(self):
        """Set up test data."""
        self.group = create_test_user_group(name=TEST_GROUP_NAME)

    def test_create_user_success_with_all_data(self):
        """Test successful user creation with all data provided."""
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

        # Check user data
        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)
        self.assertEqual(user.email, TEST_EMAIL)
        self.assertEqual(user.language, ENGLISH_LANG_CODE)
        self.assertEqual(user.group_id, self.group.id)
        self.assertTrue(user.username.startswith('lexa'))

        # Check password
        self.assertGreaterEqual(len(password), MIN_PASSWORD_LENGTH)
        self.assertLessEqual(len(password), MAX_PASSWORD_LENGTH)
        self.assertTrue(user.check_password(password))

    def test_create_user_success_minimal_data(self):
        """Test successful user creation with minimal data."""
        error, user, password = create_user(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            is_buyer=True
        )

        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertIsNotNone(password)

        # Check user data
        self.assertEqual(user.stripe_customer_id, TEST_STRIPE_CUSTOMER_ID)
        # Django User model sets email to empty string by default
        self.assertEqual(user.email, '')
        self.assertEqual(user.language, 'en')  # Default language from settings
        self.assertIsNone(user.group_id)

    def test_create_user_not_buyer(self):
        """Test user creation when is_buyer is False."""
        error, user, password = create_user(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            email=TEST_EMAIL,
            is_buyer=False
        )

        self.assertIsNone(error)
        self.assertIsNotNone(user)
        self.assertIsNone(user.stripe_customer_id)

    def test_create_user_duplicate_username_handling(self):
        """Test username conflict resolution."""
        # Create first user
        error1, user1, password1 = create_user(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            is_buyer=True
        )

        # Create second user with same stripe_customer_id pattern
        stripe_id_2 = TEST_STRIPE_CUSTOMER_ID  # Same pattern to test username increment
        error2, user2, password2 = create_user(
            # Slightly different to avoid DB constraint
            stripe_customer_id=stripe_id_2 + "x",
            is_buyer=True
        )

        self.assertIsNone(error1)
        self.assertIsNone(error2)
        self.assertNotEqual(user1.username, user2.username)

    @patch('stripe_webhooks.tasks_handlers.setter.set_user.User.objects.create')
    def test_create_user_exception_handling(self, mock_create):
        """Test exception handling during user creation."""
        mock_create.side_effect = Exception("Database error")

        error, user, password = create_user(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            is_buyer=True
        )

        self.assertIsNotNone(error)
        self.assertIsNone(user)
        self.assertIsNone(password)
        self.assertEqual(error.code, 500)  # exception code

    def test_deactivate_user_success(self):
        """Test successful user deactivation."""
        # Create user
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        user.group = self.group
        user.is_active = True
        user.save()

        # Add user as admin
        self.group.admin.add(user)

        # Deactivate user
        error = deactivate_user(user)

        self.assertIsNone(error)

        # Check user is deactivated
        user.refresh_from_db()
        self.assertFalse(user.is_active)

        # Check user is removed from admin
        self.assertNotIn(user, self.group.admin.all())

    def test_deactivate_user_not_admin(self):
        """Test user deactivation when user is not admin."""
        # Create user
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )
        user.group = self.group
        user.is_active = True
        user.save()

        # Deactivate user (not an admin)
        error = deactivate_user(user)

        self.assertIsNone(error)

        # Check user is deactivated
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    @patch('stripe_webhooks.tasks_handlers.setter.set_user.User.save')
    def test_deactivate_user_exception_handling(self, mock_save):
        """Test exception handling during user deactivation."""
        user = User.objects.create_user(
            username=TEST_USERNAME,
            email=TEST_EMAIL,
            password=TEST_PASSWORD
        )

        mock_save.side_effect = Exception("Database error")

        error = deactivate_user(user)

        self.assertIsNotNone(error)
        self.assertEqual(error.code, 500)  # exception code


class SetUserGroupTestCase(TestCase):
    """Test case for set_userGroup functions."""

    def test_create_userGroup_success(self):
        """Test successful user group creation."""
        
        error, group = create_userGroup(TEST_GROUP_NAME)

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(group.name, TEST_GROUP_NAME)
        # Plus de génération d'API key au niveau du groupe

    @patch('stripe_webhooks.tasks_handlers.setter.set_userGroup.UserGroup.objects.create')
    def test_create_userGroup_exception_handling(self, mock_create):
        """Test exception handling during user group creation."""
        mock_create.side_effect = Exception("Database error")

        error, group = create_userGroup(TEST_GROUP_NAME)

        self.assertIsNotNone(error)
        self.assertIsNone(group)
        self.assertEqual(error.code, 500)  # exception code

    @mock_api_key_generation()
    def test_create_userGroup_if_not_exists_new_group(self, mock_post):
        """Test creating user group when it doesn't exist."""
        
        error, group, is_found = create_userGroup_if_not_exists(
            TEST_GROUP_NAME.lower())

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(is_found, GROUP_NEWLY_CREATED)
        self.assertEqual(group.name, TEST_GROUP_NAME)  # Should be uppercase

    def test_create_userGroup_if_not_exists_existing_group(self):
        """Test creating user group when it already exists."""
        # Create existing group
        existing_group = create_test_user_group(name=TEST_GROUP_NAME)

        error, group, is_found = create_userGroup_if_not_exists(
            TEST_GROUP_NAME.lower())

        self.assertIsNone(error)
        self.assertIsNotNone(group)
        self.assertEqual(is_found, GROUP_ALREADY_EXISTS)
        self.assertEqual(group.id, existing_group.id)

    @patch('stripe_webhooks.tasks_handlers.setter.set_userGroup.get_userGroup_by_group_name')
    def test_create_userGroup_if_not_exists_exception_in_get(self, mock_get):
        """Test exception handling in get_userGroup_by_group_name."""
        # Mock exception in get function
        mock_error = MagicMock()
        mock_error.exception = Exception("Database error")
        mock_get.return_value = (mock_error, None)

        error, group, is_found = create_userGroup_if_not_exists(
            TEST_GROUP_NAME)

        self.assertIsNotNone(error)
        self.assertIsNone(group)
        self.assertIsNone(is_found)

    @patch('stripe_webhooks.tasks_handlers.setter.set_userGroup.create_userGroup')
    @patch('stripe_webhooks.tasks_handlers.setter.set_userGroup.get_userGroup_by_group_name')
    def test_create_userGroup_if_not_exists_exception_in_create(self, mock_get, mock_create):
        """Test exception handling in create_userGroup."""
        # Mock not found in get
        mock_error_not_found = MagicMock()
        mock_error_not_found.exception = None
        mock_get.return_value = (mock_error_not_found, None)

        # Mock exception in create
        mock_error_create = MagicMock()
        mock_error_create.exception = Exception("Database error")
        mock_create.return_value = (mock_error_create, None)

        error, group, is_found = create_userGroup_if_not_exists(
            TEST_GROUP_NAME)

        self.assertIsNotNone(error)
        self.assertIsNone(group)
        self.assertIsNone(is_found)


class SetUserSubscriptionTestCase(TestCase):
    """Test case for set_userSubscription functions."""

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

    def test_create_userSubscriptions_success(self):
        """Test successful user subscriptions creation."""
        from datetime import datetime, timezone

        start_date = datetime.now(timezone.utc)
        end_date = datetime.now(timezone.utc)

        error, subscriptions = create_userSubscriptions(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            subscription_type=self.subscription_type,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            stripe_subscription_item_id="si_test",
            start_time=start_date,
            end_time=end_date,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            buyer=self.user,
            is_buying=True,
            quantity=1
        )

        self.assertIsNone(error)
        self.assertIsNotNone(subscriptions)
        self.assertEqual(len(subscriptions), 1)
        subscription = subscriptions[0]
        self.assertEqual(subscription.user, self.user)
        self.assertEqual(subscription.subscription, self.subscription_type)
        self.assertEqual(subscription.stripe_subscription_id,
                         TEST_STRIPE_SUBSCRIPTION_ID)
        self.assertEqual(subscription.status, SUBSCRIPTION_STATUS_ACTIVE)

    @patch('stripe_webhooks.tasks_handlers.setter.set_userSubscription.UserSubscription.objects.create')
    def test_create_userSubscriptions_exception_handling(self, mock_create):
        """Test exception handling during user subscriptions creation."""
        mock_create.side_effect = Exception("Database error")

        from datetime import datetime, timezone
        start_date = datetime.now(timezone.utc)
        end_date = datetime.now(timezone.utc)

        error, subscriptions = create_userSubscriptions(
            stripe_customer_id=TEST_STRIPE_CUSTOMER_ID,
            subscription_type=self.subscription_type,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            stripe_subscription_item_id="si_test",
            start_time=start_date,
            end_time=end_date,
            status=SUBSCRIPTION_STATUS_ACTIVE,
            buyer=self.user,
            is_buying=True,
            quantity=1
        )

        self.assertIsNotNone(error)
        self.assertIsNone(subscriptions)
        self.assertEqual(error.code, 500)  # exception code

    def test_set_new_userSubscription_list_values_success(self):
        """Test successful user subscription values update."""
        # Create subscription
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        from datetime import datetime
        from datetime import timezone as dt_timezone
        new_end_date = datetime.now(dt_timezone.utc)
        new_values = {
            'end_date': new_end_date,
            'status': SUBSCRIPTION_STATUS_CANCELED,
            'stripe_subscription_item_id': "si_updated",
        }

        error, email_types, changed = set_new_userSubscription_list_values(
            [subscription], new_values
        )

        self.assertIsNone(error)
        self.assertTrue(changed)
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, SUBSCRIPTION_STATUS_CANCELED)

    def test_deactivate_userSubscription_success(self):
        """Test successful user subscription deactivation."""
        # Create active subscription
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            stripe_subscription_id=TEST_STRIPE_SUBSCRIPTION_ID,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date=timezone.now(),
            end_date=timezone.now())

        from datetime import datetime
        from datetime import timezone as dt_timezone
        cancel_at = datetime.now(dt_timezone.utc)

        error, deactivated = deactivate_userSubscription(
            subscription, cancel_at)

        self.assertIsNone(error)
        # The specific behavior depends on the implementation
