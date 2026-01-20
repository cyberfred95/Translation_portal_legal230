import os
from celery import Celery
from celery.schedules import crontab

# Use environment variable if set, otherwise default to legal.settings
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "legal.settings")

app = Celery("legal")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Force Redis as broker transport explicitly
# This ensures Celery uses Redis instead of trying to auto-detect AMQP
app.conf.update(
    broker_transport='redis',
    broker_transport_options={'visibility_timeout': 3600}
)

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'process_daily_subscription_renewals': {
        'task': "subscriptions.tasks.process_daily_subscription_renewals",
        "schedule": crontab(minute='0', hour='0'),
        "args": (),
    },
    'process_monthly_renewals_for_stripe_annual': {
        'task': "subscriptions.tasks.process_monthly_renewals_for_stripe_annual",
        "schedule": crontab(minute='0', hour='0'),
        "args": (),
    },
    'report_daily_metered_usage': {
        'task': "subscriptions.tasks.report_daily_metered_usage",
        "schedule": crontab(minute='5', hour='0'),
        "args": (),
    },
    'cleanup_expired_documents': {
        'task': "users.tasks.cleanup_expired_documents",
        "schedule": crontab(minute='0', hour='0'),
        "args": (),
    },
    'run_daily_health_checks': {
        'task': "monitoring.run_scheduled_health_checks",
        "schedule": crontab(minute='0', hour='22'),
        "args": (),
    }
}
