# Generated manually for generating API keys for active subscriptions

import uuid
import requests
from django.db import migrations, models
from django.utils.timezone import now
from django.conf import settings
from subscriptions.permissions import is_user_subscription_active


def generate_api_keys_for_active_subscriptions(apps, schema_editor):
    """
    Generate API keys for all active UserSubscription that don't have one yet.
    """
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    
    # Get all subscriptions without API key (null or empty)
    subscriptions_without_key = UserSubscription.objects.filter(
        models.Q(api_key__isnull=True) | models.Q(api_key='')
    )
    
    print(f"Total subscriptions without API key: {subscriptions_without_key.count()}")
    
    # Filter by active status and date range
    current_time = now()
    subscriptions_to_update = []
    
    for subscription in subscriptions_without_key:
        print(f"Checking subscription ID {subscription.id}: status={subscription.status}, start={subscription.start_date}, end={subscription.end_date}")
        
        # Check if subscription is active using the same logic as permissions
        if is_user_subscription_active(subscription.status):
            print(f"  -> Status is active")
            # Check date range
            if (current_time <= subscription.end_date and 
                current_time >= subscription.start_date):
                print(f"  -> Date range is valid")
                subscriptions_to_update.append(subscription)
            else:
                print(f"  -> Date range invalid: now={current_time}")
        else:
            print(f"  -> Status is not active")
    
    print(f"Subscriptions to update: {len(subscriptions_to_update)}")
    
    # Function to create API key (same logic as in the model)
    def create_api_key(subscription_id):
        try:
            if not hasattr(settings, 'CUSTOM_MT_CONSOLE_URL') or not hasattr(settings, 'CLOUDSTORAGE_API_KEY'):
                return None
            
            if not settings.CUSTOM_MT_CONSOLE_URL or not settings.CLOUDSTORAGE_API_KEY:
                return None
            
            url = settings.CUSTOM_MT_CONSOLE_URL.rstrip('/') + "/cabinet_api/create_api_key/"
            data = {"label": str(subscription_id)}
            headers = {
                "token": settings.CLOUDSTORAGE_API_KEY,
                "Content-Type": "application/json"
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('api_key')
            else:
                return None
        except Exception:
            return None
    
    # Generate API keys manually
    updated_count = 0
    for subscription in subscriptions_to_update:
        print(f"Generating API key for subscription ID: {subscription.id}")
        old_api_key = subscription.api_key
        
        # Generate API key
        generated_key = create_api_key(subscription.id)
        if generated_key:
            subscription.api_key = generated_key
        else:
            # Fallback to UUID
            subscription.api_key = str(uuid.uuid4())
        
        # Save the subscription
        subscription.save()
        
        print(f"  -> Old API key: {old_api_key}")
        print(f"  -> New API key: {subscription.api_key}")
        updated_count += 1
    
    print(f"Generated API keys for {updated_count} active subscriptions")


def reverse_generate_api_keys(apps, schema_editor):
    """
    Reverse operation: clear all API keys (optional)
    """
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    UserSubscription.objects.update(api_key=None)


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0012_add_api_key_to_user_subscription'),
    ]

    operations = [
        migrations.RunPython(
            generate_api_keys_for_active_subscriptions,
            reverse_generate_api_keys,
        ),
    ]
