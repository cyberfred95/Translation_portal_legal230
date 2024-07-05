from django.db import models
from django.utils.translation import gettext_lazy as _


class Domain(models.Model):
    name = models.CharField(max_length=255)
    french_name = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")
        ordering = ["name"]
