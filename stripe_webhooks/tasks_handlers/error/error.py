"""
Error and success response utilities.

This module provides classes and functions for creating standardized HTTP responses
for both error and success cases in the Stripe webhook system. It uses predefined
message templates to ensure consistent error reporting across the application.
"""

import inspect
from typing import Optional

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

    def __init__(
        self, code: int, message: str, exception: Optional[Exception] = None
    ):
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


def _create_response_from_template(
    template_dict: dict[str, dict[str, str | int]],
    key: str,
    exception: Optional[Exception] = None,
    **kwargs
) -> HttpResponse:
    """
    Create an HTTP response from a template dictionary.

    This internal function extracts the common logic for creating responses
    from predefined templates, reducing code duplication.

    Args:
        template_dict: Dictionary containing message templates.
        key: The template key to look up.
        exception: Optional exception to associate with the response.
        **kwargs: Keyword arguments for message formatting.

    Returns:
        HttpResponse: Formatted response object.

    Raises:
        KeyError: If the template key is not found.
    """
    template = template_dict[key]
    formatted_message = template["message"].format(**kwargs)
    status_code = template["code"]
    return HttpResponse(code=status_code, message=formatted_message, exception=exception)


def success_message(
    key: str, exception: Optional[Exception] = None, **kwargs
) -> HttpResponse:
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
    return _create_response_from_template(
        SUCCESS_MESSAGES_TEMPLATE, key, exception, **kwargs
    )


def error_message(
    key: str, exception: Optional[Exception] = None, **kwargs
) -> HttpResponse:
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
    return _create_response_from_template(
        ERROR_MESSAGES_TEMPLATE, key, exception, **kwargs
    )


def _get_calling_function_name() -> str:
    """
    Get the name of the function that called the current function.

    Returns:
        str: The name of the calling function.
    """
    frame = inspect.currentframe()
    if frame is None or frame.f_back is None:
        return "unknown"
    return frame.f_back.f_code.co_name


def _extract_exception_details(exception: Exception) -> tuple[str, str]:
    """
    Extract type and message from an exception.

    Args:
        exception: The exception to extract details from.

    Returns:
        tuple[str, str]: A tuple containing (exception_type, exception_message).
    """
    exception_type = type(exception).__name__
    exception_message = str(exception) or "No error message available"
    return exception_type, exception_message


def exception_error(exception: Exception, **kwargs) -> HttpResponse:
    """
    Create an exception error response with automatic function name detection.

    This utility function simplifies the creation of exception error messages
    by automatically detecting the calling function name and formatting a
    standardized exception error response with exception details.

    Args:
        exception (Exception): The exception that occurred.
        **kwargs: Additional keyword arguments for message formatting.

    Returns:
        HttpResponse: Formatted exception error response containing:
            - The name of the function where the exception occurred
            - The exception type
            - The exception message
    """
    function_name = _get_calling_function_name()
    exception_type, exception_message = _extract_exception_details(exception)

    return error_message(
        "exception",
        function_name=function_name,
        exception_type=exception_type,
        exception_message=exception_message,
        exception=exception,
        **kwargs
    )
