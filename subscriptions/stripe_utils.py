import stripe
from django.conf import settings


class StripeCheckoutConfigurationError(Exception):
    """Raised when Stripe Checkout URLs are missing."""

    pass


def _get_checkout_urls():
    """Return success/cancel URLs or raise if missing."""
    success_url = getattr(settings, 'STRIPE_CHECKOUT_SUCCESS_URL', '')
    cancel_url = getattr(settings, 'STRIPE_CHECKOUT_CANCEL_URL', '')
    if not success_url or not cancel_url:
        raise StripeCheckoutConfigurationError(
            "Les URLs de retour Stripe ne sont pas configurées."
        )
    return success_url, cancel_url


def create_metered_checkout_session(price_id, with_serpa=True):
    """
    Create a Stripe Checkout Session for a metered price.
    
    Args:
        price_id: The Stripe price ID
        with_serpa: If True, requires payment method collection (default: True)
                    If False, skips payment method collection (no banking details)
    """
    success_url, cancel_url = _get_checkout_urls()
    session_params = {
        'mode': 'subscription',
        'line_items': [{'price': price_id}],
        'success_url': success_url,
        'cancel_url': cancel_url,
        'billing_address_collection': 'required',
        'api_key': settings.STRIPE_API_KEY,
    }
    
    if not with_serpa:
        # Skip payment method collection for subscriptions sans coordonnées bancaires
        session_params['payment_method_collection'] = 'if_required'
    
    return stripe.checkout.Session.create(**session_params)


def list_active_stripe_prices(product_id):
    """Return formatted active prices for a given product."""
    response = stripe.Price.list(
        product=product_id,
        limit=50,
        active=True,
        api_key=settings.STRIPE_API_KEY,
    )
    prices = getattr(response, 'data', [])
    return [
        {
            'id': price.id,
            'nickname': getattr(price, 'nickname', '') or '',
            'currency': getattr(price, 'currency', '') or '',
        }
        for price in prices
    ]

