from .models import LanguageQuote
from typing import Optional


def get_price_by_language_pair(source_language: str, target_language: str) -> Optional[LanguageQuote]:
    return LanguageQuote.objects.filter(source_language__abbreviation__iexact=source_language,
                                        target_language__abbreviation__iexact=target_language).first()
