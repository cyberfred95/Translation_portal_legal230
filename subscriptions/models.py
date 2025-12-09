from datetime import timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

from users.models import UserGroup, User
from subscriptions.services.api_key_generator import APIKeyService


class SubscriptionType(models.Model):
    class ProductChoices(models.TextChoices):
        LEXA = 'LEXA', 'Portail lexa'
        WORD_ADD_IN = 'WORD_ADD_IN', 'Microsoft word add-in'
        API = 'API', 'Application Programming Interface'

    name = models.CharField(max_length=255)

    stripe_product_id = models.CharField(
        max_length=32, unique=True, verbose_name="Stripe Product ID", null=True, blank=True)

    max_symbols_count = models.IntegerField(
        default=-1, 
        help_text="Maximum number of symbols. Use -1 for unlimited (∞)."
    )
    max_words_count = models.IntegerField(
        default=-1, 
        help_text="Maximum number of words. Use -1 for unlimited (∞)."
    )
    max_files_count = models.IntegerField(
        default=-1, 
        help_text="Maximum number of files. Use -1 for unlimited (∞)."
    )
    custom_glossaries_count = models.IntegerField(
        default=-1, 
        verbose_name="Custom Glossaries Count",
        help_text="Maximum number of custom glossaries. Use -1 for unlimited (∞)."
    )

    product_type = models.CharField(
        max_length=255, choices=ProductChoices.choices, verbose_name="Product Type", default=ProductChoices.LEXA)
    price = models.DecimalField(max_digits=7, decimal_places=2)

    access_to_writing = models.BooleanField(
        default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(
        default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(
        default=False, verbose_name="Possible access by SSO authentication logic")

    def __str__(self):
        return self.name


class UserSubscription(models.Model):

    class UserSubscriptionChoices(models.TextChoices):
        INCOMPLETE = 'INCOMPLETE', 'Incomplete'
        ACTIVE = 'ACTIVE', 'Active'
        TRIALING = 'TRIALING', 'Trialing'
        PAST_DUE = 'PAST_DUE', 'Past Due'
        UNPAID = 'UNPAID', 'Unpaid'
        INCOMPLETE_EXPIRED = 'INCOMPLETE_EXPIRED', 'Incomplete Expired'
        TERMINATED = 'TERMINATED', 'Terminated'
        UNKNOWN = 'UNKNOWN', 'Unknown'

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    subscription = models.ForeignKey(
        SubscriptionType, on_delete=models.CASCADE, related_name='users')
    status = models.CharField(
        max_length=255, choices=UserSubscriptionChoices.choices)
    stripe_subscription_id = models.CharField(
        max_length=32, verbose_name="Stripe Subscription ID", null=True, blank=True)
    api_key = models.CharField(
        max_length=256, 
        blank=True, 
        null=True,
        help_text="API key for this subscription. If not provided, will be automatically generated"
    )


    max_symbols_count = models.IntegerField(default=-1)
    max_files_count = models.IntegerField(default=0)
    max_words_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(
        default=0, verbose_name="Custom Glossaries Count")

    translated_symbols_count = models.IntegerField(default=0)
    translated_words_count = models.IntegerField(default=0)
    translated_files_count = models.IntegerField(default=0)

    access_to_writing = models.BooleanField(
        default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(
        default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(
        default=False, verbose_name="Possible access by SSO authentication logic")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    
    def __str__(self):
        return self.user.__str__()

    def is_active(self):
        """Check if subscription is active using the same logic as permissions."""
        active_states = {
            self.UserSubscriptionChoices.INCOMPLETE,
            self.UserSubscriptionChoices.ACTIVE,
            self.UserSubscriptionChoices.TRIALING,
            self.UserSubscriptionChoices.PAST_DUE,
        }
        return self.status in active_states

    def create_api_key(self) -> str:
        """
        Crée une nouvelle clé API locale unique.
        
        Cette méthode génère une clé API localement et vérifie qu'elle n'existe
        pas déjà dans la base de données avant de la retourner.
        
        Returns:
            str: Clé API unique générée au format UUID.
            
        Raises:
            RuntimeError: Si aucune clé unique n'a pu être générée.
        """
        return APIKeyService.create_api_key_for_subscription(self)

    def save(self, *args, **kwargs):
        if self.subscription:
            self.max_files_count = self.subscription.max_files_count
            self.max_words_count = self.subscription.max_words_count
            self.max_symbols_count = self.subscription.max_symbols_count
            self.custom_glossaries_count = self.subscription.custom_glossaries_count
            self.access_to_writing = self.subscription.access_to_writing
            self.access_to_official_glossaries = self.subscription.access_to_official_glossaries
            self.access_to_sso = self.subscription.access_to_sso
        
        # Auto-generate API key if empty AND subscription is active
        needs_api_key = (
            not self.api_key and 
            self.is_active()
        )
        
        if needs_api_key:
            # First save to get an ID
            super().save(*args, **kwargs)
            
            # Generate unique API key using the local service
            # Le service garantit l'unicité et génère une clé de manière fiable
            self.api_key = self.create_api_key()
            
            # Save again with the API key
            super().save()
        else:
            # Normal save if API key already exists or not needed
            super().save(*args, **kwargs)

    def clean(self):
        if self.user.subscriptions.all().exclude(id=self.id).exists():
            raise ValidationError("Subscription for this user already exists")


# New model for counter history
class CountHistory(models.Model):
    user_subscription = models.ForeignKey(
        UserSubscription, on_delete=models.CASCADE, related_name='count_histories')
    subscription_type = models.ForeignKey(
        SubscriptionType, on_delete=models.CASCADE, related_name='count_histories')
    start_date = models.DateTimeField()
    translated_symbols_count = models.IntegerField()
    translated_words_count = models.IntegerField()
    translated_files_count = models.IntegerField()

    def __str__(self):
        return f"History for {self.user_subscription} at {self.start_date}"
