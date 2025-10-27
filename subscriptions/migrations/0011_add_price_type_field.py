# Generated manually to add missing price_type field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0010_auto_20251027_1341'),
    ]

    operations = [
        migrations.AddField(
            model_name='subscriptiontype',
            name='price_type',
            field=models.CharField(
                choices=[
                    ('LEXA', 'Portail lexa'),
                    ('WORD_ADD_IN', 'Microsoft word add-in'),
                    ('API', 'Application Programming Interface')
                ],
                default='LEXA',
                max_length=255,
                verbose_name='Product Type'
            ),
        ),
    ]
