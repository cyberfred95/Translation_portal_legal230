from django.contrib import admin
from .models import Domain
from .tasks import update_domains


def update_domains_action(modeladmin, request, queryset):
    update_domains()


update_domains_action.short_description = 'Refresh'


@admin.register(Domain)
class LanguageRegionCodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "french_name"
    )
    actions = [update_domains_action]
