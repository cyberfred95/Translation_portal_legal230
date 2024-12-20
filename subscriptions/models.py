from datetime import timezone

from django.db import models

from users.models import UserGroup


# Create your models here.


class SubscriptionType(models.Model):
    class PriceTypeChoices(models.TextChoices):
        PUMP = 'PER_USER_PER_MONTH', 'Per-user per month (PUMP)'
        AU = 'AS_USE', 'As use (AU)',

    name = models.CharField(max_length=255)

    max_words_count = models.IntegerField(default=0)
    max_files_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")


    price_type = models.CharField(max_length=255, choices=PriceTypeChoices.choices)
    price = models.DecimalField(max_digits=7, decimal_places=2)

    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")

    def __str__(self):
        return self.name


class GroupSubscription(models.Model):

    class GroupSubscriptionChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, related_name='subscriptions')
    subscription = models.ForeignKey(SubscriptionType, on_delete=models.CASCADE, related_name='groups')
    status = models.CharField(max_length=255, choices=GroupSubscriptionChoices.choices)

    max_files_count = models.IntegerField(default=0)
    max_words_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")

    translated_words_count = models.IntegerField(default=0)
    translated_files_count = models.IntegerField(default=0)

    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()


    def __str__(self):
        return self.group.name
