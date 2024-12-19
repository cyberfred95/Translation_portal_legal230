from django.contrib import admin
from .models import SubscriptionType, GroupSubscription

# Register your models here.
admin.site.register(SubscriptionType)


class GroupSubscriptionAdmin(admin.ModelAdmin):
    fieldsets = (
        (None, {'fields': ('group', 'subscription')}),
        ('Allowed', {'fields': ('max_words_count', 'custom_glossaries_count', )}),
        ('Used', {'fields': ('used_words_count',)}),
        ('Access permissions', {'fields': ('access_to_writing', 'access_to_official_glossaries', 'access_to_sso')})
    )

admin.site.register(GroupSubscription, GroupSubscriptionAdmin)