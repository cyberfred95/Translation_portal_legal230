from django.contrib import admin
from .models import Domain


class DomainAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "french_name"
    )


admin.site.register(Domain, DomainAdmin)
