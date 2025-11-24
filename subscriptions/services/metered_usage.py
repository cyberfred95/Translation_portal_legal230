"""Envoi quotidien des usages metered vers Stripe."""

import logging
from collections.abc import Iterable
from datetime import datetime, time, timezone as dt_timezone

import stripe
from django.conf import settings
from django.utils import timezone

from subscriptions.models import CountMetered, SubscriptionType, UserSubscription


logger = logging.getLogger(__name__)


class MeteredUsageError(Exception):
    """Erreur fonctionnelle lors de l'envoi d'un usage metered."""


def report_metered_usage_to_stripe() -> dict:
    """Point d'entrée appelé par la tâche Celery."""
    return MeteredUsageReporter().run()


class MeteredUsageReporter:
    """Gère la sélection des entrées et leur envoi à Stripe."""

    def __init__(self) -> None:
        self.today = timezone.now().date()

    def run(self) -> dict:
        stats = {"processed": 0, "reported": 0, "errors": 0}

        for entry in self._entries_to_report():
            stats["processed"] += 1
            try:
                usage_record_id = self._send_to_stripe(entry)
            except MeteredUsageError as error:
                stats["errors"] += 1
                logger.error(
                    "Transmission ignorée pour CountMetered %s (subscription=%s) : %s",
                    entry.id,
                    entry.user_subscription_id,
                    error,
                )
                continue
            except Exception:  # noqa: BLE001
                stats["errors"] += 1
                logger.exception(
                    "Erreur inattendue lors de l'envoi de CountMetered %s (subscription=%s)",
                    entry.id,
                    entry.user_subscription_id,
                )
                continue

            self._finalize_entry(entry, usage_record_id)
            stats["reported"] += 1

        return stats

    def _entries_to_report(self) -> Iterable[CountMetered]:
        """
        Retourne au plus un compteur (le plus récent) par souscription API.
        """
        queryset = (
            CountMetered.objects.filter(
                reported__isnull=True,
                user_subscription__subscription__product_type=SubscriptionType.ProductChoices.API,
            )
            .select_related('user_subscription', 'user_subscription__subscription')
            .order_by('user_subscription_id', '-date')
        )

        latest_per_subscription: dict[int, CountMetered] = {}
        for entry in queryset:
            if entry.user_subscription_id not in latest_per_subscription:
                latest_per_subscription[entry.user_subscription_id] = entry

        return latest_per_subscription.values()

    def _send_to_stripe(self, entry: CountMetered) -> str:
        subscription_item_id = entry.user_subscription.stripe_subscription_item_id
        if not subscription_item_id:
            raise MeteredUsageError(
                "Aucun subscription_item Stripe n'est associé à cette souscription."
            )

        timestamp = self._midnight_timestamp(entry.date)
        usage_record = stripe.UsageRecord.create(
            subscription_item=subscription_item_id,
            action="set",
            quantity=entry.daily_translated_symbols_count,
            timestamp=timestamp,
            api_key=settings.STRIPE_API_KEY,
        )
        return usage_record.id

    def _midnight_timestamp(self, entry_date):
        midnight = datetime.combine(
            entry_date,
            time(0, 0, 0),
            tzinfo=dt_timezone.utc,
        )
        return int(midnight.timestamp())

    def _finalize_entry(self, entry: CountMetered, usage_record_id: str):
        entry.reported = self.today
        update_fields = ['reported']

        if usage_record_id:
            entry.stripe_usage_record_id = usage_record_id
            update_fields.append('stripe_usage_record_id')

        entry.save(update_fields=update_fields)
        self._ensure_next_counter(entry.user_subscription)

    @staticmethod
    def _ensure_next_counter(subscription: UserSubscription):
        try:
            subscription.ensure_api_count_metered()
        except ValueError as error:
            logger.error(
                "Impossible de créer le compteur du jour pour la souscription %s : %s",
                subscription.id,
                error,
            )

