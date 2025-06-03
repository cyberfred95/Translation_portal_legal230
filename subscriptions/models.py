from datetime import timezone

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models

from users.models import UserGroup, User


# Create your models here.


class SubscriptionType(models.Model):
    name = models.CharField(max_length=255)

    max_symbols_count = models.IntegerField(default=0)
    max_words_count = models.IntegerField(default=0)
    max_files_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")

    price = models.DecimalField(max_digits=7, decimal_places=2)

    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")

    def __str__(self):
        return self.name


class UserSubscription(models.Model):

    class UserSubscriptionChoices(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        INACTIVE = 'INACTIVE', 'Inactive'

    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE, related_name='subscriptions')
    subscription = models.ForeignKey(SubscriptionType, on_delete=models.CASCADE, related_name='groups')
    status = models.CharField(max_length=255, choices=UserSubscriptionChoices.choices)

    max_symbols_count = models.IntegerField(default=0)
    max_files_count = models.IntegerField(default=0)
    max_words_count = models.IntegerField(default=0)
    custom_glossaries_count = models.IntegerField(default=0, verbose_name="Custom Glossaries Count")

    translated_symbols_count = models.IntegerField(default=0)
    translated_words_count = models.IntegerField(default=0)
    translated_files_count = models.IntegerField(default=0)

    access_to_writing = models.BooleanField(default=False, verbose_name="Access to Writing")
    access_to_official_glossaries = models.BooleanField(default=False, verbose_name="Access to Official Glossaries")
    access_to_sso = models.BooleanField(default=False, verbose_name="Possible access by SSO authentication logic")

    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    def __str__(self):
        return self.user.__str__()

    def clean(self):
        if self.user.subscriptions.all().exclude(id=self.id).exists():
            raise ValidationError("Subscription for this user already exists")
