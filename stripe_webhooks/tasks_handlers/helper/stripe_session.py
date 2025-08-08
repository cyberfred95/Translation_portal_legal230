"""
Stripe session management helpers.

This module provides functions for managing Stripe customer portal sessions
and related Stripe API interactions.
"""

import stripe
from django.conf import settings

from ..error.error import HttpResponse, error_message, exception_error


def get_stripe_customer_session_url(customer_id: str) -> tuple[HttpResponse | None, str | None]:
    """
    Create a Stripe customer portal session URL.

    This function creates a Stripe billing portal session for the given customer
    and returns the session URL that allows the customer to manage their billing
    information and subscriptions.

    Args:
        customer_id (str): The Stripe customer identifier.

    Returns:
        tuple[HttpResponse | None, str | None]: Error response and session URL,
        or None and URL on success.
    """
    # Validate customer_id parameter
    if not customer_id:
        return error_message("invalid_customer_id"), None

    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=settings.STRIPE_PORTAL_RETURN_URL,
            api_key=settings.STRIPE_API_KEY
        )
        return None, session.url

    except Exception as error:
        return exception_error(error), None
