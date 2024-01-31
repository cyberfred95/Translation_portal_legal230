from django.contrib import admin

from preferences.admin import PreferencesAdmin
from .models import MainSettings


class MainSettingsAdmin(PreferencesAdmin):
    exclude = ('sites',)


admin.site.register(MainSettings, MainSettingsAdmin)
