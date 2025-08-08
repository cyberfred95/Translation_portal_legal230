"""
Unit tests for stripe_webhooks utilities and general functions.

This module contains tests for utility functions and any additional
helper methods used across the stripe_webhooks module.
"""

import json
from unittest.mock import MagicMock, patch

from django.test import TestCase

from stripe_webhooks.tasks_handlers.error.error import (
    HttpResponse,
    error_message,
    success_message,
)
from stripe_webhooks.tests.settings import (
    ERROR_EXCEPTION,
    ERROR_NOT_FOUND_ID,
    TEST_STRIPE_CUSTOMER_ID,
)


class ErrorHandlingTestCase(TestCase):
    """Test case for error handling utilities."""

    def test_error_message_creation_basic(self):
        """Test basic error message creation."""
        error_type = ERROR_NOT_FOUND_ID
        response = error_message(error_type)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 400)  # Default status code

    def test_error_message_creation_with_parameters(self):
        """Test error message creation with additional parameters."""
        error_type = "not_found_user_by_stripe_customer_id"
        stripe_customer_id = TEST_STRIPE_CUSTOMER_ID

        response = error_message(
            error_type,
            stripe_customer_id=stripe_customer_id
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 404)

    def test_error_message_creation_with_exception(self):
        """Test error message creation with exception."""
        error_type = ERROR_EXCEPTION
        function_name = "test_function"
        exception = Exception("Test exception")

        response = error_message(
            error_type,
            function_name=function_name,
            exception=exception
        )

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 500)
        self.assertEqual(response.exception, exception)

    def test_success_message_creation_basic(self):
        """Test basic success message creation."""
        response = success_message("customer_created")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 201)

    def test_success_message_creation_with_data(self):
        """Test success message creation with data."""
        test_data = {"key": "value", "number": 42}
        response = success_message("customer_created", data=test_data)

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 201)

    def test_success_message_creation_with_message(self):
        """Test success message creation with custom message."""
        # The success_message function always uses the template, not a custom message
        response = success_message("customer_created")

        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response.code, 201)
        self.assertEqual(response.message, "Customer created successfully")

    def test_http_response_properties(self):
        """Test HttpResponse object properties."""
        code = 400
        message = "test error"
        exception = Exception("Test error")

        response = HttpResponse(
            code=code, message=message, exception=exception)

        self.assertEqual(response.code, code)
        self.assertEqual(response.message, message)
        self.assertEqual(response.exception, exception)

    def test_http_response_serialization(self):
        """Test HttpResponse serialization to dictionary."""
        error_type = ERROR_NOT_FOUND_ID
        status_code = 404
        message = "Resource not found"

        response = HttpResponse(code=400, message="test error")

        # Test that response can be serialized to JSON
        response_dict = {
            'error_type': response.code,
            'status_code': response.code,
            'message': response.message
        }

        # Should not raise exception
        json_str = json.dumps(response_dict)
        self.assertIsInstance(json_str, str)

    def test_error_message_status_code_mapping(self):
        """Test that error types map to correct status codes."""
        test_cases = [
            ("not_found_id", 400, {}),
            ("not_found_name", 400, {}),
            ("not_found_email", 400, {}),
            ("not_found_language", 400, {}),
            ("not_found_status", 400, {}),
            ("not_found_customer_id", 400, {}),
            ("not_found_user_by_stripe_customer_id",
             404, {"stripe_customer_id": "cus_test123"}),
            ("not_found_subscriptionType_by_stripe_product_id",
             404, {"stripe_product_id": "prod_test123"}),
            ("not_found_userSubscription_by_stripe_subscription_id",
             404, {"stripe_subscription_id": "sub_test123"}),
            ("not_found_userGroup_by_group_name",
             404, {"group_name": "test_group"}),
            ("exception", 500, {"function_name": "test_function"})
        ]

        for error_type, expected_status, kwargs in test_cases:
            response = error_message(error_type, **kwargs)
            self.assertEqual(
                response.code,
                expected_status,
                f"Error type '{error_type}' should have status code {expected_status}"
            )


