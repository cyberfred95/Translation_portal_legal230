"""
Celery tasks for subscription management.

This module contains scheduled tasks for managing user subscriptions,
including daily renewal processing for monthly subscriptions and monthly
counter resets for annual Stripe subscriptions.
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


def get_monthly_subscriptions_to_renew(current_date) -> list[UserSubscription]:
    """
    Retourne les souscriptions mensuelles (hors Stripe) actives dont la date de fin est aujourd'hui.
    
    Cette fonction ne gère que les abonnements mensuels non-Stripe.
    Les abonnements annuels Stripe sont gérés par process_monthly_renewals_for_stripe_annual().
    """
    monthly_subscriptions = UserSubscription.objects.filter(
        stripe_subscription_id__isnull=True,
        interval=UserSubscription.IntervalChoices.MONTH
    )
    active_monthly_subscriptions = (
        subscription for subscription in monthly_subscriptions
        if is_user_subscription_active(subscription.status)
    )
    return [
        subscription for subscription in active_monthly_subscriptions
        if subscription.end_date.date() == current_date
    ]


def get_stripe_annual_subscriptions_to_renew_monthly(current_date) -> list[UserSubscription]:
    """
    Retourne les abonnements annuels Stripe qui doivent être renouvelés mensuellement.
    
    Un abonnement annuel doit être renouvelé si :
    - Il est actif
    - cycles_done < 11 (pas le dernier cycle, géré par Stripe)
    - La date calculée (start_date + cycles_done mois) correspond à aujourd'hui
    """
    stripe_annual_subscriptions = UserSubscription.objects.filter(
        stripe_subscription_id__isnull=False,
        interval=UserSubscription.IntervalChoices.YEAR,
        cycles_done__lt=11  # Exclure le dernier cycle (géré par Stripe)
    )
    
    subscriptions_to_renew = []
    for subscription in stripe_annual_subscriptions:
        if not is_user_subscription_active(subscription.status):
            continue
        
        # Calculer la date de renouvellement : start_date + cycles_done mois
        renewal_date = subscription.start_date
        for _ in range(subscription.cycles_done):
            renewal_date = add_one_month_safely(renewal_date)
        
        # Vérifier si la date de renouvellement correspond à aujourd'hui
        if renewal_date.date() == current_date:
            subscriptions_to_renew.append(subscription)
    
    return subscriptions_to_renew


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


def update_subscription_end_date(subscription: UserSubscription) -> datetime:
    """
    Calcule et applique la prochaine date de fin pour la souscription fournie.
    """
    new_end_date = add_one_month_safely(subscription.end_date)
    subscription.end_date = new_end_date
    subscription.save(update_fields=["end_date"])
    return new_end_date


def renew_subscription(subscription: UserSubscription) -> bool:
    """
    Réinitialise les compteurs et prolonge la souscription d'un mois.
    """
    try:
        with transaction.atomic():
            if not reset_subscription_counters(subscription):
                return False

            new_end_date = update_subscription_end_date(subscription)

        logger.info(
            f"Subscription {subscription.id} renewed successfully. New end date: {new_end_date}")
        return True
    except Exception as exc:
        logger.error(
            f"Error processing subscription {subscription.id}: {exc}")
        return False


def renew_stripe_annual_monthly(subscription: UserSubscription) -> bool:
    """
    Réinitialise les compteurs et incrémente cycles_done pour un abonnement annuel Stripe.
    
    Cette fonction ne modifie PAS la date de fin (end_date) qui est gérée par Stripe.
    
    Args:
        subscription: L'abonnement annuel Stripe à renouveler
        
    Returns:
        bool: True si succès, False sinon
    """
    try:
        with transaction.atomic():
            if not reset_subscription_counters(subscription):
                return False
            
            # Incrémenter cycles_done
            subscription.cycles_done += 1
            subscription.save(update_fields=["cycles_done"])
        
        logger.info(
            f"Stripe annual subscription {subscription.id} monthly renewal completed. "
            f"Cycles done: {subscription.cycles_done}")
        return True
    except Exception as exc:
        logger.error(
            f"Error processing Stripe annual subscription {subscription.id}: {exc}")
        return False


@shared_task
def process_daily_subscription_renewals():
    """
    Daily task to process monthly subscription renewals.

    This function handles ONLY monthly subscriptions (non-Stripe):
    1. Parses all UserSubscriptions without stripe_subscription_id and interval='month'
    2. Checks that they meet the is_user_subscription_active conditions
    3. If the end_date corresponds to the current day, executes reset_subscriptions
    4. Adds 1 month to the subscription's end_date

    Executed daily at midnight.
    
    Note: Annual Stripe subscriptions are handled by process_monthly_renewals_for_stripe_annual()
    """
    current_date = timezone.now().date()
    subscriptions_to_renew = get_monthly_subscriptions_to_renew(current_date)

    renewed_count = 0
    error_count = 0

    for subscription in subscriptions_to_renew:
        if renew_subscription(subscription):
            renewed_count += 1
        else:
            error_count += 1

    logger.info(
        f"Monthly subscription renewals completed. {renewed_count} renewed, {error_count} errors.")
    return {
        'renewed_count': renewed_count,
        'error_count': error_count,
        'total_processed': len(subscriptions_to_renew)
    }


@shared_task
def process_monthly_renewals_for_stripe_annual():
    """
    Daily task to process monthly counter resets for annual Stripe subscriptions.

    This function:
    1. Finds active annual Stripe subscriptions with cycles_done < 11
    2. Calculates the renewal date (start_date + cycles_done months)
    3. If the renewal date matches today, resets counters and increments cycles_done
    4. Does NOT modify end_date (managed by Stripe webhooks)

    Executed daily at midnight.
    """
    current_date = timezone.now().date()
    subscriptions_to_renew = get_stripe_annual_subscriptions_to_renew_monthly(current_date)

    renewed_count = 0
    error_count = 0

    for subscription in subscriptions_to_renew:
        if renew_stripe_annual_monthly(subscription):
            renewed_count += 1
        else:
            error_count += 1

    logger.info(
        f"Stripe annual monthly renewals completed. {renewed_count} renewed, {error_count} errors.")
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
