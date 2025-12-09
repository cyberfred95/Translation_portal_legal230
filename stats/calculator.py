import logging
import os

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile

from legal.services.file_processing import FileTextExtractorFactory

# Configuration du logger
logger = logging.getLogger(__name__)


class StatsProcessor:
    """Processeur de statistiques pour les fichiers."""

    def __init__(self, api_key):
        self._api_key = api_key

    def get_texts(self, file: InMemoryUploadedFile) -> dict:
        """
        Extrait le texte d'un fichier en utilisant le service local.
        
        Note: Cette méthode ne convertit plus les PDF en DOCX.
        La conversion doit être effectuée avant l'appel à cette méthode.
        
        Args:
            file: Fichier en mémoire à traiter (doit déjà être converti si PDF)
            
        Returns:
            dict: Résultat au format {"texts": [{"text": "..."}]}
            
        Raises:
            ValueError: Si le format n'est pas supporté
        """
        file_extension = self._get_file_extension(file)
        logger.info(f"Traitement du fichier: {file.name} (extension: {file_extension})")
        
        try:
            return FileTextExtractorFactory.extract_text(file)
        except ValueError as e:
            raise ValueError(
                f"Format de fichier non supporté: {file_extension}. "
                f"Formats supportés: {', '.join(FileTextExtractorFactory.get_supported_extensions())}"
            ) from e

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

    # ============================================================================
    # WRITING FUNCTIONALITY - TEMPORARILY DISABLED
    # ============================================================================
    # Cette méthode est temporairement désactivée en prévision d'une refonte.
    # Le code est conservé en commentaire pour référence future.
    # ============================================================================
    # def send_writing_request(self,
    #                          texts: list,
    #                          user_uuid,
    #                          file_name='Text writing',
    #                          gpt_model='gpt-3.5-turbo-0613'):
    #     response = requests.post(
    #         settings.STATS_API_URL + "add_writing_statistic/",
    #         headers={
    #             'token': settings.STATS_API_KEY,
    #             'X-API-KEY': self._api_key,
    #         },
    #         data={
    #             "messages": texts,
    #             "uuid": user_uuid,
    #             'file_name': file_name,
    #             "gpt_model": gpt_model,
    #         }
    #     )
