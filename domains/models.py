from django.db import models
from django.utils.translation import gettext_lazy as _
from preferences.models import Preferences

ICON_WEIGHT_CHOICES = [
    ('thin', _('Thin')),
    ('light', _('Light')),
    ('regular', _('Regular')),
    ('bold', _('Bold')),
    ('fill', _('Fill')),
    ('duotone', _('Duotone')),
]


class DomainGroup(models.Model):

    name = models.CharField(_("name"), max_length=255)
    french_name = models.CharField(
        _("french_name"), max_length=255, blank=True, null=True)
    icon = models.CharField(
        _("icon"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Phosphor icon name (https://phosphoricons.com/)"
    )

    def __str__(self):
        return self.name


class Domain(models.Model):
    name = models.CharField(max_length=255)
    french_name = models.CharField(max_length=255, blank=True, null=True)
    domain_group = models.ForeignKey(DomainGroup, on_delete=models.SET_NULL, blank=True, null=True,
                                     related_name='domains')
    featured = models.BooleanField(default=False)
    icon = models.CharField(
        _("icon"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Phosphor icon name (https://phosphoricons.com/)"
    )
    entities = models.ManyToManyField(
        'Entity',
        blank=True,
        related_name='domains',
        verbose_name=_("entities"),
        help_text="Entities associated with this domain"
    )

    class Meta:
        verbose_name = "Domain"
        verbose_name_plural = "Domains"
        ordering = ["name"]

    def __str__(self):
        return self.name


class DefaultTranslation(Preferences):
    name = models.CharField(
        max_length=255, help_text="Default domain which user will see if domain translation is not configured")
    french_name = models.CharField(max_length=255, blank=True, null=True)
    enabled = models.BooleanField(default=False,
                                  help_text="Activate Default Template option in to the CMT Console for translation to all languages")

    class Meta:
        verbose_name = "Default Translation"
        verbose_name_plural = "Default Translation"


class Entity(models.Model):
    name = models.CharField(_("name"), max_length=255)
    png_file = models.ImageField(
        _("PNG file"),
        upload_to='entities/',
        help_text="Entity PNG file"
    )

    class Meta:
        verbose_name = "Entity"
        verbose_name_plural = "Entities"
        ordering = ["name"]

    def __str__(self):
        return self.name
