from celery import shared_task
from .models import QuotingNumberCounter


@shared_task
def reset_quote_number():
    quote_counter = QuotingNumberCounter.objects.first()
    quote_counter.number = 0
    quote_counter.save()
