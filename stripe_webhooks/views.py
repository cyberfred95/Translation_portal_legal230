"""
Stripe webhook views.

This module defines the Django views for handling incoming Stripe webhook
requests, including signature verification and event processing delegation.
"""

import stripe
from django.conf import settings
from django.http import HttpResponseForbidden, JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

from .tasks import handle_event


@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(View):
    """
    Django view for handling Stripe webhook requests.

    This view processes incoming Stripe webhook events by:
    1. Verifying the webhook signature for security
    2. Parsing the event payload
    3. Delegating event processing to the appropriate Celery task
    4. Returning a JSON response with the processing result
    """

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests from Stripe webhooks.

        This method validates the webhook signature and processes the event
        by delegating to the handle_event Celery task.

        Args:
            request: The HTTP request object containing the webhook payload.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            JsonResponse: JSON response containing processing result and status.
            HttpResponseForbidden: If signature verification fails.
        """
        # Extract payload and signature from request
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE', '')
        endpoint_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET")

        # Verify webhook signature and construct event
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError:
            # Invalid payload format
            return HttpResponseForbidden("Invalid payload")
        except stripe.error.SignatureVerificationError:
            # Invalid or missing signature
            return HttpResponseForbidden("Invalid signature")

        # Process the event using Celery task
        result = handle_event(event)

        # Return JSON response with processing result
        return JsonResponse({
            "code": result.code,
            "message": result.message,
            "exception": str(result.exception) if result.exception else None
        }, status=result.code, safe=False)
