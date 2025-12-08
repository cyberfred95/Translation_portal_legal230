"""
Classes de base pour les tests d'extraction de texte.
"""

from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile


class FileProcessingTestCase(TestCase):
    """Classe de base pour les tests d'extraction de texte."""
    
    def setUp(self):
        """Préparation des tests."""
        self.api_key = "test_api_key"
    
    def create_test_file(self, content: bytes, filename: str) -> InMemoryUploadedFile:
        """
        Crée un fichier en mémoire pour les tests.
        
        Args:
            content: Contenu binaire du fichier
            filename: Nom du fichier avec extension
            
        Returns:
            InMemoryUploadedFile: Fichier en mémoire pour les tests
        """
        file_obj = BytesIO(content)
        return InMemoryUploadedFile(
            file_obj,
            None,
            filename,
            'application/octet-stream',
            len(content),
            None
        )

