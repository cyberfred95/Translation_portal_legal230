import uuid
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings


class UserGroup(models.Model):
    name = models.CharField(max_length=64)
    admin = models.ManyToManyField('users.User', blank=True)
    quote_monthly_number = models.IntegerField(
        default=0, validators=[MinValueValidator(1), MaxValueValidator(9999)])

    def generate_quoting_number(self):
        self.quote_monthly_number += 1
        self.save()
        return f"{now().strftime('%Y/%m')}/{self.quote_monthly_number}"

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'

    def __str__(self):
        return self.name


class User(AbstractUser):
    # Constantes pour les périodes de rétention (en jours)
    RETENTION_1_DAY = 1
    RETENTION_7_DAYS = 7
    RETENTION_30_DAYS = 30
    RETENTION_1_YEAR = 365
    RETENTION_2_YEARS = 730
    RETENTION_3_YEARS = 1095
    RETENTION_5_YEARS = 1825
    
    RETENTION_PERIOD_CHOICES = [
        (RETENTION_1_DAY, '1 jour'),
        (RETENTION_7_DAYS, '7 jours'),
        (RETENTION_30_DAYS, '30 jours'),
        (RETENTION_1_YEAR, '1 an'),
        (RETENTION_2_YEARS, '2 ans'),
        (RETENTION_3_YEARS, '3 ans'),
        (RETENTION_5_YEARS, '5 ans'),
    ]
    
    DEFAULT_RETENTION_PERIOD = RETENTION_1_YEAR
    
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    stripe_customer_id = models.CharField(
        max_length=32, unique=True, verbose_name="Stripe customer ID", null=True, blank=True)
    group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE, blank=True, null=True)
    language = models.CharField(max_length=32,
                                choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE, verbose_name="Language")
    retention_period = models.IntegerField(
        choices=RETENTION_PERIOD_CHOICES,
        default=DEFAULT_RETENTION_PERIOD,
        verbose_name="Période de rétention",
        help_text="Nombre de jours avant suppression automatique des traductions"
    )
    
    @classmethod
    def get_valid_retention_periods(cls):
        """Retourne la liste des valeurs valides pour retention_period."""
        return [choice[0] for choice in cls.RETENTION_PERIOD_CHOICES]
