import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legal.settings")

app = Celery("legal")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    # 'reset_quote_counter': {
    #    'task': "quoting.tasks.reset_quote_counter",
    #    "schedule": crontab(minute='0', hour='0', day_of_month=1),
    #    "args": (),
    # },
    'process_daily_subscription_renewals': {
        'task': "subscriptions.tasks.process_daily_subscription_renewals",
        "schedule": crontab(minute='0', hour='0'),
        "args": (),
    },
    'report_daily_metered_usage': {
        'task': "subscriptions.tasks.report_daily_metered_usage",
        "schedule": crontab(minute='5', hour='0'),
        "args": (),
    }
}
