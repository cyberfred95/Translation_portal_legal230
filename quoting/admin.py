from django.contrib import admin
from .models import LanguageQuote


# Register your models here.

class LanguageQuoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'price')


admin.site.register(LanguageQuote, LanguageQuoteAdmin)
