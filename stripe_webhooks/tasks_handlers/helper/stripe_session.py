"""
Stripe session management helpers.

This module provides functions for managing Stripe customer portal sessions
and related Stripe API interactions.
"""

import stripe
import requests
from django.conf import settings
from typing import Callable

from ..error.error import HttpResponse, error_message, exception_error


def _validate_customer_id(customer_id: str) -> HttpResponse | None:
    """
    Validate Stripe customer ID.
    
    Args:
        customer_id: The Stripe customer identifier.
        
    Returns:
        HttpResponse | None: Error response if invalid, None if valid.
    """
    if not customer_id:
        return error_message("invalid_customer_id")
    return None


def _execute_stripe_operation(
    operation: Callable[[str], str],
    customer_id: str
) -> tuple[HttpResponse | None, str | None]:
    """
    Execute a Stripe operation with error handling.
    
    Args:
        operation: Stripe API operation function that takes customer_id and returns a string.
        customer_id: The Stripe customer identifier.
        
    Returns:
        tuple[HttpResponse | None, str | None]: Error response and result,
        or None and result on success.
    """
    error_response = _validate_customer_id(customer_id)
    if error_response:
        return error_response, None
    
    try:
        result = operation(customer_id)
        return None, result
    except Exception as error:
        return exception_error(error), None


def _extract_stripe_api_error_detail(http_error: requests.exceptions.HTTPError) -> str:
    """
    Extract error detail from Stripe API HTTP error response.
    
    Args:
        http_error: HTTPError exception from requests.
        
    Returns:
        str: Error detail message.
    """
    if not hasattr(http_error, 'response'):
        return str(http_error)
    
    try:
        error_data = http_error.response.json()
        return error_data.get('error', {}).get('message', str(http_error))
    except (ValueError, KeyError):
        return f"HTTP {http_error.response.status_code}"


def get_stripe_customer_session_url(customer_id: str) -> tuple[HttpResponse | None, str | None]:
    """
    Create a Stripe customer portal session URL.

    This function creates a Stripe billing portal session for the given customer
    and returns the session URL that allows the customer to manage their billing
    information and subscriptions.

    Args:
        customer_id: The Stripe customer identifier.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and session URL,
        or None and URL on success.
    """
    def _create_portal_session(customer_id: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.STRIPE_PORTAL_RETURN_URL,
            api_key=settings.STRIPE_API_KEY
        )
        return session.url
    
    return _execute_stripe_operation(_create_portal_session, customer_id)


def create_stripe_customer_session(customer_id: str) -> tuple[HttpResponse | None, str | None]:
    """
    Create a Stripe customer session for embedded components.
    
    This function creates a Stripe customer session that enables embedded components
    like buy buttons on external pages. The session client_secret can be used
    to authenticate the customer on the pricing page.
    
    Note: This requires Stripe API version 2024-06-20 or later and the customer_sessions
    feature to be enabled in your Stripe account.
    
    Args:
        customer_id: The Stripe customer identifier.
        
    Returns:
        tuple[HttpResponse | None, str | None]: Error response and client_secret,
        or None and client_secret on success.
    """
    def _create_customer_session(customer_id: str) -> str:
        """
        Create a Stripe customer session using REST API directly.
        
        The customer_sessions API is not available in the Python Stripe library yet,
        so we use the REST API directly.
        """
        api_key = settings.STRIPE_API_KEY
        
        if not api_key:
            raise ValueError("STRIPE_API_KEY is not configured")
        
        # Use REST API directly since customer_sessions is not in the Python library
        url = "https://api.stripe.com/v1/customer_sessions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Stripe-Version": "2024-06-20"  # Minimum required version
        }
        data = {
            "customer": customer_id,
            "components[buy_button][enabled]": "true"
        }
        
        try:
            response = requests.post(url, headers=headers, data=data, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if 'client_secret' not in result:
                raise ValueError(f"Response missing client_secret: {result}")
            
            return result['client_secret']
        except requests.exceptions.HTTPError as e:
            error_detail = _extract_stripe_api_error_detail(e)
            raise Exception(
                f"Stripe API error: {error_detail}. "
                f"Status: {e.response.status_code if hasattr(e, 'response') else 'unknown'}"
            ) from e
        except requests.exceptions.RequestException as e:
            raise Exception(f"Failed to connect to Stripe API: {str(e)}") from e
    
    return _execute_stripe_operation(_create_customer_session, customer_id)
