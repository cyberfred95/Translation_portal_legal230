# Generated manually to fix price_type access issue

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0015_remove_subscriptiontype_price_type'),
    ]

    operations = [
        # Temporarily add price_type field to avoid Django errors
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
                verbose_name='Product Type (Legacy)'
            ),
        ),
        
        # Copy data from product_type to price_type
        migrations.RunSQL(
            "UPDATE subscriptions_subscriptiontype SET price_type = product_type;",
            reverse_sql="UPDATE subscriptions_subscriptiontype SET product_type = price_type;",
        ),
    ]
