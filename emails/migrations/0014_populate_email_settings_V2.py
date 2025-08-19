# Generated 2025-08-18 16:03

from django.db import migrations


def populate_email_settings(apps, schema_editor):
    EmailSettings = apps.get_model('emails', 'EmailSettings')
    EmailSettings.objects.all().delete()

    email_settings_data = [
        # SUBSCRIPTION_DELETED
        ('SUBSCRIPTION_DELETED', 'en', 211923, 'Lexamt.com - Your subscription has been cancelled'),
        ('SUBSCRIPTION_DELETED', 'fr', 211810, 'Lexamt.fr - Suppression de votre abonnement'),
        # SUBSCRIPTION_DELETED_ADMIN
        ('SUBSCRIPTION_DELETED_ADMIN', 'en', 212053, 'Lexamt.com - Your subscription has been cancelled'),
        ('SUBSCRIPTION_DELETED_ADMIN', 'fr', 212054, 'Lexamt.fr - Suppression de votre abonnement'),
        # SUBSCRIPTION_NEED_PAYMENT_ADMIN
        ('SUBSCRIPTION_NEED_PAYMENT_ADMIN', 'en', 211924, 'Lexamt.com - Payment failure detected'),
        ('SUBSCRIPTION_NEED_PAYMENT_ADMIN', 'fr', 211809, 'Lexamt.fr - Défaut de paiement détécté'),
        # SUBSCRIPTION_TRIALS_WILL_END
        ('SUBSCRIPTION_TRIALS_WILL_END', 'en', 211925, 'Lexamt.com - Your trial period is expiring'),
        ('SUBSCRIPTION_TRIALS_WILL_END', 'fr', 211811, 'Lexamt.fr - Votre période d\'essai arrive à expiration'),
        # SUBSCRIPTION_TRIALS_WILL_END_ADMIN
        ('SUBSCRIPTION_TRIALS_WILL_END_ADMIN', 'en', 212046, 'Lexamt.com - Your trial period is expiring'),
        ('SUBSCRIPTION_TRIALS_WILL_END_ADMIN', 'fr', 212041, 'Lexamt.fr - Votre période d\'essai arrive à expiration'),
        # SUBSCRIPTION_UPDATED_INACTIVE
        ('SUBSCRIPTION_UPDATED_INACTIVE', 'en', 211926, 'Lexamt.com - Your subscription has become inactive'),
        ('SUBSCRIPTION_UPDATED_INACTIVE', 'fr', 211808, 'Lexamt.fr - Votre abonnement est devenu inactif'),
        # SUBSCRIPTION_UPDATED_INACTIVE_ADMIN
        ('SUBSCRIPTION_UPDATED_INACTIVE_ADMIN', 'en', 212052, 'Lexamt.com - Your subscription has become inactive'),
        ('SUBSCRIPTION_UPDATED_INACTIVE_ADMIN', 'fr', 212047, 'Lexamt.fr - Votre abonnement est devenu inactif'),
        # SUBSCRIPTION_UPDATED_QUANTITY_ADMIN
        ('SUBSCRIPTION_UPDATED_QUANTITY_ADMIN', 'en', 211951, 'Lexamt.com - Subscription modification confirmed'),
        ('SUBSCRIPTION_UPDATED_QUANTITY_ADMIN', 'fr', 211807, 'Lexamt.fr - Modification de votre abonnement confirmé'),
        # USER_ADM_TR_FILE
        ('USER_ADM_TR_FILE', 'en', 213243, 'lexamt.fr - Notification traduction de document(s)'),
        ('USER_ADM_TR_FILE', 'fr', 213245, 'lexamt.com - Document(s) translation notification'),
        # USER_CREATED
        ('USER_CREATED', 'en', 211927, 'Lexamt.com - Welcome and access to your account'),
        ('USER_CREATED', 'fr', 211686, 'Lexamt.fr - Bienvenue et accès à votre compte'),
        # USER_MANAGEMENT_INVITATION
        ('USER_MANAGEMENT_INVITATION', 'en', 213084, 'lexamt.com - Invitation to connect to the legal translation portal portail.lexamt.com'),
        ('USER_MANAGEMENT_INVITATION', 'fr', 213238, 'lexamt.fr - Invitation à vous connecter au portail de traduction juridique portail.lexamt.fr'),
        # USER_MANAGEMENT_QUOTE
        ('USER_MANAGEMENT_QUOTE', 'en', 213242, 'lexamt.com - Quote for expert review of your document'),
        ('USER_MANAGEMENT_QUOTE', 'fr', 213086, 'lexamt.fr - Proposition pour la relecture de votre document par un expert'),
        # USER_MANAGEMENT_RESET_PASSWORD
        ('USER_MANAGEMENT_RESET_PASSWORD', 'en', 213085, 'lexamt.fr - Réinitialisation de votre mot de passe'),
        ('USER_MANAGEMENT_RESET_PASSWORD', 'fr', 213239, 'lexamt.com - Reset password'),
    ]

    for email_type, language, template_id, subject in email_settings_data:
        EmailSettings.objects.get_or_create(
            email_type=email_type,
            language=language,
            defaults={
                'template_id': template_id,
                'subject': subject,
            }
        )


def reverse_populate_email_settings(apps, schema_editor):
    EmailSettings = apps.get_model('emails', 'EmailSettings')
    EmailSettings.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('emails', '0013_auto_20250818_1655'),
    ]

    operations = [
        migrations.RunPython(
            populate_email_settings,
            reverse_populate_email_settings,
        ),
    ]
