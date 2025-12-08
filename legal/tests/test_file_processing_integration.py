"""
Tests d'intégration pour le service d'extraction de texte.

Ces tests vérifient que le nouveau service fonctionne correctement
avec le code existant (get_text_from_file, StatsProcessor, etc.).
"""

from unittest.mock import patch, MagicMock
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
        file = self.load_fixture_file("test_txt.txt")
        
        words, texts = get_text_from_file(file, self.api_key)
        
        self.assertIsInstance(words, list)
        self.assertIsInstance(texts, list)
        self.assertGreater(len(texts), 0)
        for text in texts:
            self.assertIsInstance(text, str)
    
    def test_stats_processor_get_texts(self):
        """Test que StatsProcessor.get_texts() fonctionne avec le nouveau service."""
        file = self.load_fixture_file("test_txt.txt")
        
        processor = StatsProcessor(self.api_key)
        result = processor.get_texts(file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)
        if result["texts"]:
            self.assertIn("text", result["texts"][0])
    
    def test_stats_processor_get_texts_docx(self):
        """Test que StatsProcessor.get_texts() fonctionne avec un fichier DOCX réel."""
        file = self.load_fixture_file("test_docx.docx")
        
        processor = StatsProcessor(self.api_key)
        result = processor.get_texts(file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)
        self.assertGreater(len(result["texts"]), 0)
    
    def test_stats_processor_get_chars(self):
        """Test que StatsProcessor.get_chars() fonctionne avec le nouveau service."""
        file = self.load_fixture_file("test_txt.txt")
        
        processor = StatsProcessor(self.api_key)
        chars_count = processor.get_chars(file)
        
        self.assertIsInstance(chars_count, int)
        self.assertGreater(chars_count, 0)
    
    @patch('stats.calculator.AdobePDFService')
    @patch('stats.calculator.FileTextExtractorFactory')
    def test_pdf_conversion_to_docx(self, mock_extractor_factory, mock_adobe_service):
        """
        Test que les PDF sont automatiquement convertis en DOCX avant l'extraction.
        
        Le test mocke le service Adobe et l'extracteur pour éviter les appels réels.
        """
        # Créer un mock du service Adobe
        mock_service_instance = MagicMock()
        mock_adobe_service.return_value = mock_service_instance
        
        # Simuler un fichier DOCX converti
        docx_content = b"PK\x03\x04 fake docx content"
        mock_docx_file = self.create_test_file(docx_content, "test.docx")
        mock_service_instance.convert_pdf_to_docx.return_value = mock_docx_file
        
        # Mock de l'extraction pour retourner un résultat valide
        expected_result = {"texts": [{"text": "Texte extrait du DOCX"}]}
        mock_extractor_factory.extract_text.return_value = expected_result
        
        # Créer un fichier PDF de test
        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = self.create_test_file(pdf_content, "test.pdf")
        
        processor = StatsProcessor(self.api_key)
        
        # Le traitement devrait appeler la conversion puis l'extraction
        result = processor.get_texts(pdf_file)
        
        # Vérifier que la conversion a été appelée
        mock_service_instance.convert_pdf_to_docx.assert_called_once()
        
        # Vérifier que l'extraction a été appelée avec le fichier DOCX converti
        mock_extractor_factory.extract_text.assert_called_once()
        call_args = mock_extractor_factory.extract_text.call_args[0][0]
        self.assertEqual(call_args.name, "test.docx")
        
        # Vérifier que le résultat est valide
        self.assertIsInstance(result, dict)
        self.assertIn("texts", result)
        self.assertEqual(result, expected_result)
    
    @patch('stats.calculator.AdobePDFService')
    def test_pdf_conversion_error(self, mock_adobe_service):
        """
        Test que les erreurs de conversion PDF sont correctement propagées.
        """
        # Créer un mock du service Adobe qui lève une exception
        mock_service_instance = MagicMock()
        mock_adobe_service.return_value = mock_service_instance
        mock_service_instance.convert_pdf_to_docx.side_effect = Exception("Erreur de conversion Adobe")
        
        pdf_content = b"%PDF-1.4 fake pdf content"
        pdf_file = self.create_test_file(pdf_content, "test.pdf")
        
        processor = StatsProcessor(self.api_key)
        
        # Le traitement devrait lever une exception
        with self.assertRaises(Exception) as context:
            processor.get_texts(pdf_file)
        
        self.assertIn("conversion", str(context.exception).lower())
    
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
        file = self.load_fixture_file("test_txt.txt")
        file.seek(0)
        original_content = file.read()
        
        processor = StatsProcessor(self.api_key)
        processor.get_texts(file)
        
        file.seek(0)
        self.assertEqual(file.read(), original_content)
    
    def test_multiple_extractions_same_file(self):
        """Test que le même fichier peut être extrait plusieurs fois."""
        file = self.load_fixture_file("test_txt.txt")
        
        processor = StatsProcessor(self.api_key)
        result1 = processor.get_texts(file)
        result2 = processor.get_texts(file)
        
        self.assertEqual(result1, result2)
