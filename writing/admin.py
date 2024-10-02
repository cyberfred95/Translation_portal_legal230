from django.contrib import admin
from .models import Prompt, PromptTranslation, Prompt
from legal.constants import LANGUAGES, EN, FR


# Register your models here.

class PromptTranslationInline(admin.StackedInline):
    model = PromptTranslation
    extra = len(LANGUAGES)
    max_num = len(LANGUAGES)


class PromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'gpt_model', 'name_en', 'name_fr')
    inlines = [PromptTranslationInline]

    @staticmethod
    def name_en(obj: Prompt) -> str:
        return obj.translations.filter(language=EN).first().name if obj.translations.filter(language=EN) else '-'

    @staticmethod
    def name_fr(obj: Prompt) -> str:
        return obj.translations.filter(language=FR).first().name if obj.translations.filter(language=FR) else '-'


admin.site.register(Prompt, PromptAdmin)
