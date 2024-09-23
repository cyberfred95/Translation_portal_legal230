from django.db import models
from preferences.models import Preferences


class StatisticSettings(Preferences):
    API_KEY = models.CharField(max_length=255)
    URL = models.URLField(max_length=255, default='https://statistic.portal.custom.mt/')

    class Meta:
        verbose_name = 'Statistic Settings'
        verbose_name_plural = 'Statistic Settings'
