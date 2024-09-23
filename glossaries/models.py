from django.db import models
from languages.models import Language
from users.models import User, UserGroup
from django.core.validators import FileExtensionValidator
from domains.models import Domain
from django.core.exceptions import ValidationError


# Create your models here.

class Glossary(models.Model):
    name = models.CharField(max_length=255)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, blank=True, null=True)
    group = models.ForeignKey(UserGroup, on_delete=models.SET_NULL, blank=True, null=True)
    file = models.FileField(upload_to='glossaries/', validators=[FileExtensionValidator(['csv'])])
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
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='glossaries')

    class Meta:
        verbose_name = 'Glossary'
        verbose_name_plural = 'Glossaries'

    def __str__(self):
        return self.name

    def file_size(self):
        if self.file:
            size = self.file.size
            return str(round(size / (1024 * 1024), 2)) + " Mb"
        else:
            return

    def clean(self):
        # Ensure that either user or group is selected, but not both
        if self.user and self.group:
            raise ValidationError("You cannot select both a user and a group at the same time.")
        if not self.user and not self.group:
            raise ValidationError("You must select either a user or a group.")

        super().clean()
