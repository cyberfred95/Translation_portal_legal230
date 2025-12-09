# ============================================================================
# WRITING FUNCTIONALITY - TEMPORARILY DISABLED
# ============================================================================
# Cette fonctionnalité est temporairement désactivée en prévision d'une refonte.
# Tout le code est conservé en commentaire pour référence future.
# ============================================================================

# from django.contrib import admin
# from django.utils.safestring import mark_safe
# from .models import Prompt, PromptTranslation
# from legal.constants import LANGUAGES, EN, FR
# 
# 
# # Register your models here.
# 
# class PromptTranslationInline(admin.StackedInline):
#     model = PromptTranslation
#     extra = len(LANGUAGES)
#     max_num = len(LANGUAGES)
#     fields = ("language", "name", "description")
# 
# 
# class PromptAdmin(admin.ModelAdmin):
#     class Media:
#         css = {
#             'all': (
#                 'https://unpkg.com/@phosphor-icons/web@2.0.3/src/regular/style.css',
#             )
#         }
# 
#     list_display = ('id', 'gpt_model', 'name_en', 'name_fr', 'icon_display')
#     fields = ('prompt', 'variables', 'temperature', 'gpt_model', 'icon')
#     inlines = [PromptTranslationInline]
# 
#     @staticmethod
#     def icon_display(obj: Prompt):
#         if getattr(obj, 'icon', None):
#             return mark_safe(f'<i class="ph ph-{obj.icon}" style="font-size: 1.5em;"></i>')
#         return "-"
# 
#     icon_display.short_description = "Icon"
# 
#     @staticmethod
#     def name_en(obj: Prompt) -> str:
#         return obj.translations.filter(language=EN).first().name if obj.translations.filter(language=EN) else '-'
# 
#     @staticmethod
#     def name_fr(obj: Prompt) -> str:
#         return obj.translations.filter(language=FR).first().name if obj.translations.filter(language=FR) else '-'
# 
# 
# admin.site.register(Prompt, PromptAdmin)
