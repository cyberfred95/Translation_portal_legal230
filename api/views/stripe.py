import logging

from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from stripe_webhooks.tasks_handlers.helper.stripe_session import (
    get_stripe_customer_session_url,
    create_stripe_customer_session
)
from ..utils import get_api_user_subscription
from ..stripe_helpers import build_pricing_url_with_client_secret
from subscriptions.models import SubscriptionType

logger = logging.getLogger(__name__)


def _extract_stripe_exception_details(exception: Exception) -> dict:
    """
    Extract detailed information from a Stripe exception.
    
    Args:
        exception: The exception to extract details from.
        
    Returns:
        dict: Dictionary containing exception details.
    """
    details = {}
    
    # Standard exception attributes
    if hasattr(exception, 'user_message'):
        details["stripe_user_message"] = exception.user_message
    if hasattr(exception, 'code'):
        details["stripe_error_code"] = exception.code
    if hasattr(exception, 'param'):
        details["stripe_param"] = exception.param
    if hasattr(exception, 'http_body'):
        details["stripe_http_body"] = exception.http_body
    if hasattr(exception, 'http_status'):
        details["stripe_http_status"] = exception.http_status
    
    # AttributeError specific handling
    if isinstance(exception, AttributeError):
        if hasattr(exception, 'name'):
            details["missing_attribute"] = exception.name
        details["hint"] = (
            "This might indicate that the Stripe API feature is not available. "
            "customer_sessions requires Stripe Python library >= 7.0.0 and "
            "Stripe API version 2024-06-20 or later."
        )
    
    return details


def _build_error_response(error_response, user) -> Response:
    """
    Build a detailed error response from an error_response object.
    
    Args:
        error_response: HttpResponse error object.
        user: User object for logging context.
        
    Returns:
        Response: DRF Response with error details.
    """
    # Log error for debugging
    logger.error(
        "Erreur lors de la création de la session Stripe customer",
        extra={
            "user_id": user.id,
            "stripe_customer_id": user.stripe_customer_id,
            "error_code": error_response.code,
            "error_message": error_response.message,
            "exception": str(error_response.exception) if error_response.exception else None,
        }
    )
    
    # Build base error data
    error_data = {
        "detail": error_response.message,
        "error_code": error_response.code,
    }
    
    # Add exception details if available
    if error_response.exception:
        exception = error_response.exception
        error_data["exception_type"] = type(exception).__name__
        error_data["exception_message"] = str(exception)
        
        # Extract Stripe-specific details
        error_data.update(_extract_stripe_exception_details(exception))
    
    return Response(
        error_data,
        status=status.HTTP_400_BAD_REQUEST
    )


class StripePortalSessionView(APIView):
    # Remove DRF permission classes as we use custom auth
    permission_classes = []

    def get(self, request):
        # Custom authentication using UserSubscription.api_key
        user_subscription, error = get_api_user_subscription(request)
        if error:
            return Response({"detail": error}, status=status.HTTP_401_UNAUTHORIZED)
        
        user = user_subscription.user
        product_type = user_subscription.subscription.product_type
        
        check_only = request.query_params.get('check_only') == 'true'
        
        # For WORD_ADD_IN only
        is_word_add_in = product_type == SubscriptionType.ProductChoices.WORD_ADD_IN
        
        if check_only:
            has_stripe_customer = bool(user.stripe_customer_id)
            return Response(
                {
                    "status": is_word_add_in and has_stripe_customer
                },
                status=status.HTTP_200_OK
            )

        if not is_word_add_in:
            return Response(
                {
                    "detail": "Cette clé API n'est pas associée à un abonnement Word Add-in.",
                    "code": "invalid_product_type"
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if user has a stripe customer id
        if not user.stripe_customer_id:
            return Response(
                {
                    "detail": "Aucun abonnement Stripe associé à ce compte.",
                    "code": "no_stripe_customer"
                }, 
                status=status.HTTP_404_NOT_FOUND
            )

        error_response, portal_url = get_stripe_customer_session_url(user.stripe_customer_id)
        
        if error_response:
            return Response(
                {"detail": "Erreur lors de la création de la session Stripe."}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if portal_url:
            return Response({"url": portal_url}, status=status.HTTP_200_OK)
            
        return Response(
            {"detail": "Erreur inconnue lors de la récupération du lien."}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class StripePricingPageUrlView(APIView):
    """
    API view to generate pricing page URL with Stripe customer session client_secret.
    
    If the user has a stripe_customer_id, creates a Stripe customer session
    and appends the client_secret to the pricing page URL.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        Generate pricing page URL, optionally with Stripe customer session client_secret.
        
        Returns:
            Response: JSON response with 'url' field containing the pricing page URL.
        """
        user = request.user
        base_url = getattr(settings, 'TARIFS_PAGE_URL', None)
        
        if not base_url:
            return Response(
                {"detail": "TARIFS_PAGE_URL n'est pas configuré dans les settings."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        if not user.stripe_customer_id:
            return Response({"url": base_url}, status=status.HTTP_200_OK)
        
        error_response, client_secret = create_stripe_customer_session(
            user.stripe_customer_id
        )
        
        if error_response:
            return _build_error_response(error_response, user)
        
        if not client_secret:
            return Response(
                {"detail": "Impossible de générer le client_secret."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        url_with_secret = build_pricing_url_with_client_secret(base_url, client_secret)
        return Response({"url": url_with_secret}, status=status.HTTP_200_OK)
