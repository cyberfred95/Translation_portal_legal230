"""
Service de conversion PDF vers DOCX utilisant Adobe PDF Services.

Ce module fournit une interface pour convertir des fichiers PDF en DOCX
en utilisant l'API Adobe PDF Services.
"""

import logging
import os
import time
from io import BytesIO

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile

# Configuration du logger
logger = logging.getLogger(__name__)


class AdobePDFService:
    """Service pour convertir des PDF en DOCX via Adobe PDF Services."""

    # URLs de l'API Adobe
    AUTH_URL = "https://ims-na1.adobelogin.com/ims/token/v3"
    ASSETS_URL = "https://pdf-services.adobe.io/assets"
    EXPORT_URL = "https://pdf-services.adobe.io/operation/exportpdf"

    # Timeout pour la conversion (en secondes)
    DEFAULT_MAX_WAIT = 300  # 5 minutes
    POLL_INTERVAL = 5  # secondes entre chaque vérification
    
    # Scope OAuth 2.0 pour l'authentification Adobe
    OAUTH_SCOPE = (
        'openid,AdobeID,read_organizations,'
        'additional_info.projectedProductContext,additional_info.roles'
    )
    
    # Statuts de job Adobe
    STATUS_DONE = 'done'
    STATUS_FAILED = 'failed'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RUNNING = 'running'
    STATUS_PENDING = 'pending'
    STATUS_IN_PROGRESS_VARIANTS = [STATUS_IN_PROGRESS, STATUS_RUNNING, STATUS_PENDING]
    
    # Code HTTP pour création de ressource asynchrone
    HTTP_CREATED = 201

    def __init__(self):
        """Initialise le service Adobe PDF."""
        self._client_id = getattr(settings, 'ADOBE_CLIENT_ID', None)
        self._client_secret = getattr(settings, 'ADOBE_CLIENT_SECRET', None)
        self._organization_id = getattr(settings, 'ADOBE_ORGANIZATION_ID', None)

        if not all([self._client_id, self._client_secret, self._organization_id]):
            raise ValueError(
                "Les credentials Adobe sont manquants. "
                "Vérifiez ADOBE_CLIENT_ID, ADOBE_CLIENT_SECRET et ADOBE_ORGANIZATION_ID dans les settings."
            )
    
    def _get_api_headers(self, access_token: str, content_type: str = 'application/json') -> dict:
        """
        Construit les headers pour les requêtes API Adobe.
        
        Args:
            access_token: Token d'accès Adobe
            content_type: Type de contenu (défaut: application/json)
            
        Returns:
            dict: Headers pour les requêtes API
        """
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-api-key': self._client_id,
            'x-gw-ims-org-id': self._organization_id,
        }
        if content_type:
            headers['Content-Type'] = content_type
        return headers
    
    def _handle_request_error(self, error: requests.exceptions.RequestException, context: str):
        """
        Gère les erreurs de requête et lève une exception appropriée.
        
        Args:
            error: Exception de requête
            context: Contexte de l'erreur (ex: "l'authentification", "l'upload du PDF")
            
        Raises:
            Exception: Exception avec message d'erreur détaillé
        """
        error_msg = f"Erreur lors de {context} Adobe: {error}"
        if hasattr(error, 'response') and error.response is not None:
            logger.error(f"Réponse: {error.response.text}")
        raise Exception(error_msg)

    def convert_pdf_to_docx(self, pdf_file: InMemoryUploadedFile) -> InMemoryUploadedFile:
        """
        Convertit un fichier PDF en DOCX.

        Args:
            pdf_file: Fichier PDF en mémoire à convertir

        Returns:
            InMemoryUploadedFile: Fichier DOCX converti en mémoire

        Raises:
            ValueError: Si les credentials Adobe sont manquants
            Exception: Si la conversion échoue
        """
        logger.info(f"Conversion Adobe PDF vers DOCX pour: {pdf_file.name}")

        # Lire le contenu du PDF
        pdf_content = pdf_file.read()
        pdf_file.seek(0)  # Réinitialiser la position

        try:
            logger.debug("Récupération du token d'accès Adobe")
            access_token = self._get_access_token()

            logger.debug("Upload du PDF vers Adobe")
            asset_id = self._upload_pdf(pdf_content, pdf_file.name, access_token)

            logger.debug("Démarrage de la conversion PDF vers DOCX")
            job_result = self._start_conversion(asset_id, access_token)

            logger.debug("Téléchargement du fichier DOCX converti")
            docx_content = self._download_result(job_result)

            docx_filename = self._get_docx_filename(pdf_file.name)
            docx_file = self._create_in_memory_file(docx_content, docx_filename)

            logger.info(f"Conversion Adobe réussie: {pdf_file.name} -> {docx_filename}")
            return docx_file

        except Exception as e:
            logger.error(f"Erreur lors de la conversion Adobe: {e}")
            raise

    def _get_access_token(self) -> str:
        """
        Obtient un token d'accès Adobe via OAuth 2.0.

        Returns:
            str: Token d'accès

        Raises:
            Exception: Si l'authentification échoue
        """
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': self._client_id,
            'client_secret': self._client_secret,
            'grant_type': 'client_credentials',
            'scope': self.OAUTH_SCOPE
        }

        try:
            response = requests.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()

            token_data = response.json()
            access_token = token_data.get('access_token')

            if not access_token:
                raise Exception("Pas de token d'accès reçu dans la réponse")

            expires_in = token_data.get('expires_in', 'N/A')
            logger.debug(f"Token Adobe obtenu, expire dans: {expires_in} secondes")
            return access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur d'authentification Adobe: {e}")
            self._handle_request_error(e, "l'authentification")

    def _upload_pdf(self, pdf_content: bytes, filename: str, access_token: str) -> str:
        """
        Upload un fichier PDF vers Adobe et retourne l'asset ID.

        Args:
            pdf_content: Contenu binaire du PDF
            filename: Nom du fichier
            access_token: Token d'accès Adobe

        Returns:
            str: Asset ID du fichier uploadé

        Raises:
            Exception: Si l'upload échoue
        """
        headers = self._get_api_headers(access_token)
        payload = {"mediaType": "application/pdf"}

        try:
            # Obtenir une URL d'upload
            response = requests.post(self.ASSETS_URL, headers=headers, json=payload)
            response.raise_for_status()

            upload_data = response.json()
            upload_uri = upload_data['uploadUri']
            asset_id = upload_data['assetID']

            logger.debug(f"URL d'upload obtenue, Asset ID: {asset_id}")

            # Upload du fichier PDF
            upload_headers = {'Content-Type': 'application/pdf'}
            upload_response = requests.put(upload_uri, data=pdf_content, headers=upload_headers)
            upload_response.raise_for_status()

            logger.debug("Fichier PDF uploadé avec succès")
            return asset_id

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de l'upload du PDF: {e}")
            self._handle_request_error(e, "l'upload du PDF")

    def _start_conversion(self, asset_id: str, access_token: str) -> dict:
        """
        Démarre la conversion PDF vers DOCX et attend le résultat.

        Args:
            asset_id: ID de l'asset PDF uploadé
            access_token: Token d'accès Adobe

        Returns:
            dict: Résultat de la conversion

        Raises:
            Exception: Si la conversion échoue
        """
        headers = self._get_api_headers(access_token)

        payload = {
            "assetID": asset_id,
            "targetFormat": "docx"
        }

        try:
            response = requests.post(self.EXPORT_URL, headers=headers, json=payload)

            if response.status_code == self.HTTP_CREATED:
                job_url = response.headers.get('location')
                if not job_url:
                    raise Exception("URL de job non trouvée dans les headers")

                logger.debug(f"Job de conversion créé: {job_url}")
                return self._wait_for_completion(job_url, access_token)
            
            response.raise_for_status()

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du démarrage de la conversion: {e}")
            self._handle_request_error(e, "du démarrage de la conversion")

    def _wait_for_completion(self, job_url: str, access_token: str, max_wait: int = None) -> dict:
        """
        Attend la completion de la conversion.

        Args:
            job_url: URL du job de conversion
            access_token: Token d'accès Adobe
            max_wait: Temps maximum d'attente en secondes (défaut: DEFAULT_MAX_WAIT)

        Returns:
            dict: Résultat de la conversion

        Raises:
            Exception: Si la conversion échoue ou dépasse le timeout
        """
        if max_wait is None:
            max_wait = self.DEFAULT_MAX_WAIT

        headers = self._get_api_headers(access_token, content_type=None)
        start_time = time.time()
        poll_count = 0

        while time.time() - start_time < max_wait:
            poll_count += 1
            job_status = self._poll_job_status(job_url, headers, poll_count)
            
            if job_status:
                return job_status
            
            time.sleep(self.POLL_INTERVAL)

        raise Exception(f"Timeout: La conversion a pris plus de {max_wait} secondes")
    
    def _poll_job_status(self, job_url: str, headers: dict, poll_count: int) -> dict:
        """
        Interroge le statut du job de conversion.
        
        Args:
            job_url: URL du job de conversion
            headers: Headers pour la requête
            poll_count: Numéro du poll (pour le logging)
            
        Returns:
            dict: Résultat si terminé, None si en cours
            
        Raises:
            Exception: Si la conversion a échoué
        """
        try:
            response = requests.get(job_url, headers=headers)
            response.raise_for_status()

            job_status = response.json()
            status = job_status.get('status', 'unknown')

            logger.debug(f"Poll #{poll_count}: Status = {status}")

            if status == self.STATUS_DONE:
                logger.debug("Conversion terminée avec succès")
                return job_status
            elif status == self.STATUS_FAILED:
                error_info = job_status.get('error', 'Erreur inconnue')
                raise Exception(f"Conversion échouée: {error_info}")
            elif status in self.STATUS_IN_PROGRESS_VARIANTS:
                return None
            else:
                logger.debug(f"Status inattendu: {status}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la vérification du job: {e}")
            return None

    def _download_result(self, job_result: dict) -> bytes:
        """
        Télécharge le fichier DOCX converti.

        Args:
            job_result: Résultat du job de conversion

        Returns:
            bytes: Contenu binaire du fichier DOCX

        Raises:
            Exception: Si le téléchargement échoue
        """
        asset_info = job_result.get('asset')
        if not asset_info:
            raise Exception("Pas d'information d'asset dans le résultat")

        download_uri = asset_info.get('downloadUri')
        if not download_uri:
            raise Exception("Pas d'URI de téléchargement trouvée")

        logger.debug(f"Téléchargement depuis: {download_uri}")

        try:
            response = requests.get(download_uri)
            response.raise_for_status()

            logger.debug(f"Fichier téléchargé, taille: {len(response.content)} bytes")
            return response.content

        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du téléchargement: {e}")
            raise Exception(f"Erreur lors du téléchargement: {e}")

    @staticmethod
    def _get_docx_filename(pdf_filename: str) -> str:
        """
        Génère un nom de fichier DOCX à partir d'un nom de fichier PDF.

        Args:
            pdf_filename: Nom du fichier PDF

        Returns:
            str: Nom du fichier DOCX
        """
        name, _ = os.path.splitext(pdf_filename)
        return f"{name}.docx"

    @staticmethod
    def _create_in_memory_file(content: bytes, filename: str) -> InMemoryUploadedFile:
        """
        Crée un fichier InMemoryUploadedFile à partir de contenu binaire.

        Args:
            content: Contenu binaire du fichier
            filename: Nom du fichier

        Returns:
            InMemoryUploadedFile: Fichier en mémoire
        """
        file_obj = BytesIO(content)
        return InMemoryUploadedFile(
            file_obj,
            None,
            filename,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            len(content),
            None
        )

