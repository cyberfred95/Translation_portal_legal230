from django.db import models
from django.utils.translation import gettext_lazy as _


class DomainGroup(models.Model):
    name = models.CharField(_("name"), max_length=255)
    french_name = models.CharField(_("french_name"), max_length=255, blank=True, null=True)


class Domain(models.Model):
    name = models.CharField(max_length=255)
    french_name = models.CharField(max_length=255, blank=True, null=True)
    domain_group = models.ForeignKey(DomainGroup, on_delete=models.CASCADE, related_name='domains')

    class Meta:
        verbose_name = _("Domain")
        verbose_name_plural = _("Domains")
        ordering = ["name"]

    def __str__(self):
        return self.name
