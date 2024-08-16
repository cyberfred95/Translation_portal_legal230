import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser


# Create your models here.

class UserGroup(models.Model):
    name = models.CharField(max_length=64)
    api_key = models.CharField(max_length=256)
    admin = models.ForeignKey('users.User', on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = 'Group'
        verbose_name_plural = 'Groups'

    def __str__(self):
        return self.name


class User(AbstractUser):
    uuid = models.UUIDField(default=uuid.uuid4, unique=True)
    group = models.ForeignKey(UserGroup, on_delete=models.CASCADE, blank=True, null=True)
