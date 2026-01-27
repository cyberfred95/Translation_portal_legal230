"""
Commande de gestion Django pour corriger les dates de fin d'abonnement.
Met à jour tous les UserSubscription avec une end_date >= 2027 pour qu'elle soit égale à la date d'hier.

Usage: python manage.py fix_end_dates_2027 [--dry-run]
"""
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from subscriptions.models import UserSubscription


class Command(BaseCommand):
    help = 'Met à jour tous les UserSubscription avec end_date >= 2027 pour qu\'elle soit égale à la date d\'hier'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Mode simulation - affiche ce qui sera modifié sans faire de changements',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # Date de début de 2027 (au début de la journée)
        date_2027 = timezone.make_aware(datetime(2027, 1, 1, 0, 0, 0))
        
        # Date d'hier à minuit dans le fuseau horaire actif
        now = timezone.now()
        yesterday = now - timedelta(days=1)
        # Créer la date d'hier à minuit en préservant le fuseau horaire
        yesterday_date = yesterday.date()
        yesterday_midnight = timezone.make_aware(
            datetime.combine(yesterday_date, datetime.min.time())
        )

        # Trouver tous les UserSubscription avec end_date >= 2027
        queryset = UserSubscription.objects.filter(end_date__gte=date_2027)

        total = queryset.count()
        
        self.stdout.write(f'Abonnements trouvés avec end_date >= 2027: {total}')

        if total == 0:
            self.stdout.write(self.style.SUCCESS('Aucun abonnement à mettre à jour'))
            return

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE SIMULATION - Aucun changement ne sera effectué'))
            self.stdout.write(f'\nLes abonnements suivants seront mis à jour (end_date = {yesterday_midnight}):')
            self.stdout.write('-' * 80)
            
            for subscription in queryset[:20]:  # Afficher les 20 premiers comme exemples
                self.stdout.write(
                    f'ID: {subscription.id} | User: {subscription.user} | '
                    f'Ancienne end_date: {subscription.end_date} | '
                    f'Nouvelle end_date: {yesterday_midnight}'
                )
            
            if total > 20:
                self.stdout.write(f'... et {total - 20} autres abonnements')
            
            self.stdout.write('-' * 80)
            self.stdout.write(f'\nTotal: {total} abonnements seraient mis à jour')
        else:
            # Mettre à jour tous les abonnements
            updated_count = queryset.update(end_date=yesterday_midnight)
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✓ {updated_count} abonnement(s) mis à jour avec succès'
                )
            )
            self.stdout.write(f'  Nouvelle end_date: {yesterday_midnight}')

