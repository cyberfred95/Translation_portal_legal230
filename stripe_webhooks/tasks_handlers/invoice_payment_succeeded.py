"""
Stripe event handler: invoice.payment.succeeded

This handler creates a count history and resets counters for each UserSubscription linked to the Stripe subscription.
For annual Stripe subscriptions, it also resets the cycles_done counter to 0 (12th month renewal).
"""

import logging

from django.db import transaction

from subscriptions.models import UserSubscription

from .error.error import HttpResponse, success_message
from .getter.get_payload import get_payload_customer_id
from .getter.get_data import (
    get_userSubscriptions_list_by_stripe_subscription_id,
    get_user_by_stripe_customer_id,
    get_stripe_subscription_id_from_user
)
from .setter.set_countHistory import reset_subscriptions

logger = logging.getLogger(__name__)


def _reset_cycles_done_for_annual_subscriptions(
    user_subscription_list: list[UserSubscription],
    stripe_subscription_id: str
) -> None:
    """
    Reset cycles_done to 0 for annual Stripe subscriptions.

    This is called during the 12th month renewal when Stripe processes the payment.
    The cycles_done counter tracks monthly renewals (0-11), and is reset to 0
    when the annual subscription is renewed.

    Args:
        user_subscription_list: List of UserSubscription objects to process.
        stripe_subscription_id: Stripe subscription ID for logging purposes.
    """
    try:
        annual_subscriptions = [
            sub for sub in user_subscription_list
            if (sub.stripe_subscription_id and 
                sub.interval == UserSubscription.IntervalChoices.YEAR)
        ]
        
        if not annual_subscriptions:
            return
        
        with transaction.atomic():
            for subscription in annual_subscriptions:
                subscription.cycles_done = 0
                subscription.save(update_fields=["cycles_done"])
    except Exception as error:
        # Log error but don't fail the webhook
        logger.error(
            f"Error resetting cycles_done for subscription {stripe_subscription_id}: {error}"
        )


def handle_invoice_payment_succeeded(payload: dict) -> HttpResponse:
    """
    Handle the Stripe event invoice.payment.succeeded.

    This function retrieves the Stripe customer ID from the payload, gets the buyer user,
    retrieves their subscription ID, fetches all related UserSubscription objects,
    creates a CountHistory record for each, resets their counters, and for annual
    subscriptions, resets the cycles_done counter to 0.

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

    # Reset cycles_done to 0 for annual Stripe subscriptions (12th month renewal)
    _reset_cycles_done_for_annual_subscriptions(
        user_subscription_list,
        stripe_subscription_id
    )

    return success_message(
        "invoice_payment_succeeded",
        stripe_subscription_id=stripe_subscription_id,
        countHistory_count=len(count_history_list)
    )


INVOICE_EVENT_HANDLERS = {
    "invoice.payment_succeeded": handle_invoice_payment_succeeded,
}
