from django.core.exceptions import ValidationError
from django.db import models

from languages.models import Language
from users.models import User


# Create your models here.

class LanguageQuote(models.Model):
    source_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='in_language_quotes_as_source')
    target_language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='in_language_quotes_as_target')
    price = models.DecimalField(max_digits=5, decimal_places=2, default=0.0, help_text="€/word")
    daily_performance = models.IntegerField(default=100, help_text="words")
    additional_time_for_order_processing = models.IntegerField(default=7, help_text="days")

    class Meta:
        ordering = ['price']

    def clean(self):
        if LanguageQuote.objects.filter(
                source_language=self.source_language,
                target_language=self.target_language
        ).exclude(pk=self.pk).exists():
            raise ValidationError("A quote with this source and target language already exists.")

    def __str__(self):
        return f"{self.source_language.abbreviation} -> {self.target_language.abbreviation}"


class QuotePDF(models.Model):
    """
    Modèle pour stocker les informations sur les devis PDF créés.
    
    Lors de la suppression de l'instance, le fichier PDF associé est automatiquement supprimé.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='quote_pdfs',
        verbose_name="Utilisateur"
    )
    words_count = models.IntegerField(
        verbose_name="Nombre de mots",
        help_text="Nombre de mots dans le document traduit"
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Montant total",
        help_text="Montant total du devis en euros"
    )
    language_quote = models.ForeignKey(
        LanguageQuote,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='quote_pdfs',
        verbose_name="Devis de langue",
        help_text="Lien vers le devis de langue utilisé"
    )
    source_language = models.CharField(
        max_length=10,
        verbose_name="Langue source",
        help_text="Code de la langue source (ex: 'fr', 'en')"
    )
    target_language = models.CharField(
        max_length=10,
        verbose_name="Langue cible",
        help_text="Code de la langue cible (ex: 'fr', 'en')"
    )
    pdf_file = models.FileField(
        upload_to='quote/',
        verbose_name="Fichier PDF",
        help_text="Fichier PDF du devis"
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
        help_text="Date et heure de création du PDF"
    )

    class Meta:
        verbose_name = "Devis PDF"
        verbose_name_plural = "Devis PDF"
        ordering = ['-created_at']

    def __str__(self):
        return f"Devis PDF - {self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"

    def delete(self, *args, **kwargs):
        """
        Supprime le fichier PDF associé lors de la suppression de l'instance.
        """
        if self.pdf_file:
            self.pdf_file.delete(save=False)
        super().delete(*args, **kwargs)
