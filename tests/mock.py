"""
Centralized mock utilities for tests.

This module contains shared mock functions and decorators used across all test files
to ensure consistency and avoid external API calls during testing.
"""

from unittest.mock import Mock, patch
from functools import wraps


# Common mock configurations
def _create_mock_settings():
    """Create a mock settings object with standard configuration."""
    import os
    mock_settings = Mock()
    mock_settings.CUSTOM_MT_CONSOLE_URL = os.environ.get('CUSTOM_MT_CONSOLE_URL')
    if not mock_settings.CUSTOM_MT_CONSOLE_URL:
        raise ValueError("CUSTOM_MT_CONSOLE_URL environment variable is required for tests")
    mock_settings.api_key = 'main-api-key-123'
    return mock_settings


def _create_mock_api_response(api_key, success=True):
    """Create a mock API response object."""
    mock_response = Mock()
    if success:
        mock_response.status_code = 200
        mock_response.json.return_value = {'api_key': api_key}
    else:
        mock_response.status_code = 400
        mock_response.text = 'Bad Request'
    return mock_response


def _api_key_decorator_base(test_func, api_key, success=True, silent=False, with_requests=True):
    """Base decorator logic for API key mocking to reduce code duplication."""
    # Cette fonction n'est plus utilisée - on garde les décorateurs séparés pour maintenir les signatures
    pass


def mock_api_key_generation(api_key='test-api-key-mock'):
    """
    Decorator to mock API key generation for UserGroup creation.
    
    Args:
        api_key: The API key to return in the mock response
    """
    def decorator(test_func):
        @wraps(test_func)
        @patch('subscriptions.models.requests.post')
        def wrapper(self, mock_post, *args, **kwargs):
            # Use shared configuration functions
            mock_post.return_value = _create_mock_api_response(api_key, success=True)
            
            # Pass mocks to the test function
            return test_func(self, mock_post, *args, **kwargs)
        return wrapper
    return decorator


def mock_api_key_generation_silent(api_key='test-api-key-silent'):
    """
    Decorator to mock API key generation silently (suppresses all console output).
    This is useful for integration tests where we don't want to see API generation messages.
    
    Args:
        api_key: The API key to return in the mock response
    """
    def decorator(test_func):
        @wraps(test_func)
        @patch('subscriptions.models.requests.post')
        @patch('builtins.print')  # Suppress print statements
        def wrapper(self, mock_print, mock_post, *args, **kwargs):
            # Use shared configuration functions
            mock_post.return_value = _create_mock_api_response(api_key, success=True)
            
            # Pass mocks to the test function
            return test_func(self, mock_post, *args, **kwargs)
        return wrapper
    return decorator


def mock_api_key_generation_failure():
    """
    Decorator to mock API key generation failure (for testing UUID fallback).
    Suppresses console output for clean test results.
    """
    def decorator(test_func):
        @wraps(test_func)
        @patch('subscriptions.models.requests.post')
        @patch('builtins.print')  # Suppress print statements
        def wrapper(self, mock_print, mock_post, *args, **kwargs):
            # Use shared configuration functions
            mock_post.return_value = _create_mock_api_response('', success=False)
            
            # Pass mocks to the test function
            return test_func(self, mock_post, *args, **kwargs)
        return wrapper
    return decorator


def mock_no_settings():
    """
    Decorator to mock when main settings are not available.
    Suppresses console output for clean test results.
    """
    def decorator(test_func):
        @wraps(test_func)
        @patch('builtins.print')  # Suppress print statements
        def wrapper(self, mock_print, *args, **kwargs):
            # Pass mock to the test function
            return test_func(self, *args, **kwargs)
        return wrapper
    return decorator


def create_test_user_group(name='Test Group'):
    """
    Helper function to create a UserGroup for testing.
    Note: API keys are now stored in UserSubscription, not UserGroup.
    
    Args:
        name: The name of the group
        
    Returns:
        UserGroup: The created group
    """
    from users.models import UserGroup
    return UserGroup.objects.create(name=name)


def create_test_user_subscription(user, subscription_type, api_key='test-api-key'):
    """
    Helper function to create a UserSubscription with an API key for testing.
    
    Args:
        user: The user instance
        subscription_type: The subscription type instance
        api_key: The API key to assign
        
    Returns:
        UserSubscription: The created subscription
    """
    from subscriptions.models import UserSubscription
    from django.utils.timezone import now
    from datetime import timedelta
    
    return UserSubscription.objects.create(
        user=user,
        subscription=subscription_type,
        status=UserSubscription.UserSubscriptionChoices.ACTIVE,
        api_key=api_key,
        start_date=now(),
        end_date=now() + timedelta(days=30)
    )


def suppress_api_calls(test_class):
    """
    Class decorator to suppress API key generation calls and their output.
    Apply this decorator to test classes that create UserGroups.
    
    Usage:
        @suppress_api_calls
        class MyTestCase(TestCase):
            ...
    """
    # Store original setUp and tearDown methods
    original_setUp = test_class.setUp if hasattr(test_class, 'setUp') else None
    original_tearDown = test_class.tearDown if hasattr(test_class, 'tearDown') else None
    
    def new_setUp(self):
        """Enhanced setUp with API mocking."""
        # Call original setUp first
        if original_setUp:
            original_setUp(self)
        
        # Start the patches
        self._api_patcher_requests = patch('subscriptions.models.requests.post')
        self._api_patcher_print = patch('builtins.print')
        
        # Start all patches
        self._api_mock_post = self._api_patcher_requests.start()
        self._api_mock_print = self._api_patcher_print.start()
        
        # Use common mock setup functions
        self._api_mock_post.return_value = _create_mock_api_response('test-mocked-api-key')
    
    def new_tearDown(self):
        """Enhanced tearDown with patch cleanup."""
        # Stop patches first
        for patcher_name in ['_api_patcher_requests', '_api_patcher_print']:
            if hasattr(self, patcher_name):
                getattr(self, patcher_name).stop()
        
        # Call original tearDown
        if original_tearDown:
            original_tearDown(self)
    
    # Replace methods
    test_class.setUp = new_setUp
    test_class.tearDown = new_tearDown
    
    return test_class
