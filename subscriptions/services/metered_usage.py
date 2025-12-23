"""Envoi quotidien des usages metered vers Stripe."""

import logging
from collections.abc import Iterable
from datetime import datetime, time, timezone as dt_timezone

import stripe
from django.conf import settings
from django.db import transaction
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

    def _entries_to_report(self) -> Iterable[CountMetered]:
        """
        Retourne au plus un compteur (le plus récent) par souscription API.
        
        Les entrées sont verrouillées pour éviter le traitement concurrent.
        """
        with transaction.atomic():
            queryset = (
                CountMetered.objects.filter(
                    reported__isnull=True,
                    user_subscription__subscription__product_type=SubscriptionType.ProductChoices.API,
                )
                .select_for_update(skip_locked=True)
                .select_related('user_subscription', 'user_subscription__subscription')
                .order_by('user_subscription_id', '-date')
            )

            latest_per_subscription: dict[int, CountMetered] = {}
            for entry in queryset:
                if entry.user_subscription_id not in latest_per_subscription:
                    latest_per_subscription[entry.user_subscription_id] = entry

            return list(latest_per_subscription.values())

    def _process_entry(self, entry: CountMetered) -> bool:
        """
        Traite une entrée : envoie à Stripe et finalise.
        
        Utilise un verrou pour éviter le traitement concurrent du même CountMetered.
        Le verrou est maintenu pendant toute l'opération pour garantir qu'une seule
        tâche traite chaque entrée. Avec skip_locked=True, les autres tâches
        n'attendent pas et ignorent simplement l'entrée verrouillée.
        
        Returns:
            True si l'entrée a été traitée avec succès, False sinon.
        """
        try:
            with transaction.atomic():
                # Lock entry to prevent concurrent processing
                locked_entry = (
                    CountMetered.objects.select_for_update(skip_locked=True)
                    .filter(
                        id=entry.id,
                        reported__isnull=True,
                    )
                    .first()
                )
                
                if not locked_entry:
                    logger.info(
                        "CountMetered %s (subscription=%s) déjà reporté ou verrouillé, ignoré.",
                        entry.id,
                        entry.user_subscription_id,
                    )
                    return False
                
                # Send to Stripe and finalize within the same transaction
                # This ensures atomicity and prevents duplicate Stripe calls
                usage_record_id = self._send_to_stripe(locked_entry)
                self._mark_as_reported(locked_entry, usage_record_id)
                self._ensure_next_counter(locked_entry.user_subscription)
            
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

    def _midnight_timestamp(self, entry_date) -> int:
        """Convertit une date en timestamp Unix de minuit UTC."""
        midnight = datetime.combine(
            entry_date,
            time(0, 0, 0),
            tzinfo=dt_timezone.utc,
        )
        return int(midnight.timestamp())

    def _mark_as_reported(self, entry: CountMetered, usage_record_id: str | None) -> None:
        """
        Marque l'entrée comme reportée.
        
        Cette méthode doit être appelée dans une transaction avec l'entrée verrouillée.
        """
        entry.reported = self.today
        update_fields = ['reported']

        if usage_record_id:
            entry.stripe_usage_record_id = usage_record_id
            update_fields.append('stripe_usage_record_id')

        entry.save(update_fields=update_fields)
        logger.info(
            "CountMetered %s (subscription=%s, date=%s) marqué comme reporté.",
            entry.id,
            entry.user_subscription_id,
            entry.date
        )

    def _ensure_next_counter(self, subscription: UserSubscription) -> None:
        """
        Crée un nouveau CountMetered pour aujourd'hui après avoir reporté.
        
        Utilise get_or_create pour éviter les doublons en cas d'exécution concurrente.
        """
        if not self._should_create_counter(subscription):
            return

        try:
            count_metered, created = CountMetered.objects.get_or_create(
                user_subscription=subscription,
                date=self.today,
                defaults={'reported': None},
            )
            if created:
                logger.info(
                    "Nouveau CountMetered créé pour la souscription %s (date=%s).",
                    subscription.id,
                    self.today
                )
            else:
                logger.debug(
                    "CountMetered existe déjà pour la souscription %s (date=%s).",
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
