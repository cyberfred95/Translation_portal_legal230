from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'System test'

    def handle(self, *args, **options):
        pass
