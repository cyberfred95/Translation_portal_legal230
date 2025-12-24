"""
Classes de base pour les tests d'extraction de texte.
"""

import os
from io import BytesIO
from django.test import TestCase
from django.core.files.uploadedfile import InMemoryUploadedFile


class FileProcessingTestCase(TestCase):
    """Classe de base pour les tests d'extraction de texte."""
    
    # Chemin vers le dossier des fixtures
    FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')
    
    def setUp(self):
        """Préparation des tests."""
        self.api_key = "test_api_key"
    
    def load_fixture_file(self, filename: str) -> InMemoryUploadedFile:
        """
        Charge un fichier de fixture depuis le dossier fixtures.
        
        Args:
            filename: Nom du fichier (ex: 'test_docx.docx')
            
        Returns:
            InMemoryUploadedFile: Fichier en mémoire chargé depuis la fixture
            
        Raises:
            FileNotFoundError: Si le fichier n'existe pas
        """
        fixture_path = os.path.join(self.FIXTURES_DIR, filename)
        
        if not os.path.exists(fixture_path):
            raise FileNotFoundError(f"Fixture non trouvée: {fixture_path}")
        
        with open(fixture_path, 'rb') as f:
            content = f.read()
        
        return self.create_test_file(content, filename)
    
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
    
    def assert_result_format(self, result_dict: dict):
        """
        Vérifie que le format de résultat correspond au format standardisé.
        
        Args:
            result_dict: Dictionnaire de résultat à vérifier
        """
        self.assertIn("texts", result_dict)
        self.assertIsInstance(result_dict["texts"], list)
        if result_dict["texts"]:
            self.assertIn("text", result_dict["texts"][0])
            self.assertIsInstance(result_dict["texts"][0]["text"], str)
    
    def skip_if_dependency_missing(self, extractor_class, dependency_name: str):
        """
        Helper pour tester si une dépendance est disponible.
        
        Args:
            extractor_class: Classe de l'extracteur à tester
            dependency_name: Nom de la dépendance (pour le message)
            
        Raises:
            SkipTest: Si la dépendance n'est pas disponible
        """
        try:
            extractor_class()
        except ImportError:
            self.skipTest(f"{dependency_name} n'est pas installé")
