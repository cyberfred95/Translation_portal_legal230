"""
Error and success response utilities.

This module provides classes and functions for creating standardized HTTP responses
for both error and success cases in the Stripe webhook system. It uses predefined
message templates to ensure consistent error reporting across the application.
"""

from .error_messages import ERROR_MESSAGES_TEMPLATE
from .success_messages import SUCCESS_MESSAGES_TEMPLATE


class HttpResponse:
    """
    HTTP response wrapper for webhook operations.

    This class encapsulates HTTP response data including status code,
    message, and optional exception information for error tracking.

    Attributes:
        code (int): HTTP status code.
        message (str): Response message.
        exception (Exception, optional): Associated exception if any.
    """

    def __init__(self, code: int, message: str, exception: Exception = None):
        """
        Initialize HTTP response.

        Args:
            code (int): HTTP status code.
            message (str): Response message.
            exception (Exception, optional): Associated exception. Defaults to None.
        """
        self.code = code
        self.message = message
        self.exception = exception


def success_message(key: str, exception: Exception = None, **kwargs) -> HttpResponse:
    """
    Create a success response using a predefined template.

    This function looks up a success message template by key and formats
    it with the provided keyword arguments to create a standardized
    success response.

    Args:
        key (str): The template key to look up in SUCCESS_MESSAGES_TEMPLATE.
        exception (Exception, optional): Associated exception. Defaults to None.
        **kwargs: Keyword arguments for message formatting.

    Returns:
        HttpResponse: Formatted success response object.
    """
    template = SUCCESS_MESSAGES_TEMPLATE[key]
    message = template["message"].format(**kwargs)
    code = template["code"]
    return HttpResponse(code=code, message=message, exception=exception)


def error_message(key: str, exception: Exception = None, **kwargs) -> HttpResponse:
    """
    Create an error response using a predefined template.

    This function looks up an error message template by key and formats
    it with the provided keyword arguments to create a standardized
    error response.

    Args:
        key (str): The template key to look up in ERROR_MESSAGES_TEMPLATE.
        exception (Exception, optional): Associated exception. Defaults to None.
        **kwargs: Keyword arguments for message formatting.

    Returns:
        HttpResponse: Formatted error response object.
    """
    template = ERROR_MESSAGES_TEMPLATE[key]
    message = template["message"].format(**kwargs)
    code = template["code"]
    return HttpResponse(code=code, message=message, exception=exception)


def exception_error(exception: Exception, **kwargs) -> HttpResponse:
    """
    Create an exception error response with automatic function name detection.

    This utility function simplifies the creation of exception error messages
    by automatically detecting the calling function name and formatting a
    standardized exception error response.

    Args:
        exception (Exception): The exception that occurred.
        **kwargs: Additional keyword arguments for message formatting.

    Returns:
        HttpResponse: Formatted exception error response.
    """
    import inspect

    # Get the calling function name
    function_name = inspect.currentframe().f_back.f_code.co_name

    return error_message(
        "exception",
        function_name=function_name,
        exception=exception,
        **kwargs
    )
