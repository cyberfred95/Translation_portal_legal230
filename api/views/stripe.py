from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from ..utils import get_api_user

class StripePortalSessionView(APIView):
    # Remove DRF permission classes as we use custom auth
    permission_classes = []

    def get(self, request):
        # Custom authentication using UserSubscription.api_key
        user, error = get_api_user(request)
        if error:
            return Response({"detail": error}, status=status.HTTP_401_UNAUTHORIZED)
        
        check_only = request.query_params.get('check_only') == 'true'
        
        # Check if user has a stripe customer id
        if not user.stripe_customer_id:
            return Response(
                {
                    "detail": "Aucun abonnement Stripe associé à ce compte.",
                    "code": "no_stripe_customer"
                }, 
                status=status.HTTP_404_NOT_FOUND
            )

        if check_only:
            return Response({"status": "active"}, status=status.HTTP_200_OK)

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
