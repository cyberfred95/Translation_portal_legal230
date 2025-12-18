from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import LanguageQuote, QuotePDF

@admin.register(LanguageQuote)
class LanguageQuoteAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'price')


@admin.register(QuotePDF)
class QuotePDFAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user_display',
        'words_count',
        'total_amount_display',
        'language_pair_display',
        'language_quote_link',
        'created_at',
        'pdf_file_link'
    )
    list_filter = ('created_at', 'source_language', 'target_language')
    search_fields = ('user__username', 'user__email', 'source_language', 'target_language')
    readonly_fields = ('created_at', 'pdf_file_preview')
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Informations utilisateur', {
            'fields': ('user',)
        }),
        ('Informations du devis', {
            'fields': ('words_count', 'total_amount', 'language_quote', 'source_language', 'target_language')
        }),
        ('Fichier PDF', {
            'fields': ('pdf_file', 'pdf_file_preview')
        }),
        ('Dates', {
            'fields': ('created_at',)
        }),
    )

    def user_display(self, obj):
        """Affiche l'utilisateur avec son email."""
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        return "-"
    user_display.short_description = "Utilisateur"

    def total_amount_display(self, obj):
        """Affiche le montant total formaté."""
        return f"{obj.total_amount} €"
    total_amount_display.short_description = "Montant total"

    def language_pair_display(self, obj):
        """Affiche la paire de langues."""
        return f"{obj.source_language.upper()} → {obj.target_language.upper()}"
    language_pair_display.short_description = "Paire de langues"

    def language_quote_link(self, obj):
        """Affiche un lien vers le LanguageQuote."""
        if obj.language_quote:
            url = reverse('admin:quoting_languagequote_change', args=[obj.language_quote.pk])
            return format_html('<a href="{}">{}</a>', url, str(obj.language_quote))
        return "-"
    language_quote_link.short_description = "Devis de langue"

    def _format_pdf_link(self, obj, show_placeholder=False):
        """
        Helper pour formater le lien PDF.
        
        Args:
            obj: Instance QuotePDF
            show_placeholder: Si True, affiche un message si le PDF n'est pas disponible
            
        Returns:
            str: HTML du lien ou message
        """
        if obj.pdf_file:
            return format_html(
                '<a href="{}" target="_blank">Télécharger le PDF</a>',
                obj.pdf_file.url
            )
        return "Le PDF sera disponible après la sauvegarde." if show_placeholder else "-"

    def pdf_file_link(self, obj):
        """Affiche un lien vers le fichier PDF dans la liste."""
        return self._format_pdf_link(obj)
    pdf_file_link.short_description = "Fichier PDF"

    def pdf_file_preview(self, obj):
        """Affiche un aperçu du lien PDF dans le formulaire d'édition."""
        return self._format_pdf_link(obj, show_placeholder=True)
    pdf_file_preview.short_description = "Aperçu du PDF"