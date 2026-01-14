# Generated manually

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0019_add_block_after_first_month'),
    ]

    operations = [
        migrations.AddField(
            model_name='usersubscription',
            name='interval',
            field=models.CharField(
                choices=[('day', 'Day'), ('week', 'Week'), ('month', 'Month'), ('year', 'Year')],
                default='month',
                help_text='Billing interval for this subscription (day, week, month, or year)',
                max_length=10,
                verbose_name='Billing Interval'
            ),
        ),
    ]

