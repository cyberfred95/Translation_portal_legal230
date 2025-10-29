"""
Utilities for subscription management and API key handling.
"""

from subscriptions.models import UserSubscription, SubscriptionType
from django.utils.timezone import now


def get_user_api_key(user):
    """
    Retourne la clé API depuis la UserSubscription active de l'utilisateur.
    Lève ValueError si aucune souscription active valide n'est trouvée.
    """
    # If the user has any subscription explicitly without API key, consider as no valid subscription
    if UserSubscription.objects.filter(user=user, api_key__isnull=True).exists():
        raise ValueError("no subscription")
    subscriptions = UserSubscription.objects.filter(user=user, api_key__isnull=False)

    for subscription in subscriptions:
        try:
            if (
                subscription.is_active()
                and subscription.end_date and subscription.end_date > now()
                and subscription.api_key
                and subscription.subscription.product_type in [
                    SubscriptionType.ProductChoices.LEXA,
                    SubscriptionType.ProductChoices.WORD_ADD_IN,
                    SubscriptionType.ProductChoices.API,
                ]
            ):
                return subscription.api_key
        except Exception:
            continue

    raise ValueError("no subscription")

