from django.contrib import admin
from preferences import preferences

from .models import Glossary
from .forms import GlossaryAdminForm


@admin.register(Glossary)
class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_language', 'target_language', )
    exclude = ('name',)
    search_fields = ('name', 'glossary_id')
    readonly_fields = ('glossary_id',)
    form = GlossaryAdminForm

