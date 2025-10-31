# Generated manually for terminating expired subscriptions

from django.db import migrations, models
from django.utils.timezone import now
from subscriptions.permissions import is_user_subscription_active


def terminate_expired_subscriptions(apps, schema_editor):
    """
    Terminate all UserSubscription that have passed their end_date
    but still have an active status.
    """
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    
    # Get current time
    current_time = now()
    
    # Get all subscriptions with active status
    active_subscriptions = UserSubscription.objects.all()
    
    print(f"Total subscriptions to check: {active_subscriptions.count()}")
    
    # Find subscriptions that are expired but still have active status
    expired_subscriptions = []
    
    for subscription in active_subscriptions:
        # Check if status is active
        if is_user_subscription_active(subscription.status):
            # Check if end_date has passed
            if current_time > subscription.end_date:
                print(f"Found expired subscription ID {subscription.id}: status={subscription.status}, end_date={subscription.end_date}")
                expired_subscriptions.append(subscription)
    
    print(f"Expired subscriptions to terminate: {len(expired_subscriptions)}")
    
    # Update all expired subscriptions to TERMINATED
    if expired_subscriptions:
        updated_ids = []
        for subscription in expired_subscriptions:
            subscription.status = 'TERMINATED'
            subscription.save()
            updated_ids.append(subscription.id)
        
        print(f"Updated {len(updated_ids)} subscriptions to TERMINATED: {updated_ids}")
    else:
        print("No expired subscriptions to update")
    
    print(f"Completed: {len(expired_subscriptions)} subscriptions terminated")


def reverse_terminate_expired_subscriptions(apps, schema_editor):
    """
    Reverse operation: set back to ACTIVE (may not be accurate)
    Note: This is a destructive reverse operation.
    """
    UserSubscription = apps.get_model('subscriptions', 'UserSubscription')
    # You can't really reverse this accurately, so we'll just pass
    print("Reverse operation: cannot accurately restore subscription status")


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0013_generate_api_keys_for_active_subscriptions'),
    ]

    operations = [
        migrations.RunPython(
            terminate_expired_subscriptions,
            reverse_terminate_expired_subscriptions,
        ),
    ]
