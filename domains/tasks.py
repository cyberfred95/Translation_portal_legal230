import requests
from django.conf import settings
from preferences import preferences
from celery import shared_task
from .models import Domain


@shared_task
def update_domains():
    existing_domains = Domain.objects.all()
    domains = requests.get(
        settings.CUSTOM_MT_CONSOLE_URL + 'translation/get-domamins-list',
        headers={'token': settings.CLOUDSTORAGE_API_KEY}
    )
    existing_domain_names = existing_domains.values_list('name', flat=True)

    cmt_domain_names = []
    for domain in domains.json():
        cmt_domain_names.append(domain['domain_name'])

    for domain in cmt_domain_names:
        if domain not in existing_domain_names:
            Domain.objects.create(name=domain)

    for domain in existing_domains:
        if domain.name not in cmt_domain_names:
            domain.delete()
