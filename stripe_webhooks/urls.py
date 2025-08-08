"""
URL configuration for Stripe webhooks.

This module defines the URL patterns for Stripe webhook endpoints,
mapping webhook requests to the appropriate view handlers.
"""

from django.urls import path

from .views import StripeWebhookView

urlpatterns = [
    path('', StripeWebhookView.as_view(), name='stripe-webhook'),
]
