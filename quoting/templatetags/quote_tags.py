"""
Template tags for quote PDF translations using a separate translation domain.

This module provides custom template tags that use a separate translation domain ('quote')
to isolate PDF translations from application translations.
"""
import gettext
import logging
from django import template
from django.utils import translation
from django.conf import settings

from quoting.constants import QUOTE_TRANSLATION_DOMAIN

logger = logging.getLogger(__name__)
register = template.Library()

# Cache for translation objects to avoid reloading on every call
_translation_cache = {}


def _get_locale_path() -> str:
    """Get the locale path from Django settings."""
    return str(settings.LOCALE_PATHS[0]) if settings.LOCALE_PATHS else 'locale'


def _load_quote_translation(language: str) -> gettext.NullTranslations:
    """
    Load translation object for the quote domain.
    
    Args:
        language: Language code (e.g., 'fr', 'en')
        
    Returns:
        Translation object or NullTranslations if not found
    """
    locale_path = _get_locale_path()
    
    try:
        return gettext.translation(
            QUOTE_TRANSLATION_DOMAIN,
            localedir=locale_path,
            languages=[language],
            fallback=True
        )
    except (OSError, IOError) as e:
        logger.warning(f"Could not load quote translation for language '{language}': {e}")
        return gettext.NullTranslations()


def _get_quote_translation():
    """
    Get translation object for the quote domain with the currently active language.
    
    Uses gettext directly to load the 'quote' domain from locale/{lang}/LC_MESSAGES/quote.mo.
    The language must be activated before calling this function (via translation.activate()).
    
    Returns:
        Translation object or NullTranslations if not found
    """
    current_language = translation.get_language() or settings.LANGUAGE_CODE
    cache_key = f"{QUOTE_TRANSLATION_DOMAIN}_{current_language}"
    
    # Return cached translation if available
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]
    
    # Load and cache translation
    quote_trans = _load_quote_translation(current_language)
    _translation_cache[cache_key] = quote_trans
    
    return quote_trans


def clear_quote_translation_cache():
    """Clear the quote translation cache. Useful when language changes."""
    _translation_cache.clear()


@register.simple_tag
def quote_trans(message):
    """
    Translation tag for quote domain.
    
    Uses the 'quote' translation domain instead of the default 'django' domain.
    This allows separating PDF translations from application translations.
    
    Usage:
        {% quote_trans 'Text to translate' %}
        
    Args:
        message: Text to translate
        
    Returns:
        Translated text or original message if translation not found
    """
    return _get_quote_translation().gettext(message)


@register.tag(name='quote_blocktrans')
def do_quote_blocktrans(parser, token):
    """
    Block translation tag for quote domain with variable support.
    
    Usage:
        {% quote_blocktrans with var1=value1 var2=value2 %}
            Text with {{ var1 }} and {{ var2 }}
        {% endquote_blocktrans %}
    """
    bits = token.split_contents()
    remaining_bits = bits[1:]
    
    vars_dict = {}
    if remaining_bits and remaining_bits[0] == 'with':
        remaining_bits = remaining_bits[1:]
        while remaining_bits and '=' in remaining_bits[0]:
            var_name, var_value = remaining_bits[0].split('=', 1)
            vars_dict[var_name.strip()] = parser.compile_filter(var_value.strip())
            remaining_bits = remaining_bits[1:]
    
    nodelist = parser.parse(('endquote_blocktrans',))
    parser.delete_first_token()
    
    return QuoteBlockTransNode(nodelist, vars_dict)


class QuoteBlockTransNode(template.Node):
    """Node for rendering block translations with variable substitution."""
    
    def __init__(self, nodelist, vars_dict):
        self.nodelist = nodelist
        self.vars_dict = vars_dict
    
    def render(self, context):
        """
        Render the block translation with variable substitution.
        
        Variables are resolved from context, then the content is translated,
        and finally variables are replaced in the translated string.
        """
        # Resolve variables from context
        resolved_vars = {
            var_name: var_filter.resolve(context)
            for var_name, var_filter in self.vars_dict.items()
        }
        
        # Render content (variables in template syntax are already resolved)
        content = self.nodelist.render(context)
        
        # Translate the content
        translated = _get_quote_translation().gettext(content)
        
        # Replace variables in translated string (for Python format placeholders)
        for var_name, var_value in resolved_vars.items():
            translated = translated.replace(f'{{{{ {var_name} }}}}', str(var_value))
            translated = translated.replace(f'{{{{{var_name}}}}}', str(var_value))
        
        return translated

