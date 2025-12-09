"""
Tests unitaires pour le service d'extraction de texte.

Ces tests vérifient le format de sortie standardisé et testent
chaque extracteur individuellement.
"""

from legal.services.file_processing import (
    FileTextExtractorFactory,
    WordExtractor,
    PowerPointExtractor,
    ExcelExtractor,
    TextExtractor,
    ExtractionResult,
)
from legal.tests.base import FileProcessingTestCase


class TextExtractorTest(FileProcessingTestCase):
    """Tests pour l'extracteur de fichiers texte."""
    
    def test_extract_simple_text(self):
        """Test d'extraction d'un texte simple."""
        content = b"Premier paragraphe.\nDeuxieme paragraphe.\n"
        file = self.create_test_file(content, "test.txt")
        
        extractor = TextExtractor()
        result = extractor.extract(file)
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertEqual(len(result.texts), 1)
        self.assertIn("Premier paragraphe. Deuxieme paragraphe.", result.texts[0]["text"])
    
    def test_extract_multiple_paragraphs(self):
        """Test d'extraction avec plusieurs paragraphes."""
        content = b"Paragraphe 1\n\nParagraphe 2\n\nParagraphe 3"
        file = self.create_test_file(content, "test.txt")
        
        extractor = TextExtractor()
        result = extractor.extract(file)
        
        self.assertGreaterEqual(len(result.texts), 2)
    
    def test_extract_real_txt_file(self):
        """Test d'extraction avec le fichier TXT réel et vérification du format."""
        file = self.load_fixture_file("test_txt.txt")
        
        extractor = TextExtractor()
        result = extractor.extract(file)
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertGreater(len(result.texts), 0)
        self.assert_result_format(result.to_dict())


class WordExtractorTest(FileProcessingTestCase):
    """Tests pour l'extracteur Word (nécessite python-docx)."""
    
    def test_word_extractor_import(self):
        """Test que python-docx peut être importé."""
        self.skip_if_dependency_missing(WordExtractor, "python-docx")
    
    def test_extract_real_docx_file(self):
        """Test d'extraction avec le fichier DOCX réel et vérification du format."""
        self.skip_if_dependency_missing(WordExtractor, "python-docx")
        extractor = WordExtractor()
        
        file = self.load_fixture_file("test_docx.docx")
        result = extractor.extract(file)
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertGreater(len(result.texts), 0)
        self.assert_result_format(result.to_dict())


class ExcelExtractorTest(FileProcessingTestCase):
    """Tests pour l'extracteur Excel (nécessite openpyxl)."""
    
    def test_excel_extractor_import(self):
        """Test que openpyxl peut être importé."""
        self.skip_if_dependency_missing(ExcelExtractor, "openpyxl")
    
    def test_extract_real_xlsx_file(self):
        """Test d'extraction avec le fichier XLSX réel et vérification du format."""
        self.skip_if_dependency_missing(ExcelExtractor, "openpyxl")
        extractor = ExcelExtractor()
        
        file = self.load_fixture_file("test_xlsx.xlsx")
        result = extractor.extract(file)
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertGreater(len(result.texts), 0)
        self.assert_result_format(result.to_dict())


class PowerPointExtractorTest(FileProcessingTestCase):
    """Tests pour l'extracteur PowerPoint (nécessite python-pptx)."""
    
    def test_powerpoint_extractor_import(self):
        """Test que python-pptx peut être importé."""
        self.skip_if_dependency_missing(PowerPointExtractor, "python-pptx")
    
    def test_extract_real_pptx_file(self):
        """Test d'extraction avec le fichier PPTX réel et vérification du format."""
        self.skip_if_dependency_missing(PowerPointExtractor, "python-pptx")
        extractor = PowerPointExtractor()
        
        file = self.load_fixture_file("test_pptx.pptx")
        result = extractor.extract(file)
        
        self.assertIsInstance(result, ExtractionResult)
        self.assertGreater(len(result.texts), 0)
        self.assert_result_format(result.to_dict())


class FileTextExtractorFactoryTest(FileProcessingTestCase):
    """Tests pour la factory d'extracteurs."""
    
    def test_get_extractor_docx(self):
        """Test de récupération de l'extracteur Word."""
        self.skip_if_dependency_missing(WordExtractor, "python-docx")
        extractor = FileTextExtractorFactory.get_extractor('.docx')
        self.assertIsInstance(extractor, WordExtractor)
    
    def test_get_extractor_pptx(self):
        """Test de récupération de l'extracteur PowerPoint."""
        self.skip_if_dependency_missing(PowerPointExtractor, "python-pptx")
        extractor = FileTextExtractorFactory.get_extractor('.pptx')
        self.assertIsInstance(extractor, PowerPointExtractor)
    
    def test_get_extractor_xlsx(self):
        """Test de récupération de l'extracteur Excel."""
        self.skip_if_dependency_missing(ExcelExtractor, "openpyxl")
        extractor = FileTextExtractorFactory.get_extractor('.xlsx')
        self.assertIsInstance(extractor, ExcelExtractor)
    
    def test_get_extractor_txt(self):
        """Test de récupération de l'extracteur texte."""
        extractor = FileTextExtractorFactory.get_extractor('.txt')
        self.assertIsInstance(extractor, TextExtractor)
    
    def test_get_extractor_unsupported(self):
        """Test avec une extension non supportée."""
        with self.assertRaises(ValueError):
            FileTextExtractorFactory.get_extractor('.pdf')
    
    def test_get_supported_extensions(self):
        """Test de récupération des extensions supportées."""
        extensions = FileTextExtractorFactory.get_supported_extensions()
        self.assertIn('.docx', extensions)
        self.assertIn('.pptx', extensions)
        self.assertIn('.xlsx', extensions)
        self.assertIn('.txt', extensions)
    
    def test_extract_text_method(self):
        """Test de la méthode extract_text qui retourne directement un dict."""
        file = self.load_fixture_file("test_txt.txt")
        
        result = FileTextExtractorFactory.extract_text(file)
        
        self.assertIsInstance(result, dict)
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)


class CompatibilityTest(FileProcessingTestCase):
    """
    Tests de format de sortie standardisé.
    
    Ces tests vérifient que le service retourne le format standardisé attendu.
    """
    
    def test_result_structure_matches_standard_format(self):
        """
        Test que la structure de résultat correspond au format standardisé.
        
        Format attendu:
        {
            "texts": [
                {"text": "Premier paragraphe..."},
                {"text": "Deuxième paragraphe..."}
            ]
        }
        """
        file = self.load_fixture_file("test_txt.txt")
        
        result = FileTextExtractorFactory.extract_text(file)
        
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)
        
        if result["texts"]:
            for text_item in result["texts"]:
                self.assertIn("text", text_item)
                self.assertIsInstance(text_item["text"], str)
    
    def test_empty_file_handling(self):
        """Test de gestion d'un fichier vide."""
        content = b""
        file = self.create_test_file(content, "test.txt")
        
        result = FileTextExtractorFactory.extract_text(file)
        
        self.assertIn("texts", result)
        self.assertIsInstance(result["texts"], list)
    
    def test_file_seek_reset(self):
        """Test que le fichier est repositionné après extraction."""
        file = self.load_fixture_file("test_txt.txt")
        file.seek(0)
        original_content = file.read()
        
        FileTextExtractorFactory.extract_text(file)
        
        file.seek(0)
        self.assertEqual(file.read(), original_content)
