from django.apps import AppConfig


class StripeWebhooksConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'stripe_webhooks'
    verbose_name = 'Stripe Webhooks'
