# Generated manually to add price_type field for Django compatibility

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0012_auto_20251027_1359'),
    ]

    operations = [
        # Add price_type field with same data as product_type
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
