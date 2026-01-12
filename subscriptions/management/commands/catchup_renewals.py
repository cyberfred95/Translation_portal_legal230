"""
Script de rattrapage pour les renouvellements d'abonnements manqués.

Ce script identifie les abonnements offline (sans Stripe) dont la date de fin
est passée mais qui sont toujours actifs, et les renouvelle en rattrapant
tous les mois manqués.

Usage:
    python manage.py catchup_renewals          # Mode dry-run (affiche sans modifier)
    python manage.py catchup_renewals --apply  # Applique les corrections
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction

from subscriptions.models import UserSubscription
from subscriptions.permissions import is_user_subscription_active
from subscriptions.tasks import add_one_month_safely, reset_subscription_counters


class Command(BaseCommand):
    help = 'Rattrape les renouvellements manqués pour les abonnements offline'

    def add_arguments(self, parser):
        parser.add_argument(
            '--apply',
            action='store_true',
            help='Applique les corrections (sans cette option, mode dry-run)',
        )

    def handle(self, *args, **options):
        apply_changes = options['apply']
        current_date = timezone.now().date()

        if apply_changes:
            self.stdout.write(self.style.WARNING('Mode APPLY - Les modifications seront appliquées'))
        else:
            self.stdout.write(self.style.WARNING('Mode DRY-RUN - Aucune modification ne sera appliquée'))
            self.stdout.write('Utilisez --apply pour appliquer les corrections\n')

        # Trouver les abonnements offline
        offline_subscriptions = UserSubscription.objects.filter(
            stripe_subscription_id__isnull=True
        ).select_related('user', 'subscription')

        # Filtrer les abonnements actifs avec end_date passée
        expired_active_subscriptions = []
        for sub in offline_subscriptions:
            if is_user_subscription_active(sub.status) and sub.end_date.date() < current_date:
                expired_active_subscriptions.append(sub)

        if not expired_active_subscriptions:
            self.stdout.write(self.style.SUCCESS('Aucun abonnement à rattraper.'))
            return

        self.stdout.write(f'\nTrouvé {len(expired_active_subscriptions)} abonnement(s) à rattraper:\n')
        self.stdout.write('-' * 80)

        total_renewed = 0
        total_errors = 0

        for sub in expired_active_subscriptions:
            user_email = sub.user.email
            original_end_date = sub.end_date
            months_behind = self._calculate_months_behind(sub.end_date.date(), current_date)

            self.stdout.write(f'\nUtilisateur: {user_email}')
            self.stdout.write(f'  Subscription ID: {sub.id}')
            self.stdout.write(f'  Status: {sub.status}')
            self.stdout.write(f'  Type: {sub.subscription.name if sub.subscription else "N/A"}')
            self.stdout.write(f'  End date actuelle: {original_end_date.date()}')
            self.stdout.write(f'  Mois de retard: {months_behind}')

            if apply_changes:
                success, new_end_date = self._catchup_subscription(sub, current_date)
                if success:
                    self.stdout.write(self.style.SUCCESS(
                        f'  -> Renouvelé! Nouvelle end date: {new_end_date.date()}'
                    ))
                    total_renewed += 1
                else:
                    self.stdout.write(self.style.ERROR(
                        f'  -> ERREUR lors du renouvellement'
                    ))
                    total_errors += 1
            else:
                # Calculer ce que serait la nouvelle date
                projected_end_date = self._calculate_new_end_date(sub.end_date, current_date)
                self.stdout.write(f'  -> Nouvelle end date prévue: {projected_end_date.date()}')

        self.stdout.write('\n' + '-' * 80)
        if apply_changes:
            self.stdout.write(self.style.SUCCESS(
                f'Terminé: {total_renewed} renouvelé(s), {total_errors} erreur(s)'
            ))
        else:
            self.stdout.write(f'Total à traiter: {len(expired_active_subscriptions)} abonnement(s)')
            self.stdout.write(self.style.WARNING('\nRelancez avec --apply pour appliquer les corrections'))

    def _calculate_months_behind(self, end_date, current_date):
        """Calcule le nombre de mois de retard."""
        months = 0
        temp_date = end_date
        while temp_date < current_date:
            temp_date = add_one_month_safely(
                timezone.make_aware(
                    timezone.datetime(temp_date.year, temp_date.month, temp_date.day)
                )
            ).date()
            months += 1
        return months

    def _calculate_new_end_date(self, end_date, current_date):
        """Calcule la nouvelle date de fin après rattrapage."""
        new_end_date = end_date
        while new_end_date.date() < current_date:
            new_end_date = add_one_month_safely(new_end_date)
        return new_end_date

    def _catchup_subscription(self, subscription, current_date):
        """
        Rattrape un abonnement en ajoutant les mois manqués.
        Réinitialise les compteurs une seule fois puis met à jour la date.
        """
        try:
            with transaction.atomic():
                # Réinitialiser les compteurs une seule fois
                if not reset_subscription_counters(subscription):
                    return False, None

                # Ajouter les mois jusqu'à dépasser la date actuelle
                new_end_date = subscription.end_date
                while new_end_date.date() < current_date:
                    new_end_date = add_one_month_safely(new_end_date)

                subscription.end_date = new_end_date
                subscription.save(update_fields=['end_date'])

                return True, new_end_date
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  Exception: {e}'))
            return False, None
