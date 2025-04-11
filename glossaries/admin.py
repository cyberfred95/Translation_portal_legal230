from django.contrib import admin
from .models import Glossary
from .forms import GlossaryAdminForm


class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_language', 'target_language','domain', 'file_size')
    exclude = ('name',)
    search_fields = ('name',)
    form = GlossaryAdminForm


admin.site.register(Glossary, GlossaryAdmin)

# Register your models here.