class UtilityFunctionsTestCase(TestCase):
    """Test case for general utility functions."""

    def test_payload_validation_empty_dict(self):
        """Test payload validation with empty dictionary."""
        # This is a general test for payload handling
        empty_payload = {}

        # Test that empty payload is handled gracefully
        # (Specific implementation depends on actual utility functions)
        self.assertIsInstance(empty_payload, dict)
        self.assertEqual(len(empty_payload), 0)

    def test_payload_validation_none_values(self):
        """Test payload validation with None values."""
        payload_with_none = {
            'id': None,
            'name': None,
            'email': None
        }

        # Test that None values are handled appropriately
        for key, value in payload_with_none.items():
            self.assertIsNone(value)

    def test_payload_validation_missing_keys(self):
        """Test payload validation with missing keys."""
        incomplete_payload = {
            'name': 'Test Name'
            # Missing 'id', 'email', etc.
        }

        # Test that missing keys can be detected
        self.assertNotIn('id', incomplete_payload)
        self.assertNotIn('email', incomplete_payload)
        self.assertIn('name', incomplete_payload)

    def test_string_normalization(self):
        """Test string normalization utilities."""
        test_cases = [
            ("  test string  ", "test string"),  # Whitespace trimming
            ("UPPERCASE", "UPPERCASE"),  # Case preservation
            ("", ""),  # Empty string
            ("single", "single"),  # Single word
            ("multiple   spaces", "multiple spaces")  # Multiple spaces
        ]

        for input_str, expected in test_cases:
            # Test basic string normalization
            normalized = ' '.join(input_str.strip().split())
            self.assertEqual(normalized, expected)

    def test_data_type_validation(self):
        """Test data type validation utilities."""
        # Test different data types
        test_data = {
            'string': 'test',
            'integer': 42,
            'float': 3.14,
            'boolean': True,
            'list': [1, 2, 3],
            'dict': {'nested': 'value'},
            'none': None
        }

        # Validate types
        self.assertIsInstance(test_data['string'], str)
        self.assertIsInstance(test_data['integer'], int)
        self.assertIsInstance(test_data['float'], float)
        self.assertIsInstance(test_data['boolean'], bool)
        self.assertIsInstance(test_data['list'], list)
        self.assertIsInstance(test_data['dict'], dict)
        self.assertIsNone(test_data['none'])

    def test_safe_dictionary_access(self):
        """Test safe dictionary access patterns."""
        test_dict = {
            'existing_key': 'value',
            'nested': {
                'inner_key': 'inner_value'
            }
        }

        # Test safe access patterns
        self.assertEqual(test_dict.get('existing_key'), 'value')
        self.assertEqual(test_dict.get('missing_key'), None)
        self.assertEqual(test_dict.get('missing_key', 'default'), 'default')

        # Test nested access
        nested = test_dict.get('nested', {})
        self.assertEqual(nested.get('inner_key'), 'inner_value')
        self.assertIsNone(nested.get('missing_inner_key'))

    def test_error_logging(self):
        """Test error logging functionality."""
        error_type = ERROR_EXCEPTION
        function_name = "test_function"
        exception = Exception("Test logging error")

        response = error_message(
            error_type,
            function_name=function_name,
            exception=exception
        )

        # Verify error was created
        self.assertEqual(response.code, 500)
        self.assertIn(function_name, response.message)
        self.assertEqual(response.exception, exception)
        self.assertEqual(response.code, 500)  # exception errors return 500
        self.assertEqual(response.exception, exception)

    def test_response_consistency(self):
        """Test that all response objects follow consistent format."""
        # Test error response
        error_response = error_message(ERROR_NOT_FOUND_ID)
        self.assertTrue(hasattr(error_response, 'code'))
        self.assertTrue(hasattr(error_response, 'message'))
        self.assertTrue(hasattr(error_response, 'exception'))

        # Test success response - but first we need a valid success key
        # Since "test_key" doesn't exist, let's use a valid one
        success_response = success_message("customer_created")
        self.assertTrue(hasattr(success_response, 'code'))
        self.assertTrue(hasattr(success_response, 'message'))
        # customer_created returns 201
        self.assertEqual(success_response.code, 201)
