from django.db import models

from users.models import UserGroup


# Create your models here.


class SubscriptionType(models.Model):
    class PriceTypeChoices(models.TextChoices):
        PUMP = 'PER_USER_PER_MONTH', 'Per-user per month (PUMP)'
        AU = 'AS_USE', 'As use (AU)',

    name = models.CharField(max_length=255)
    max_words_count = models.IntegerField(default=0)
    words_used = models.IntegerField(default=0)
    price_type = models.CharField(max_length=255, choices=PriceTypeChoices.choices)
    price = models.DecimalField(max_digits=7, decimal_places=2)
    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")


class GroupSubscription(models.Model):
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, null=True, blank=True)
    subscription = models.ForeignKey(SubscriptionType, on_delete=models.SET_NULL, null=True, blank=True)
    used_words_count = models.IntegerField(default=0)
    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")