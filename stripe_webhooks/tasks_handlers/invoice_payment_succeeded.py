
"""
Stripe event handler: invoice.payment.succeeded

This handler creates a count history and resets counters for each UserSubscription linked to the Stripe subscription.
"""

from .error.error import HttpResponse, success_message
from .getter.get_payload import get_payload_customer_id
from .getter.get_data import (
    get_userSubscriptions_list_by_stripe_subscription_id,
    get_user_by_stripe_customer_id,
    get_stripe_subscription_id_from_user
)
from .setter.set_countHistory import reset_subscriptions


def handle_invoice_payment_succeeded(payload: dict) -> HttpResponse:
    """
    Handle the Stripe event invoice.payment.succeeded.

    This function retrieves the Stripe customer ID from the payload, gets the buyer user,
    retrieves their subscription ID, fetches all related UserSubscription objects,
    creates a CountHistory record for each, resets their counters, and returns a success message or error.

    Args:
        payload (dict): The payload sent by Stripe.

    Returns:
        HttpResponse: HTTP response containing the result of the operation.
    """
    error_response, stripe_customer_id = get_payload_customer_id(payload)
    if error_response:
        return error_response

    error_response, buyer = get_user_by_stripe_customer_id(stripe_customer_id)
    if error_response:
        return error_response

    error_response, stripe_subscription_id = get_stripe_subscription_id_from_user(
        buyer)
    if error_response:
        return error_response

    error_response, user_subscription_list = get_userSubscriptions_list_by_stripe_subscription_id(
        stripe_subscription_id)
    if error_response:
        return error_response

    error_response, count_history_list = reset_subscriptions(
        user_subscription_list)
    if error_response:
        return error_response

    return success_message(
        "invoice_payment_succeeded",
        stripe_subscription_id=stripe_subscription_id,
        countHistory_count=len(count_history_list)
    )


INVOICE_EVENT_HANDLERS = {
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
}
