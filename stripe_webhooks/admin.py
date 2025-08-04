from django.contrib import admin

from .models import StripeEvent


@admin.register(StripeEvent)
class StripeEventAdmin(admin.ModelAdmin):

    fields = [
        'event_id',
        'event_type',
        'status',
        'code_response',
        'created_at',
        'data',
        'http_response'
    ]

    list_display = (
        'event_id',
        'event_type',
        'status',
        'code_response',
        'created_at'
    )

    list_filter = (
        'event_type',
        'created_at',
        'code_response'
    )

    search_fields = (
        'event_id',
        'event_type'
    )

    readonly_fields = ('created_at',)

    ordering = ('-created_at',)
