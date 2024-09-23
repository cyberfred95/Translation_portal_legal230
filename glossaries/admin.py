from django.contrib import admin
from .models import Glossary


class GlossaryAdmin(admin.ModelAdmin):
    list_display = ('name', 'source_language', 'target_language', 'file_size')


admin.site.register(Glossary, GlossaryAdmin)

# Register your models here.
