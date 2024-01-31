from django.contrib import admin
from .models import Language


# Register your models here.

@admin.register(Language)
class LanguageRegionCodeAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "abbreviation"
    )
