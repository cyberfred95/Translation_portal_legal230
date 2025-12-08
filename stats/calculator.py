import os

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile

from legal.services.file_processing import FileTextExtractorFactory


class StatsProcessor:
    """Processeur de statistiques pour les fichiers."""

    PDF_EXTENSION = '.pdf'
    ERROR_PDF_NOT_SUPPORTED = (
        "Les fichiers PDF doivent être convertis en DOCX avant l'extraction de texte. "
        "Cette méthode ne traite pas les PDF directement."
    )

    def __init__(self, api_key):
        self._api_key = api_key

    def get_texts(self, file: InMemoryUploadedFile) -> dict:
        """
        Extrait le texte d'un fichier en utilisant le service local.
        
        Args:
            file: Fichier en mémoire à traiter
            
        Returns:
            dict: Résultat au format {"texts": [{"text": "..."}]}
            
        Raises:
            ValueError: Si le format n'est pas supporté ou si c'est un PDF
            
        Note:
            Les fichiers PDF doivent être convertis en DOCX avant d'appeler cette méthode.
        """
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension == self.PDF_EXTENSION:
            raise ValueError(self.ERROR_PDF_NOT_SUPPORTED)
        
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
