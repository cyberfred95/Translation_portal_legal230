import logging
import os

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile

from legal.services.file_processing import FileTextExtractorFactory
from legal.services.adobe_pdf import AdobePDFService

# Configuration du logger
logger = logging.getLogger(__name__)


class StatsProcessor:
    """Processeur de statistiques pour les fichiers."""

    PDF_EXTENSION = '.pdf'

    def __init__(self, api_key):
        self._api_key = api_key

    def get_texts(self, file: InMemoryUploadedFile) -> dict:
        """
        Extrait le texte d'un fichier en utilisant le service local.
        
        Les fichiers PDF sont automatiquement convertis en DOCX avant l'extraction.
        
        Args:
            file: Fichier en mémoire à traiter
            
        Returns:
            dict: Résultat au format {"texts": [{"text": "..."}]}
            
        Raises:
            ValueError: Si le format n'est pas supporté
            Exception: Si la conversion PDF échoue
        """
        file_extension = self._get_file_extension(file)
        logger.info(f"Traitement du fichier: {file.name} (extension: {file_extension})")
        
        # Si c'est un PDF, le convertir en DOCX d'abord
        if file_extension == self.PDF_EXTENSION:
            logger.info("Conversion PDF requise avant l'extraction")
            file = self._convert_pdf_to_docx(file)
            logger.info("Conversion PDF réussie, extraction du texte du DOCX")
        
        try:
            return FileTextExtractorFactory.extract_text(file)
        except ValueError as e:
            raise ValueError(
                f"Format de fichier non supporté: {file_extension}. "
                f"Formats supportés: {', '.join(FileTextExtractorFactory.get_supported_extensions())}"
            ) from e

    def _convert_pdf_to_docx(self, pdf_file: InMemoryUploadedFile) -> InMemoryUploadedFile:
        """
        Convertit un fichier PDF en DOCX en utilisant Adobe PDF Services.
        
        Args:
            pdf_file: Fichier PDF en mémoire
            
        Returns:
            InMemoryUploadedFile: Fichier DOCX converti
            
        Raises:
            Exception: Si la conversion échoue
        """
        adobe_service = AdobePDFService()
        return adobe_service.convert_pdf_to_docx(pdf_file)

    def get_chars(self, file: InMemoryUploadedFile) -> int:
        """
        Calcule le nombre de caractères dans un fichier.
        
        Args:
            file: Fichier en mémoire à traiter
            
        Returns:
            int: Nombre total de caractères
        """
        result = self.get_texts(file)
        return sum(len(paragraph['text']) for paragraph in result['texts'])

    @staticmethod
    def _get_file_extension(file: InMemoryUploadedFile) -> str:
        """Extrait l'extension du fichier en minuscules."""
        return os.path.splitext(file.name)[1].lower()

    def send_writing_request(self,
                             texts: list,
                             user_uuid,
                             file_name='Text writing',
                             gpt_model='gpt-3.5-turbo-0613'):
        response = requests.post(
            settings.STATS_API_URL + "add_writing_statistic/",
            headers={
                'token': settings.STATS_API_KEY,
                'X-API-KEY': self._api_key,
            },
            data={
                "messages": texts,
                "uuid": user_uuid,
                'file_name': file_name,
                "gpt_model": gpt_model,
            }

        )
