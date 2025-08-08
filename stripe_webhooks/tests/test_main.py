"""
Main test runner for stripe_webhooks module.

This module imports all test classes and can be used to run
the complete test suite for stripe_webhooks.
"""

# Import all test cases
from .test_customer_handlers import CustomerHandlersTestCase
from .test_getters import GetDataTestCase, GetPayloadTestCase
from .test_helpers import ConvertorTestCase, StripeSessionTestCase
from .test_integration import StripeWebhooksIntegrationTestCase
from .test_setters import (
    SetUserGroupTestCase,
    SetUserSubscriptionTestCase,
    SetUserTestCase,
)
from .test_subscription_handlers import CustomerSubscriptionHandlersTestCase
from .test_tax_id_handlers import CustomerTaxIdHandlersTestCase
from .test_utils import (
    ErrorHandlingTestCase,
    UtilityFunctionsTestCase,
)

# Test discovery helper


def get_all_test_classes():
    """
    Return a list of all test classes for discovery.

    Returns:
        list: List of all test case classes
    """
    return [
        # Getter tests
        GetDataTestCase,
        GetPayloadTestCase,

        # Setter tests
        SetUserTestCase,
        SetUserGroupTestCase,
        SetUserSubscriptionTestCase,

        # Helper tests
        ConvertorTestCase,
        StripeSessionTestCase,

        # Handler tests
        CustomerHandlersTestCase,
        CustomerSubscriptionHandlersTestCase,
        CustomerTaxIdHandlersTestCase,

        # Integration tests
        StripeWebhooksIntegrationTestCase,

        # Utility tests
        ErrorHandlingTestCase,
        UtilityFunctionsTestCase
    ]


# Test categorization for selective running
GETTER_TESTS = [
    GetDataTestCase,
    GetPayloadTestCase
]

SETTER_TESTS = [
    SetUserTestCase,
    SetUserGroupTestCase,
    SetUserSubscriptionTestCase
]

HELPER_TESTS = [
    ConvertorTestCase,
    StripeSessionTestCase
]

HANDLER_TESTS = [
    CustomerHandlersTestCase,
    CustomerSubscriptionHandlersTestCase,
    CustomerTaxIdHandlersTestCase
]

INTEGRATION_TESTS = [
    StripeWebhooksIntegrationTestCase
]

UTILITY_TESTS = [
    ErrorHandlingTestCase,
    UtilityFunctionsTestCase
]

# Test discovery by category
TEST_CATEGORIES = {
    'getters': GETTER_TESTS,
    'setters': SETTER_TESTS,
    'helpers': HELPER_TESTS,
    'handlers': HANDLER_TESTS,
    'integration': INTEGRATION_TESTS,
    'utils': UTILITY_TESTS
}


def get_tests_by_category(category):
    """
    Get test classes for a specific category.

    Args:
        category (str): Test category name

    Returns:
        list: List of test classes for the category

    Raises:
        ValueError: If category is not found
    """
    if category not in TEST_CATEGORIES:
        available_categories = ', '.join(TEST_CATEGORIES.keys())
        raise ValueError(
            f"Unknown test category '{category}'. "
            f"Available categories: {available_categories}"
        )

    return TEST_CATEGORIES[category]


# Test metadata
TEST_MODULE_INFO = {
    'name': 'stripe_webhooks',
    'description': 'Tests for Stripe webhook handlers and utilities',
    'total_test_classes': len(get_all_test_classes()),
    'categories': list(TEST_CATEGORIES.keys()),
    'version': '1.0.0'
}


def print_test_info():
    """Print information about the test module."""
    info = TEST_MODULE_INFO
    print(f"\n{info['name'].upper()} TEST MODULE")
    print("=" * 50)
    print(f"Description: {info['description']}")
    print(f"Total test classes: {info['total_test_classes']}")
    print(f"Categories: {', '.join(info['categories'])}")
    print(f"Version: {info['version']}")
    print("=" * 50)

    for category, test_classes in TEST_CATEGORIES.items():
        print(f"\n{category.upper()} ({len(test_classes)} classes):")
        for test_class in test_classes:
            print(f"  - {test_class.__name__}")


if __name__ == '__main__':
    # Print test information when run directly
    print_test_info()
