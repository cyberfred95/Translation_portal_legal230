from django.contrib import admin
from .models import Domain


class DomainAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "french_name"
    )
    change_list_template = "admin/domains/Domain/change_list.html"


admin.site.register(Domain, DomainAdmin)
