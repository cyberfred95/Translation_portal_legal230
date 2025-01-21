import uuid
from django.utils import timezone
import random

from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.timezone import now


# Create your models here.

class UserGroup(models.Model):
    name = models.CharField(max_length=64)
    api_key = models.CharField(max_length=256)
    admin = models.ForeignKey('users.User', on_delete=models.SET_NULL, blank=True, null=True)
    quote_monthly_number = models.IntegerField(default=0, validators=[MinValueValidator(1), MaxValueValidator(9999)])

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
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, blank=True, null=True)


class ResetPasswordCode(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    code = models.IntegerField()
    created_at = models.DateTimeField(default=timezone.now)

    @classmethod
    def generate_unique_code(cls):
        while True:
            code = random.randint(100000, 999999)
            if not cls.objects.filter(code=code).exists():
                return code

    @classmethod
    def create(cls, user):
        code = cls.generate_unique_code()
        verification_code = cls(user=user, code=code)
        verification_code.save()
        return verification_code
