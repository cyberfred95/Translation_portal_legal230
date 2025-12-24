from .models import LanguageQuote
from typing import Optional


def get_price_by_language_pair(source_language: str, target_language: str) -> Optional[LanguageQuote]:
    """
    Recherche un devis pour une paire de langues donnée.
    
    Args:
        source_language: Code de la langue source (ex: 'en', 'fr', 'FR')
        target_language: Code de la langue cible (ex: 'en', 'fr', 'ES')
    
    Returns:
        LanguageQuote si trouvé, None sinon
    """
    if not source_language or not target_language:
        return None
    
    return LanguageQuote.objects.filter(
        source_language__abbreviation__iexact=source_language,
        target_language__abbreviation__iexact=target_language
    ).first()
