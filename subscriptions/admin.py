from django.contrib import admin
from .models import SubscriptionType, GroupSubscription

# Register your models here.
admin.site.register(SubscriptionType)


class GroupSubscriptionAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('group', 'subscription', 'status')}),
        ('Allowed', {'fields': ('max_words_count', 'max_files_count', 'custom_glossaries_count',)}),
        ('Translated', {'fields': ('translated_words_count', 'translated_files_count')}),
        ('Access permissions', {'fields': ('access_to_writing', 'access_to_official_glossaries', 'access_to_sso')}),
        ('Dates', {'fields': ('start_date', 'end_date')}),
    )


admin.site.register(GroupSubscription, GroupSubscriptionAdmin)
