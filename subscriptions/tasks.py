"""
Celery tasks for subscription management.

This module contains scheduled tasks for managing user subscriptions,
including daily renewal processing for non-Stripe subscriptions.
"""

import calendar
import logging
from datetime import datetime
from celery import shared_task
from django.utils import timezone
from django.db import transaction

from .models import UserSubscription
from .permissions import is_user_subscription_active
from stripe_webhooks.tasks_handlers.setter.set_countHistory import reset_subscriptions
from .services.metered_usage import report_metered_usage_to_stripe

logger = logging.getLogger(__name__)


def add_one_month_safely(date_value: datetime) -> datetime:
    """
    Ajoute un mois en conservant un jour valide (ex: 31 -> 30 si mois suivant plus court).
    """
    if date_value.month == 12:
        target_year = date_value.year + 1
        target_month = 1
    else:
        target_year = date_value.year
        target_month = date_value.month + 1

    _, last_day = calendar.monthrange(target_year, target_month)
    target_day = min(date_value.day, last_day)
    return date_value.replace(year=target_year, month=target_month, day=target_day)


def get_offline_subscriptions_to_renew(current_date) -> list[UserSubscription]:
    """
    Retourne les souscriptions hors Stripe actives dont la date de fin est atteinte ou dépassée.
    """
    offline_subscriptions = UserSubscription.objects.filter(
        stripe_subscription_id__isnull=True
    )
    active_offline_subscriptions = (
        subscription for subscription in offline_subscriptions
        if is_user_subscription_active(subscription.status)
    )
    return [
        subscription for subscription in active_offline_subscriptions
        if subscription.end_date.date() <= current_date
    ]


def reset_subscription_counters(subscription: UserSubscription) -> bool:
    """
    Réinitialise les compteurs d'une souscription unique via reset_subscriptions.
    Retourne True si succès, False sinon.
    """
    error_response, _ = reset_subscriptions([subscription])
    if error_response:
        logger.warning(
            f"Error during subscription {subscription.id} reset: {error_response}")
        return False
    return True


def update_subscription_end_date(subscription: UserSubscription, current_date) -> datetime:
    """
    Calcule et applique la prochaine date de fin pour la souscription fournie.
    Rattrape tous les mois manqués si la date de fin est dépassée.
    """
    new_end_date = subscription.end_date
    while new_end_date.date() <= current_date:
        new_end_date = add_one_month_safely(new_end_date)
    subscription.end_date = new_end_date
    subscription.save(update_fields=["end_date"])
    return new_end_date


def renew_subscription(subscription: UserSubscription, current_date) -> bool:
    """
    Réinitialise les compteurs et prolonge la souscription.
    Rattrape tous les mois manqués si nécessaire.
    """
    try:
        with transaction.atomic():
            if not reset_subscription_counters(subscription):
                return False

            new_end_date = update_subscription_end_date(subscription, current_date)

        logger.info(
            f"Subscription {subscription.id} renewed successfully. New end date: {new_end_date}")
        return True
    except Exception as exc:
        logger.error(
            f"Error processing subscription {subscription.id}: {exc}")
        return False


@shared_task
def process_daily_subscription_renewals():
    """
    Daily task to process subscription renewals.

    This function:
    1. Parses all UserSubscriptions without stripe_subscription_id (offline subscriptions)
    2. Checks that they meet the is_user_subscription_active conditions
    3. If the end_date is reached or passed, executes reset_subscriptions
    4. Extends the subscription until end_date exceeds current date (catches up missed months)

    Executed daily at midnight.
    """
    current_date = timezone.now().date()
    subscriptions_to_renew = get_offline_subscriptions_to_renew(current_date)

    renewed_count = 0
    error_count = 0

    for subscription in subscriptions_to_renew:
        if renew_subscription(subscription, current_date):
            renewed_count += 1
        else:
            error_count += 1

    logger.info(
        f"Processing completed. {renewed_count} subscriptions renewed, {error_count} errors.")
    return {
        'renewed_count': renewed_count,
        'error_count': error_count,
        'total_processed': len(subscriptions_to_renew)
    }


@shared_task
def report_daily_metered_usage():
    """
    Envoie les compteurs CountMetered non reportés à Stripe puis prépare
    le compteur du jour suivant.
    """
    result = report_metered_usage_to_stripe()
    logger.info(
        "Report metered usage terminé. Envoyés=%s, erreurs=%s",
        result["reported"],
        result["errors"],
    )
    return result
