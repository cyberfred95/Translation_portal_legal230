from django.contrib import admin

from .models import EmailSettings


@admin.register(EmailSettings)
class EmailSettingsAdmin(admin.ModelAdmin):

    list_display = ('email_type', 'language', 'template_id', 'subject')
    list_filter = ('email_type', 'language')
    search_fields = ('email_type', 'subject')
    list_per_page = 25
    ordering = ['email_type', 'language']

    fieldsets = (
        (None, {
            'fields': ('email_type', 'language')
        }),
        ('Template Configuration', {
            'fields': ('template_id', 'subject'),
            'description': 'Configure the Active Trail template and email subject'
        }),
    )
