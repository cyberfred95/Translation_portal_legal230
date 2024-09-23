from django.contrib import admin
from .models import StatisticSettings
from preferences.admin import PreferencesAdmin


class SettingsAdmin(PreferencesAdmin):
    exclude = ('sites', 'URL')

admin.site.register(StatisticSettings, SettingsAdmin)