from celery import shared_task
from .models import UserGroup


@shared_task
def reset_quote_number():
    user_groups = UserGroup.objects.all()
    for user_group in user_groups:
        user_group.quote_monthly_number = 0
        user_group.save()
