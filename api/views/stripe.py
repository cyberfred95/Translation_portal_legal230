from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from ..utils import get_api_user_subscription
from subscriptions.models import SubscriptionType

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
                    "status": bool(is_word_add_in and has_stripe_customer)
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
