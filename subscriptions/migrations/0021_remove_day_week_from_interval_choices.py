# Generated manually - removes day and week from interval choices

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0020_add_interval_to_usersubscription'),
    ]

    operations = [
        migrations.AlterField(
            model_name='usersubscription',
            name='interval',
            field=models.CharField(
                choices=[('month', 'Month'), ('year', 'Year')],
                help_text='Billing interval for this subscription (month or year)',
                max_length=10,
                verbose_name='Billing Interval'
            ),
        ),
    ]

