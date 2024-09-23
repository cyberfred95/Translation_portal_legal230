from celery import shared_task
from stats.calculator import StatsProcessor


@shared_task
def send_statistic_request(texts, user_uuid, translation_name):
    StatsProcessor.send_request(texts=texts, user_uuid=user_uuid, translation_name=translation_name)
