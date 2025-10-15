from django.contrib import admin
from .models import Prompt, PromptTranslation, Prompt
from legal.constants import LANGUAGES, EN, FR


# Register your models here.

class PromptTranslationInline(admin.StackedInline):
    model = PromptTranslation
    extra = len(LANGUAGES)
    max_num = len(LANGUAGES)
    fields = ("language", "name", "description")


class PromptAdmin(admin.ModelAdmin):
    list_display = ('id', 'gpt_model', 'icon', 'name_en', 'name_fr')
    fields = ('prompt', 'variables', 'temperature', 'gpt_model', 'icon')
    inlines = [PromptTranslationInline]

    change_list_template = "admin/writing/Prompt/change_list.html"

    @staticmethod
    def name_en(obj: Prompt) -> str:
        return obj.translations.filter(language=EN).first().name if obj.translations.filter(language=EN) else '-'

    @staticmethod
    def name_fr(obj: Prompt) -> str:
        return obj.translations.filter(language=FR).first().name if obj.translations.filter(language=FR) else '-'


admin.site.register(Prompt, PromptAdmin)
