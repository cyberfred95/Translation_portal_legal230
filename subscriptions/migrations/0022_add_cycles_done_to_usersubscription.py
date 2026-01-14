# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0021_remove_day_week_from_interval_choices'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='cycles_done',
            field=models.IntegerField(
                default=0,
                help_text='Number of monthly cycles completed for annual Stripe subscriptions (0-11). Always 0 for monthly subscriptions.',
                verbose_name='Cycles Done'
            ),
        ),
    ]

