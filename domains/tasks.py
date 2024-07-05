import requests
from legal.keys import CUSTOM_MT_CONSOLE_URL
from preferences import preferences
from celery import shared_task
from .models import Domain


@shared_task
def update_domains():
    existing_domains = Domain.objects.all().values_list('name', flat=True)
    domains = requests.get(
        CUSTOM_MT_CONSOLE_URL + 'get-domains-list',
        headers={'token': preferences.MainSettings.api_key}
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
