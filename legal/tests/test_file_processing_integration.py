"""
Tests d'intégration pour le service d'extraction de texte.

Ces tests vérifient que le nouveau service fonctionne correctement
avec le code existant (get_text_from_file, StatsProcessor, etc.).
"""

from django.test import TestCase

from legal.helpers import get_text_from_file
from stats.calculator import StatsProcessor
from legal.tests.base import FileProcessingTestCase


class IntegrationTestCase(FileProcessingTestCase):
    """Tests d'intégration avec le code existant."""
    
    def test_get_text_from_file_integration(self):
        """
        Test que get_text_from_file fonctionne avec le nouveau service.
        
        Cette fonction est utilisée dans file_translate() et LanguageDetectView.
        """
        content = b"Premier paragraphe avec plusieurs mots.\nDeuxieme paragraphe."
        file = self.create_test_file(content, "test.txt")
        
        words, texts = get_text_from_file(file, self.api_key)
        
        self.assertIsInstance(words, list)
        self.assertIsInstance(texts, list)
        self.assertGreater(len(texts), 0)
        for text in texts:
            self.assertIsInstance(text, str)
    
    def test_stats_processor_get_texts(self):
        """Test que StatsProcessor.get_texts() fonctionne avec le nouveau service."""
        content = b"Test content for stats processor"
        file = self.create_test_file(content, "test.txt")
        
        processor = StatsProcessor(self.api_key)
        result = processor.get_texts(file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)
        if result["texts"]:
            self.assertIn("text", result["texts"][0])
    
    def test_stats_processor_get_chars(self):
        """Test que StatsProcessor.get_chars() fonctionne avec le nouveau service."""
        content = b"Test content with exactly 35 characters"
        file = self.create_test_file(content, "test.txt")
        
        processor = StatsProcessor(self.api_key)
        chars_count = processor.get_chars(file)
        
        self.assertIsInstance(chars_count, int)
        self.assertGreater(chars_count, 0)
    
    def test_pdf_not_supported(self):
        """
        Test que les PDF ne sont pas supportés directement.
        
        Les PDF doivent être convertis en DOCX avant l'extraction.
        """
        content = b"%PDF-1.4 fake pdf content"
        file = self.create_test_file(content, "test.pdf")
        
        processor = StatsProcessor(self.api_key)
        
        with self.assertRaises(ValueError) as context:
            processor.get_texts(file)
        
        self.assertIn("PDF", str(context.exception))
        self.assertIn("converti", str(context.exception))
    
    def test_unsupported_format(self):
        """Test avec un format non supporté."""
        content = b"Some content"
        file = self.create_test_file(content, "test.xyz")
        
        processor = StatsProcessor(self.api_key)
        
        with self.assertRaises(ValueError) as context:
            processor.get_texts(file)
        
        self.assertIn("non supporté", str(context.exception))
    
    def test_file_seek_after_extraction(self):
        """
        Test que le fichier est correctement repositionné après extraction.
        
        Important pour que le fichier puisse être réutilisé après extraction.
        """
        content = b"Test content that should be readable after extraction"
        file = self.create_test_file(content, "test.txt")
        
        processor = StatsProcessor(self.api_key)
        processor.get_texts(file)
        
        file.seek(0)
        self.assertEqual(file.read(), content)
    
    def test_multiple_extractions_same_file(self):
        """Test que le même fichier peut être extrait plusieurs fois."""
        content = b"Content to extract multiple times"
        file = self.create_test_file(content, "test.txt")
        
        processor = StatsProcessor(self.api_key)
        result1 = processor.get_texts(file)
        result2 = processor.get_texts(file)
        
        self.assertEqual(result1, result2)
