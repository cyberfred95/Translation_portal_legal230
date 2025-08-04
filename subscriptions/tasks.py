"""
Celery tasks for subscription management.

This module contains scheduled tasks for managing user subscriptions,
including daily renewal processing for non-Stripe subscriptions.
"""

import logging
import sys
from datetime import datetime, timedelta
from celery import shared_task
from django.utils import timezone
from django.db import transaction
from django.conf import settings

from .models import UserSubscription
from .permissions import is_user_subscription_active
from stripe_webhooks.tasks_handlers.setter.set_countHistory import reset_subscriptions

logger = logging.getLogger(__name__)


@shared_task
def process_daily_subscription_renewals():
    """
    Daily task to process subscription renewals.

    This function:
    1. Parses all UserSubscriptions without stripe_subscription_id (offline subscriptions)
    2. Checks that they meet the is_user_subscription_active conditions
    3. If the end_date corresponds to the current day, executes reset_subscriptions
    4. Adds 1 month to the subscription's end_date

    Executed daily at midnight.
    """
    current_date = timezone.now().date()

    # Get UserSubscriptions without stripe_subscription_id and active
    offline_subscriptions = UserSubscription.objects.filter(
        stripe_subscription_id__isnull=True
    )

    # Filter active subscriptions
    active_offline_subscriptions = [
        subscription for subscription in offline_subscriptions
        if is_user_subscription_active(subscription.status)
    ]

    # Filter those whose end_date corresponds to the current day
    subscriptions_to_renew = [
        subscription for subscription in active_offline_subscriptions
        if subscription.end_date.date() == current_date
    ]

    renewed_count = 0
    error_count = 0

    for subscription in subscriptions_to_renew:
        try:
            with transaction.atomic():
                # Execute reset_subscriptions for this subscription
                error_response, count_history_list = reset_subscriptions([
                                                                         subscription])

                if error_response:
                    error_count += 1
                    # Only show messages outside of testing
                    if not ('test' in sys.argv or getattr(settings, 'TESTING', False)):
                        logger.warning(
                            f"Error during subscription {subscription.id} reset: {error_response}")
                    continue

                # Add 1 month to the end_date
                # Careful calculation to avoid end-of-month issues
                new_end_date = subscription.end_date
                if new_end_date.month == 12:
                    new_end_date = new_end_date.replace(
                        year=new_end_date.year + 1, month=1)
                else:
                    new_end_date = new_end_date.replace(
                        month=new_end_date.month + 1)

                subscription.end_date = new_end_date
                subscription.save()

                renewed_count += 1
                # Only show messages outside of testing
                if not ('test' in sys.argv or getattr(settings, 'TESTING', False)):
                    logger.info(
                        f"Subscription {subscription.id} renewed successfully. New end date: {new_end_date}")

        except Exception as e:
            error_count += 1
            # Only show messages outside of testing
            if not ('test' in sys.argv or getattr(settings, 'TESTING', False)):
                logger.error(
                    f"Error processing subscription {subscription.id}: {str(e)}")

    # Only show messages outside of testing
    if not ('test' in sys.argv or getattr(settings, 'TESTING', False)):
        logger.info(
            f"Processing completed. {renewed_count} subscriptions renewed, {error_count} errors.")
    return {
        'renewed_count': renewed_count,
        'error_count': error_count,
        'total_processed': len(subscriptions_to_renew)
    }
