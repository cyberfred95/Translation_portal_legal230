from django.db import models
from preferences.models import Preferences


class MainSettings(Preferences):
    class AlgorithmChoices(models.TextChoices):
        template = 'template', 'Template'
        domains = 'domain', 'Domain'

    sender_email = models.EmailField()
    quote_cc_email = models.EmailField(blank=True, null=True)
    support_email = models.EmailField(blank=True, null=True)
    api_key = models.CharField(max_length=256)
    algorithm = models.CharField(choices=AlgorithmChoices.choices, default=AlgorithmChoices.template, max_length=32)
    CUSTOM_MT_CONSOLE_URL = models.URLField(max_length=256, default='https://console.custom.mt/')
    CLOUDSTORAGE_API_URL = models.URLField(max_length=256,
                                           default='https://cloudstorage.fileprocessing.custom.mt/translate/legal230/')

    class Meta:
        verbose_name = "Main Settings"
        verbose_name_plural = "Main Settings"
