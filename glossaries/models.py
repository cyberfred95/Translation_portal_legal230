"""
Glossary model for Lexa project.

This model serves as a cache/metadata store for glossaries that are
actually stored and managed in lara-bridge. Synchronization with LARA
is handled automatically via Django signals (see signals.py).
"""
import os
from django.db import models
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError

from languages.models import Language
from users.models import User, UserGroup
from domains.models import Domain


class Glossary(models.Model):
    """
    Glossary model - metadata cache for LARA-managed glossaries.
    
    The actual glossary files and data are stored in lara-bridge.
    This model maintains local metadata for synchronization purposes.
    """
    name = models.CharField(max_length=255, blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(
        upload_to='glossaries/',
        validators=[FileExtensionValidator(['csv', 'xlsx'])]
    )
    glossary_id = models.CharField(max_length=255, blank=True, null=True)
    source_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='source_language_glossaries'
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='target_language_glossaries'
    )
    created_at = models.DateTimeField(
        auto_now=True,
        help_text="Updated on each save to track last modification"
    )
    domain = models.ForeignKey(
        Domain,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='glossaries'
    )

    class Meta:
        verbose_name = 'Glossary'
        verbose_name_plural = 'Glossaries'

    def clean(self):
        """Validate glossary instance before saving."""
        self._validate_user_group_exclusivity()
        self._validate_owner_required()
        
        if self.pk:
            self._validate_default_glossary_uniqueness()
        
        self._validate_glossary_uniqueness()
        super().clean()

    def _validate_user_group_exclusivity(self):
        """Ensure user and group are mutually exclusive."""
        if self.user and self.group:
            raise ValidationError(
                "You cannot select both a user and a group at the same time."
            )

    def _validate_owner_required(self):
        """Ensure glossary has at least one owner (domain, user, or group)."""
        if not self.domain and not self.user and not self.group:
            raise ValidationError(
                "You have to choose domain or user or group"
            )

    def _validate_default_glossary_uniqueness(self):
        """Validate uniqueness for default glossaries (no user/group)."""
        if not self.group and not self.user:
            if not self.domain:
                raise ValidationError(
                    "You must choose a domain for default glossary."
                )
            
            existing = Glossary.objects.filter(
                domain=self.domain,
                source_language=self.source_language,
                target_language=self.target_language,
                group__isnull=True,
                user__isnull=True
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    "A default glossary for this language pair and domain already exists."
                )

    def _validate_glossary_uniqueness(self):
        """Validate uniqueness for user/group-specific glossaries."""
        filters = {
            'domain': self.domain,
            'source_language': self.source_language,
            'target_language': self.target_language
        }
        
        if self.user:
            existing = Glossary.objects.filter(
                **filters,
                user=self.user
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and user already exists"
                )
        
        elif self.group:
            existing = Glossary.objects.filter(
                **filters,
                group=self.group
            ).exclude(pk=self.pk)
            
            if existing.exists():
                raise ValidationError(
                    "A glossary for this language pair and domain and group already exists"
                )

    def save(self, *args, **kwargs):
        """Save glossary instance, auto-generating name from file if needed."""
        if not self.name and self.file:
            self.name = os.path.splitext(os.path.basename(self.file.name))[0]
        
        super().save(*args, **kwargs)

    def to_json(self, request=None):
        """
        Convert glossary instance to JSON format.
        
        Args:
            request: Django request object (unused, kept for API compatibility)
        
        Returns:
            dict: Glossary data in JSON format
        """
        return {
            "id": self.id,
            "name": self.name,
            "source_language": self.source_language.abbreviation.upper(),
            "target_language": self.target_language.abbreviation.upper(),
            "created_at": self.created_at,
        }

