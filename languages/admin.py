from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.sites.models import Site

from .models import Language

admin.site.unregister(Site)
admin.site.unregister(Group)


# Register your models here.

@admin.register(Language)
class LanguageRegionCodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "abbreviation",
        "french_name"
    )
