from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.timezone import now

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
    block_after_first_month = models.BooleanField(
        default=False, verbose_name="Block After First Month")

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

    class IntervalChoices(models.TextChoices):
        DAY = 'day', 'Day'
        WEEK = 'week', 'Week'
        MONTH = 'month', 'Month'
        YEAR = 'year', 'Year'

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    subscription = models.ForeignKey(
        SubscriptionType, on_delete=models.CASCADE, related_name='users')
    status = models.CharField(
        max_length=255, choices=UserSubscriptionChoices.choices)
    stripe_subscription_id = models.CharField(
        max_length=32, verbose_name="Stripe Subscription ID", null=True, blank=True)
    stripe_subscription_item_id = models.CharField(
        max_length=64,
        verbose_name="Stripe Subscription Item ID",
        null=True,
        blank=True,
        help_text="Identifiant Stripe de l'item metered associé",
    )
    api_key = models.CharField(
        max_length=256, 
        blank=True, 
        null=True,
        help_text="API key for this subscription. If not provided, will be automatically generated"
    )
    interval = models.CharField(
        max_length=10,
        choices=IntervalChoices.choices,
        verbose_name="Billing Interval",
        help_text="Billing interval for this subscription (day, week, month, or year)"
    )

    max_symbols_count = models.IntegerField(default=-1)
    max_files_count = models.IntegerField(default=0)
    max_words_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(
        default=0, verbose_name="Custom Glossaries Count")

    translated_symbols_count = models.IntegerField(default=0)
    translated_words_count = models.IntegerField(default=0)
    translated_files_count = models.IntegerField(default=0)

    technical_maximum_symbol_removed = models.BooleanField(
        default=False,
        verbose_name="Technical Maximum Symbol Removed",
        help_text="If True, ignore the technical maximum symbols limit check"
    )

    access_to_writing = models.BooleanField(
        default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(
        default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(
        default=False, verbose_name="Possible access by SSO authentication logic")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    
    
    def __str__(self):
        return str(self.user)

    def is_active(self):
        """
        Vérifie si la souscription est active.
        
        Returns:
            bool: True si la souscription est dans un état actif.
        """
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
        """
        Surcharge de save() pour :
        - Initialiser les valeurs depuis SubscriptionType lors de la création
        - Générer automatiquement une clé API si nécessaire
        - S'assurer que le CountMetered existe pour les souscriptions API
        """
        self._initialize_from_subscription_type()
        self._generate_api_key_if_needed(*args, **kwargs)
        self._ensure_today_metered_exists()

    def clean(self):
        """
        Valide que l'utilisateur n'a qu'une seule souscription.
        
        Raises:
            ValidationError: Si l'utilisateur a déjà une autre souscription.
        """
        if self.user.subscriptions.all().exclude(id=self.id).exists():
            raise ValidationError("Subscription for this user already exists")

    def get_today_count_metered(self):
        """
        Retourne le CountMetered déjà créé pour aujourd'hui.
        L'appelant est responsable de créer l'entrée s'il n'en existe pas.
        Lève une ValueError si plusieurs enregistrements existent pour la même date.
        """
        today = now().date()
        entries = list(
            self.count_metered.filter(date=today).order_by('-reported', '-id')[:2]
        )

        if len(entries) > 1:
            raise ValueError(
                f"Multiple CountMetered entries found for {today} on subscription {self.pk}."
            )

        return entries[0] if entries else None

    def ensure_api_count_metered(self):
        """
        Crée un CountMetered pour aujourd'hui si la souscription est de type API.
        Retourne un tuple (CountMetered, created) où created est True si l'objet a été créé.
        """
        if not self.subscription:
            raise ValueError("Cannot create CountMetered because subscription is missing.")

        if self.subscription.product_type != SubscriptionType.ProductChoices.API:
            return None, False

        today = now().date()
        return CountMetered.objects.get_or_create(
            user_subscription=self,
            date=today,
            defaults={'reported': None},
        )

    def _initialize_from_subscription_type(self):
        """
        Initialise les valeurs depuis SubscriptionType uniquement lors de la création.
        Cette méthode ne fait rien si l'objet existe déjà (mise à jour).
        """
        if not self.subscription or self.pk is not None:
            return

        self.max_files_count = self.subscription.max_files_count
        self.max_words_count = self.subscription.max_words_count
        self.max_symbols_count = self.subscription.max_symbols_count
        self.custom_glossaries_count = self.subscription.custom_glossaries_count
        self.access_to_writing = self.subscription.access_to_writing
        self.access_to_official_glossaries = self.subscription.access_to_official_glossaries
        self.access_to_sso = self.subscription.access_to_sso

    def _needs_api_key_generation(self):
        """Vérifie si une clé API doit être générée."""
        return not self.api_key and self.is_active()

    def _generate_api_key_if_needed(self, *args, **kwargs):
        """
        Génère automatiquement une clé API si nécessaire.
        Effectue un premier save() pour obtenir un ID, puis génère la clé et sauvegarde à nouveau.
        """
        if not self._needs_api_key_generation():
            super().save(*args, **kwargs)
            return

        # Premier save pour obtenir un ID
        super().save(*args, **kwargs)
        
        # Génération de la clé API unique
        self.api_key = self.create_api_key()
        
        # Sauvegarde finale avec la clé API
        super().save()

    def _should_track_api_usage(self):
        """
        Vérifie si l'utilisation API doit être suivie pour cette souscription.
        
        Returns:
            bool: True si la souscription est de type API.
        """
        return (
            self.subscription
            and self.subscription.product_type == SubscriptionType.ProductChoices.API
        )

    def _ensure_today_metered_exists(self):
        """
        S'assure qu'un CountMetered existe pour aujourd'hui si nécessaire.
        Ne fait rien si la souscription n'est pas de type API.
        """
        if not self._should_track_api_usage():
            return

        if self.get_today_count_metered() is None:
            self.ensure_api_count_metered()


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


class CountMetered(models.Model):
    date = models.DateField()
    user_subscription = models.ForeignKey(
        UserSubscription, on_delete=models.CASCADE, related_name='count_metered')
    reported = models.DateField(
        null=True, blank=True, 
        verbose_name="Reported Date",
    )
    stripe_usage_record_id = models.CharField(
        max_length=255, 
        null=True, blank=True,
        verbose_name="Stripe Usage Record ID",
    )
    daily_translated_symbols_count = models.IntegerField(default=0)
    daily_translated_words_count = models.IntegerField(default=0)
    daily_translated_files_count = models.IntegerField(default=0)

    def __str__(self):
        return (
            f"Metered usage for {self.user_subscription} on {self.date}"
        )
