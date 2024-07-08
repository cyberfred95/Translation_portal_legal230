from django.db import models
from preferences.models import Preferences


class MainSettings(Preferences):

    class AlgorithmChoices(models.TextChoices):
        template = 'template', 'Template'
        domains = 'domain', 'Domain'

    sender_email = models.EmailField()
    api_key = models.CharField(max_length=256)
    algorithm = models.CharField(choices=AlgorithmChoices.choices, default=AlgorithmChoices.template, max_length=32)

    class Meta:
        verbose_name = "Main Settings"
        verbose_name_plural = "Main Settings"
