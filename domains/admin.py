from django.contrib import admin
from .models import Domain, DomainGroup


class DomainAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "french_name",
        "domain_group",
    )
    change_list_template = "admin/domains/Domain/change_list.html"


class DomainGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'french_name',)


admin.site.register(DomainGroup, DomainGroupAdmin)
admin.site.register(Domain, DomainAdmin)
