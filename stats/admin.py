from django.contrib import admin
from .models import StatisticSettings
from preferences.admin import PreferencesAdmin


class StatisticSettingsAdmin(PreferencesAdmin):
    exclude = ('sites',)


admin.site.register(StatisticSettings, StatisticSettingsAdmin)
