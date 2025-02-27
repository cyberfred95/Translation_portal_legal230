from django.contrib import admin
from .models import LanguageQuote
from preferences.admin import PreferencesAdmin


# Register your models here.

@admin.register(LanguageQuote)
class LanguageQuoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'price')