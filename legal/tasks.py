from celery import shared_task
from stats.calculator import StatsProcessor


@shared_task
def send_statistic_request(api_key, texts, user_uuid, domain_name, source_language, target_language):
    StatsProcessor(api_key=api_key).send_request(
        texts=texts, user_uuid=user_uuid, domain_name=domain_name,
        source_language=source_language, target_language=target_language
    )
