from django.db import models
from preferences.models import Preferences


class MainSettings(Preferences):
    sender_email = models.EmailField()
    api_key = models.CharField(max_length=256)

    class Meta:
        verbose_name = "Main Settings"
        verbose_name_plural = "Main Settings"
