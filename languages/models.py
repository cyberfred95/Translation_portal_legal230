from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    name = models.CharField(verbose_name=_("Name"), max_length=255, blank=True)
    abbreviation = models.CharField(verbose_name=_("Abbreviation"), max_length=2, blank=True, null=True)

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ["name"]

    def __str__(self):
        return self.name
