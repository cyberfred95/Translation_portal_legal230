from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.timezone import now
from preferences.models import Preferences

from languages.models import Language


# Create your models here.

class LanguageQuote(models.Model):
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='in_language_quotes_as_source')
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='in_language_quotes_as_target')
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="€/word")

    class Meta:
        ordering = ['price']

    def __str__(self):
        return f"{self.source_language.abbreviation} -> {self.target_language.abbreviation}"
