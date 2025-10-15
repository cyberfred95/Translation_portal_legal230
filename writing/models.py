from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from legal.constants import LANGUAGES


# Create your models here.

class Prompt(models.Model):
    prompt = models.TextField()
    variables = models.JSONField(default=dict, blank=True, null=True)
    temperature = models.DecimalField(decimal_places=1, max_digits=2, default=0,
                                      validators=[MinValueValidator(0), MaxValueValidator(1)])
    gpt_model = models.CharField(max_length=100)
    icon = models.CharField(
        _("icon"),
        max_length=100,
        blank=True,
        null=True,
        help_text="Phosphor icon name (https://phosphoricons.com/)"
    )


class PromptTranslation(models.Model):
    language = models.CharField(max_length=2, choices=LANGUAGES)
    prompt = models.ForeignKey(
        Prompt, on_delete=models.CASCADE, related_name='translations')
    name = models.CharField(max_length=100)
    description = models.TextField()
