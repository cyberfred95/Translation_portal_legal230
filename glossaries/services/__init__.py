"""
Glossary services module.

Provides service layer for glossary operations via LARA backend.
"""
from .lara_client import LaraClient
from .glossary_service import LaraGlossaryService

# Backward compatibility alias for migrations and tests
AIGlossaryService = LaraGlossaryService

__all__ = [
    'LaraClient',
    'LaraGlossaryService',
    'AIGlossaryService',
]
