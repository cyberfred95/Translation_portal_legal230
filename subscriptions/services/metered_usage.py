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

    def run(self) -> dict[str, int]:
        """Traite toutes les entrées à reporter et retourne les statistiques."""
        stats = {"processed": 0, "reported": 0, "errors": 0}

        for entry in self._entries_to_report():
            stats["processed"] += 1
            
            if self._process_entry(entry):
                stats["reported"] += 1
            else:
                stats["errors"] += 1

        return stats

    def _process_entry(self, entry: CountMetered) -> bool:
        """Traite une entrée : envoie à Stripe et finalise. Retourne True si succès."""
        try:
            usage_record_id = self._send_to_stripe(entry)
            self._finalize_entry(entry, usage_record_id)
            return True
        except MeteredUsageError as error:
            logger.error(
                "Transmission ignorée pour CountMetered %s (subscription=%s) : %s",
                entry.id,
                entry.user_subscription_id,
                error,
            )
            return False
        except Exception:  # noqa: BLE001
            logger.exception(
                "Erreur inattendue lors de l'envoi de CountMetered %s (subscription=%s)",
                entry.id,
                entry.user_subscription_id,
            )
            return False

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

    def _send_to_stripe(self, entry: CountMetered) -> str | None:
        """Envoie les données d'usage à Stripe et retourne l'identifier de l'événement."""
        self._validate_entry_for_stripe(entry)
        
        meter_event = self._create_stripe_meter_event(entry)
        return self._extract_event_identifier(meter_event, entry.id)

    def _validate_entry_for_stripe(self, entry: CountMetered) -> None:
        """Valide que l'entrée a toutes les informations nécessaires pour Stripe."""
        if not entry.user_subscription.stripe_subscription_item_id:
            raise MeteredUsageError(
                "Aucun subscription_item Stripe n'est associé à cette souscription."
            )

        if not getattr(settings, 'STRIPE_METER_EVENT_NAME', None):
            raise MeteredUsageError(
                "STRIPE_METER_EVENT_NAME n'est pas configuré."
            )

        if not entry.user_subscription.user.stripe_customer_id:
            raise MeteredUsageError(
                "La souscription n'a pas de stripe_customer_id associé."
            )

    def _create_stripe_meter_event(self, entry: CountMetered):
        """Crée l'événement Meter dans Stripe."""
        meter_event_name = settings.STRIPE_METER_EVENT_NAME
        timestamp = self._midnight_timestamp(entry.date)
        
        return stripe.billing.MeterEvent.create(
            event_name=meter_event_name,
            payload={
                "APINbChar": entry.daily_translated_symbols_count,
                "subscription_item": entry.user_subscription.stripe_subscription_item_id,
                "stripe_customer_id": entry.user_subscription.user.stripe_customer_id,
            },
            timestamp=timestamp,
            api_key=settings.STRIPE_API_KEY,
        )

    def _extract_event_identifier(self, meter_event, entry_id: int) -> str | None:
        """Extrait l'identifier de l'événement Meter retourné par Stripe."""
        try:
            return meter_event.identifier
        except AttributeError:
            logger.warning(
                "Aucun identifier trouvé dans la réponse Stripe pour CountMetered %s",
                entry_id
            )
            return None

    def _midnight_timestamp(self, entry_date):
        midnight = datetime.combine(
            entry_date,
            time(0, 0, 0),
            tzinfo=dt_timezone.utc,
        )
        return int(midnight.timestamp())

    def _finalize_entry(self, entry: CountMetered, usage_record_id: str | None) -> None:
        """Marque l'entrée comme reportée et crée le compteur suivant."""
        entry.reported = self.today
        update_fields = ['reported']

        if usage_record_id:
            entry.stripe_usage_record_id = usage_record_id
            update_fields.append('stripe_usage_record_id')

        entry.save(update_fields=update_fields)
        logger.info(
            "CountMetered %s (subscription=%s, date=%s) marqué comme reporté.",
            entry.id, entry.user_subscription_id, entry.date
        )
        self._ensure_next_counter(entry.user_subscription)

    def _ensure_next_counter(self, subscription: UserSubscription) -> None:
        """
        Crée un nouveau CountMetered pour aujourd'hui après avoir reporté.
        La date correspond au moment de création.
        """
        if not self._should_create_counter(subscription):
            return

        try:
            count_metered = CountMetered.objects.create(
                user_subscription=subscription,
                date=self.today,
                reported=None,
            )
            logger.info(
                "Nouveau CountMetered créé pour la souscription %s (date=%s).",
                subscription.id,
                self.today
            )
        except Exception:
            logger.exception(
                "Erreur lors de la création du compteur pour la souscription %s",
                subscription.id,
            )

    @staticmethod
    def _should_create_counter(subscription: UserSubscription) -> bool:
        """Vérifie si un nouveau compteur doit être créé pour cette souscription."""
        return (
            subscription.subscription is not None
            and subscription.subscription.product_type == SubscriptionType.ProductChoices.API
        )

