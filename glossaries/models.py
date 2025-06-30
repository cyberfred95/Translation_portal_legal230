import os

import requests
from django.conf import settings
from django.db import models

from glossaries.helpers import get_glossary_username
from glossaries.processor import GlossaryProcessor
from glossaries.services import AIGlossaryService
from languages.models import Language
from users.models import User, UserGroup
from django.core.validators import FileExtensionValidator
from domains.models import Domain
from django.core.exceptions import ValidationError
from preferences import preferences


# Create your models here.

class Glossary(models.Model):
    name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(upload_to='glossaries/', validators=[FileExtensionValidator(['csv', 'xlsx'])])
    glossary_id = models.CharField(max_length=255, blank=True, null=True)
    source_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='source_language_glossaries'
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.SET_NULL,
        blank=True, null=True,
        related_name='target_language_glossaries'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    domain = models.ForeignKey(Domain, on_delete=models.SET_NULL, blank=True, null=True, related_name='glossaries')

    class Meta:
        verbose_name = 'Glossary'
        verbose_name_plural = 'Glossaries'

    def clean(self):
        if self.user and self.group:
            raise ValidationError("You cannot select both a user and a group at the same time.")

        if self.pk:

            existing_default_glossaries = Glossary.objects.filter(
                domain=self.domain,
                source_language=self.source_language,
                target_language=self.target_language,
                group__isnull=True,
                user__isnull=True
            )
            if not self.group and not self.user:
                existing_default_glossaries = existing_default_glossaries.exclude(pk=self.pk)

                if existing_default_glossaries.exists():
                    raise ValidationError("A default glossary for this language pair and domain already exists.")

                if not self.domain:
                    raise ValidationError("You must choose a domain for default glossary.")

        if not self.domain and not self.user and not self.group:
            raise ValidationError("You have to choose domain or user or group")

        existing_glossary_filters = {
            'domain': self.domain,
            'source_language': self.source_language,
            'target_language': self.target_language
        }

        if self.user:
            if Glossary.objects.filter(**existing_glossary_filters, user=self.user).exclude(pk=self.pk).exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and user already exists")
        elif self.group:
            if Glossary.objects.filter(**existing_glossary_filters, group=self.group).exclude(pk=self.pk).exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and user already exists")

        super().clean()

