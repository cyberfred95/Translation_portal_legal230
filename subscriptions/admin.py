from django.contrib import admin
from .models import SubscriptionType, UserSubscription

# Register your models here.
admin.site.register(SubscriptionType)


class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription')
    fieldsets = (
        (None, {'fields': ('user', 'subscription', 'status')}),
        ('Allowed', {'fields': ('max_symbols_count', 'max_words_count', 'max_files_count', 'custom_glossaries_count',)}),
        ('Translated', {'fields': ('translated_symbols_count', 'translated_words_count', 'translated_files_count')}),
        ('Access permissions', {'fields': ('access_to_writing', 'access_to_official_glossaries', 'access_to_sso')}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
    )


admin.site.register(UserSubscription, UserSubscriptionAdmin)
