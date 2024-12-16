from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True)
    abbreviation = models.CharField(verbose_name=_("Abbreviation"), max_length=1024, blank=True, null=True)
    french_name = models.CharField(verbose_name=_("Name in French"), blank=True, null=True, max_length=255)

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ["name"]

    def __str__(self):
        return self.name
