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


def create_metered_checkout_session(price_id):
    """Create a Stripe Checkout Session for a metered price."""
    success_url, cancel_url = _get_checkout_urls()
    return stripe.checkout.Session.create(
        mode='subscription',
        line_items=[{'price': price_id}],
        success_url=success_url,
        cancel_url=cancel_url,
        api_key=settings.STRIPE_API_KEY,
    )


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

