# Generated manually to cleanly migrate from price_type to product_type

from django.db import migrations, models


def migrate_price_type_to_product_type(apps, schema_editor):
    """
    Migrate data from price_type to product_type with proper mapping:
    - AS_USE -> WORD_ADD_IN
    - PER_USER_PER_MONTH -> WORD_ADD_IN
    - PUMP -> LEXA
    - AU -> WORD_ADD_IN
    """
    SubscriptionType = apps.get_model('subscriptions', 'SubscriptionType')
    
    # Mapping old values to new values
    migration_map = {
        'AS_USE': 'WORD_ADD_IN',
        'PER_USER_PER_MONTH': 'WORD_ADD_IN', 
        'PUMP': 'LEXA',
        'AU': 'WORD_ADD_IN',
    }
    
    # Update all existing records
    for subscription in SubscriptionType.objects.all():
        if hasattr(subscription, 'price_type') and subscription.price_type:
            # Map old value to new value
            new_value = migration_map.get(subscription.price_type, 'LEXA')
            subscription.product_type = new_value
            subscription.save()


def reverse_migrate_product_type_to_price_type(apps, schema_editor):
    """
    Reverse migration: copy product_type back to price_type
    """
    SubscriptionType = apps.get_model('subscriptions', 'SubscriptionType')
    
    for subscription in SubscriptionType.objects.all():
        if hasattr(subscription, 'product_type') and subscription.product_type:
            subscription.price_type = subscription.product_type
            subscription.save()


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0010_auto_20251027_1341'),
    ]

    operations = [
        # Add the new product_type field
        migrations.AddField(
            model_name='subscriptiontype',
            name='product_type',
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
        
        # Migrate data from price_type to product_type
        migrations.RunPython(
            migrate_price_type_to_product_type,
            reverse_migrate_product_type_to_price_type,
        ),
        
        # Remove the old price_type field
        migrations.RemoveField(
            model_name='subscriptiontype',
            name='price_type',
        ),
    ]
