import uuid
from django.utils import timezone
import random

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now
from django.conf import settings


class UserGroup(models.Model):
    name = models.CharField(max_length=64)
    api_key = models.CharField(max_length=256)
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
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    stripe_customer_id = models.CharField(
        max_length=32, unique=True, verbose_name="Stripe customer ID", null=True, blank=True)
    group = models.ForeignKey(
        UserGroup, on_delete=models.CASCADE, blank=True, null=True)
    language = models.CharField(max_length=32,
                                choices=settings.LANGUAGES, default=settings.LANGUAGE_CODE, verbose_name="Language")
