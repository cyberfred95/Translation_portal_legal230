from django.contrib import admin
from .models import Prompt, PromptTranslation, Prompt
from legal.constants import LANGUAGES


# Register your models here.

class PromptTranslationInline(admin.StackedInline):
    model = PromptTranslation
    extra = len(LANGUAGES)
    max_num = len(LANGUAGES)


class PromptAdmin(admin.ModelAdmin):
    inlines = [PromptTranslationInline]

admin.site.register(Prompt, PromptAdmin)

