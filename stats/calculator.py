import json
import os
import base64
import tempfile
import logging
from io import BytesIO

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile
from preferences import preferences

# Configuration du logger
logger = logging.getLogger(__name__)


class StatsProcessor:

    def __init__(self, api_key):
        self._api_key = api_key

    file_extension_route_mapping = {
        '.docx': 'word',
        '.pptx': 'powerpoint',
        '.txt': 'text',
        '.pdf': 'word',
        '.xlsx': 'excel',
    }

    def get_files_processing_api_url(self, file_extension):
        return f"{settings.FILES_PROCESSING_API_URL}/api/{self.file_extension_route_mapping[file_extension]}"

    def get_texts(self, file: InMemoryUploadedFile):
        logger.info(f"Traitement du fichier: {file.name}")
        file_extension = os.path.splitext(file.name)[1]
        file_name = file.name
        file_content = file.read()
        logger.debug(f"Extension: {file_extension}, Taille: {len(file_content)} bytes")
        
        if file_extension == '.pdf':
            conversion_method = getattr(settings, 'CONVERSION_METHOD', 'custommt')
            logger.info(f"Conversion PDF requise - Méthode: {conversion_method}")
            
            if conversion_method == 'adobe':
                logger.info("Conversion Adobe PDF Services")
                try:
                    file_content = self._convert_pdf_with_adobe(file_content, file_name)
                    logger.info("Conversion Adobe réussie")
                except Exception as e:
                    logger.error(f"Erreur conversion Adobe: {e}")
                    raise
            else:
                # Default to CustomMT conversion
                logger.info("Conversion CustomMT")
                try:
                    converted_file_response = requests.post(
                        f"{settings.FILES_PROCESSING_API_URL}/api/pdf/convert",
                        headers={
                            "Content-Type": file_extension,
                            "Content-Disposition": f'attachment; '
                                                   f'filename="{file_name}"',
                        },
                        data=file_content
                    )
                    logger.debug(f"Réponse CustomMT: Status {converted_file_response.status_code}")
                    file_content = converted_file_response.content
                    logger.info(f"Conversion CustomMT réussie, taille: {len(file_content)} bytes")
                except Exception as e:
                    logger.error(f"Erreur conversion CustomMT: {e}")
                    raise
            file_extension = '.docx'
            logger.debug(f"Extension changée vers: {file_extension}")

        logger.debug(f"Extraction de texte pour {file_extension}")
        export_url = self.get_files_processing_api_url(file_extension) + '/export'
        logger.debug(f"URL d'export: {export_url}")
        
        try:
            response = requests.post(
                export_url,
                headers={
                    "Content-Type": file_extension,
                    "Content-Disposition": f'attachment; '
                                           f'filename="{file_name}"',
                },
                data=file_content
            )
            logger.debug(f"Réponse export: Status {response.status_code}")
            file.seek(0)
            
            if response.status_code == 200:
                result = response.json()
                logger.info(f"Extraction réussie, segments: {len(result.get('texts', []))}")
                return result
            else:
                logger.error(f"Erreur export: {response.status_code} - {response.text}")
                response.raise_for_status()
                
        except Exception as e:
            logger.error(f"Exception extraction de texte: {e}")
            raise

    def _get_adobe_access_token(self):
        """Obtenir un token d'accès Adobe via OAuth 2.0"""
        auth_url = "https://ims-na1.adobelogin.com/ims/token/v3"
        logger.debug(f"Authentification Adobe: {auth_url}")
        
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        data = {
            'client_id': getattr(settings, 'ADOBE_CLIENT_ID', None),
            'client_secret': getattr(settings, 'ADOBE_CLIENT_SECRET', None),
            'grant_type': 'client_credentials',
            'scope': 'openid,AdobeID,read_organizations,additional_info.projectedProductContext,additional_info.roles'
        }
        
        if not data['client_id'] or not data['client_secret']:
            raise Exception("Credentials Adobe manquants dans les settings")
        
        try:
            response = requests.post(auth_url, headers=headers, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            access_token = token_data.get('access_token')
            
            if not access_token:
                raise Exception("Pas de token d'accès reçu")
            
            expires_in = token_data.get('expires_in', 'N/A')
            logger.info(f"Token Adobe obtenu, expire dans: {expires_in} secondes")
            return access_token
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur authentification Adobe: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Réponse: {e.response.text}")
            raise Exception(f"Erreur d'authentification Adobe: {e}")

    def _convert_pdf_with_adobe(self, pdf_content, filename):
        """Convertir un PDF en DOCX en utilisant l'API Adobe PDF Services"""
        logger.info(f"Conversion Adobe pour {filename}, taille: {len(pdf_content)} bytes")
        
        try:
            # Étape 1: Authentification
            logger.debug("Récupération token Adobe")
            access_token = self._get_adobe_access_token()
            
            # Étape 2: Upload du fichier PDF
            logger.debug("Upload PDF vers Adobe")
            asset_id = self._upload_pdf_to_adobe(pdf_content, filename, access_token)
            
            # Étape 3: Conversion PDF vers DOCX
            logger.debug("Conversion PDF vers DOCX")
            job_result = self._start_pdf_conversion(asset_id, access_token)
            
            # Étape 4: Téléchargement du résultat
            logger.debug("Téléchargement DOCX converti")
            docx_content = self._download_converted_file(job_result, access_token)
            
            logger.info(f"Conversion Adobe réussie, taille DOCX: {len(docx_content)} bytes")
            return docx_content
            
        except Exception as e:
            logger.error(f"Erreur conversion Adobe: {e}")
            # En cas d'erreur avec Adobe, fallback vers CustomMT
            logger.info("Fallback vers CustomMT")
            try:
                converted_file_response = requests.post(
                    f"{settings.FILES_PROCESSING_API_URL}/api/pdf/convert",
                    headers={
                        "Content-Type": ".pdf",
                        "Content-Disposition": f'attachment; filename="{filename}"',
                    },
                    data=pdf_content
                )
                converted_file_response.raise_for_status()
                logger.info("Fallback CustomMT réussi")
                return converted_file_response.content
            except Exception as fallback_error:
                logger.error(f"Erreur fallback CustomMT: {fallback_error}")
                raise Exception(f"Erreur Adobe: {e}. Erreur fallback CustomMT: {fallback_error}")

    def _upload_pdf_to_adobe(self, pdf_content, filename, access_token):
        """Upload un fichier PDF vers Adobe et retourne l'asset ID"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-api-key': getattr(settings, 'ADOBE_CLIENT_ID'),
            'x-gw-ims-org-id': getattr(settings, 'ADOBE_ORGANIZATION_ID'),
            'Content-Type': 'application/json'
        }
        
        # Étape 1: Obtenir une URL d'upload
        upload_url = "https://pdf-services.adobe.io/assets"
        payload = {"mediaType": "application/pdf"}
        
        response = requests.post(upload_url, headers=headers, json=payload)
        response.raise_for_status()
        
        upload_data = response.json()
        upload_uri = upload_data['uploadUri']
        asset_id = upload_data['assetID']
        
        logger.debug(f"URL d'upload obtenue, Asset ID: {asset_id}")
        
        # Étape 2: Upload du fichier PDF
        upload_headers = {'Content-Type': 'application/pdf'}
        upload_response = requests.put(upload_uri, data=pdf_content, headers=upload_headers)
        upload_response.raise_for_status()
        
        logger.debug("Fichier PDF uploadé avec succès")
        return asset_id

    def _start_pdf_conversion(self, asset_id, access_token):
        """Démarre la conversion PDF vers DOCX et attend le résultat"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-api-key': getattr(settings, 'ADOBE_CLIENT_ID'),
            'x-gw-ims-org-id': getattr(settings, 'ADOBE_ORGANIZATION_ID'),
            'Content-Type': 'application/json'
        }
        
        # Lancer la conversion
        export_url = "https://pdf-services.adobe.io/operation/exportpdf"
        payload = {
            "assetID": asset_id,
            "targetFormat": "docx"
        }
        
        response = requests.post(export_url, headers=headers, json=payload)
        
        if response.status_code == 201:
            # Job asynchrone créé
            job_url = response.headers.get('location')
            if not job_url:
                raise Exception("URL de job non trouvée dans les headers")
            
            logger.debug(f"Job de conversion créé: {job_url}")
            return self._wait_for_conversion_completion(job_url, access_token)
        else:
            response.raise_for_status()

    def _wait_for_conversion_completion(self, job_url, access_token, max_wait=300):
        """Attend la completion de la conversion"""
        headers = {
            'Authorization': f'Bearer {access_token}',
            'x-api-key': getattr(settings, 'ADOBE_CLIENT_ID'),
            'x-gw-ims-org-id': getattr(settings, 'ADOBE_ORGANIZATION_ID')
        }
        
        import time
        start_time = time.time()
        poll_count = 0
        
        while time.time() - start_time < max_wait:
            poll_count += 1
            try:
                response = requests.get(job_url, headers=headers)
                response.raise_for_status()
                
                job_status = response.json()
                status = job_status.get('status', 'unknown')
                
                logger.debug(f"Poll #{poll_count}: Status = {status}")
                
                if status == 'done':
                    logger.debug("Conversion terminée avec succès")
                    return job_status
                elif status == 'failed':
                    error_info = job_status.get('error', 'Erreur inconnue')
                    raise Exception(f"Conversion échouée: {error_info}")
                elif status in ['in_progress', 'running', 'pending']:
                    time.sleep(5)  # Attendre 5 secondes
                else:
                    logger.debug(f"Status inattendu: {status}")
                    time.sleep(5)
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Erreur lors de la vérification du job: {e}")
                time.sleep(5)
        
        raise Exception("Timeout: La conversion a pris trop de temps")

    def _download_converted_file(self, job_result, access_token):
        """Télécharge le fichier DOCX converti"""
        asset_info = job_result.get('asset')
        if not asset_info:
            raise Exception("Pas d'information d'asset dans le résultat")
        
        download_uri = asset_info.get('downloadUri')
        if not download_uri:
            raise Exception("Pas d'URI de téléchargement trouvée")
        
        logger.debug(f"Téléchargement depuis: {download_uri}")
        
        response = requests.get(download_uri)
        response.raise_for_status()
        
        logger.debug(f"Fichier téléchargé, taille: {len(response.content)} bytes")
        return response.content

    def get_chars(self, file):
        logger.info(f"Calcul des caractères pour {file.name}")
        try:
            response = self.get_texts(file)
            if response and 'texts' in response:
                chars = 0
                for paragraph in response['texts']:
                    chars += len(paragraph['text'])
                logger.info(f"Caractères calculés: {chars}")
                return chars
            else:
                logger.error("Réponse invalide lors du calcul des caractères")
                return 0
        except Exception as e:
            logger.error(f"Erreur calcul des caractères: {e}")
            return 0

    def get_template_name(self, source_language, target_language, domain_name):
        response = requests.post(
            preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "translation/get_template_by_language_pair_and_domain",
            headers={
                "token": self._api_key
            },
            data={
                "source_language": source_language,
                "target_language": target_language,
                "domain_name": domain_name
            }
        )
        return response.json().get('name')

    def send_request(self,
                     texts: list,
                     user_uuid,
                     domain_name,
                     source_language,
                     target_language,
                     file_name='Text translate',
                     words_count=None,
                     ):
        template_name = self.get_template_name(source_language, target_language, domain_name)
        response = requests.post(
            preferences.StatisticSettings.URL + "add_statistic/",
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-KEY': self._api_key,
            },
            data={
                "messages": texts,
                "uuid": user_uuid,
                'template_name': template_name,
                'file_name': file_name,
                'meta': json.dumps(
                    {
                        "words_count": words_count
                    }
                )
            }
        )

    def send_writing_request(self,
                             texts: list,
                             user_uuid,
                             file_name='Text writing',
                             gpt_model='gpt-3.5-turbo-0613'):
        response = requests.post(
            preferences.StatisticSettings.URL + "add_writing_statistic/",
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-KEY': self._api_key,
            },
            data={
                "messages": texts,
                "uuid": user_uuid,
                'file_name': file_name,
                "gpt_model": gpt_model,
            }

        )
