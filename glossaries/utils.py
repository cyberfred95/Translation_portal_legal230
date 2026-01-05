"""
Utility functions for glossary operations.
"""
from datetime import datetime
from typing import Optional


def parse_iso_datetime(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse an ISO format datetime string to a datetime object.
    
    Handles both standard ISO format and Z-suffix format (converts Z to +00:00).
    Returns None if the string is empty, None, or cannot be parsed.
    
    Args:
        iso_string: ISO format datetime string (e.g., "2024-01-15T10:30:00Z" or "2024-01-15T10:30:00+00:00")
        
    Returns:
        datetime object if parsing succeeds, None otherwise
    """
    if not iso_string:
        return None
    
    try:
        # Replace Z suffix with +00:00 for timezone-aware parsing
        normalized_string = iso_string.replace('Z', '+00:00')
        return datetime.fromisoformat(normalized_string)
    except (ValueError, AttributeError):
        return None


def format_glossary_for_frontend(glossary_data: dict) -> dict:
    """
    Transform a glossary dictionary from LARA API format to frontend format.
    
    Args:
        glossary_data: Dictionary from LARA API with keys like 'glossary_id', 'name', etc.
        
    Returns:
        Dictionary formatted for frontend consumption
    """
    display_name = glossary_data.get('user_glossary_name') or glossary_data.get('name', '')
    target_languages = glossary_data.get('target_languages', '')
    target_language = target_languages.split(',')[0] if target_languages else ''
    
    return {
        'id': glossary_data.get('glossary_id', ''),
        'name': display_name,
        'source_language': glossary_data.get('source_language', ''),
        'target_language': target_language,
        'created_at': parse_iso_datetime(glossary_data.get('generated_at')),
    }

