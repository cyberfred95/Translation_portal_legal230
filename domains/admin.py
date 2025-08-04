from django.contrib import admin
from .models import Domain, DomainGroup, DefaultTranslation, Entity
from preferences.admin import PreferencesAdmin
from django.utils.safestring import mark_safe


class IconMixin:
    """Mixin for managing Phosphor icons display and handling"""

    class Media:
        css = {
            'all': (
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/thin/style.css',
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/light/style.css',
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/regular/style.css',
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/bold/style.css',
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/fill/style.css',
                'https://unpkg.com/@phosphor-icons/web@2.0.3/src/duotone/style.css',
            )
        }

    def icon_display(self, obj):
        if obj.icon:
            weight_class = f"ph-{obj.icon_weight}" if hasattr(
                obj, 'icon_weight') and obj.icon_weight != 'regular' else "ph"
            return mark_safe(f'<i class="{weight_class} ph-{obj.icon}" style="font-size: 1.5em;"></i>')
        return "-"

    icon_display.short_description = "Icon"

    def save_model(self, request, obj, form, change):
        if not obj.icon:
            obj.icon = "book-open-text"
        super().save_model(request, obj, form, change)


@admin.register(Domain)
class DomainAdmin(IconMixin, admin.ModelAdmin):
    list_display = (
        "name",
        "french_name",
        "domain_group",
        "icon_display",
        "entities_preview",
    )
    fields = ("name", "french_name", "domain_group",
              "featured", "icon", "icon_weight", "entities")
    list_filter = ("domain_group", "featured")
    search_fields = ("name", "french_name")
    filter_horizontal = ("entities",)

    def entities_preview(self, obj):
        entities = obj.entities.all()
        if entities:
            images = []
            for entity in entities:
                if entity.png_file:
                    images.append(
                        f'<img src="{entity.png_file.url}" style="max-height: 30px; max-width: 30px; margin-right: 5px;" title="{entity.name}" />')
            return mark_safe(''.join(images)) if images else "-"
        return "-"

    entities_preview.short_description = "Entities"


@admin.register(DomainGroup)
class DomainGroupAdmin(IconMixin, admin.ModelAdmin):
    list_display = ("name", "french_name", "icon_display")
    fields = ("name", "french_name", "icon", "icon_weight")
    search_fields = ("name", "french_name")


@admin.register(DefaultTranslation)
class DefaultTranslationAdmin(PreferencesAdmin):
    exclude = ("sites",)


@admin.register(Entity)
class EntityAdmin(admin.ModelAdmin):
    list_display = ("name", "png_preview", "png_file")
    fields = ("name", "png_file")
    search_fields = ("name",)
    ordering = ("name",)

    def png_preview(self, obj):
        if obj.png_file:
            return mark_safe(f'<img src="{obj.png_file.url}" style="max-height: 50px; max-width: 50px;" />')
        return "-"

    png_preview.short_description = "Preview"

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('png_file',)
        return self.readonly_fields
