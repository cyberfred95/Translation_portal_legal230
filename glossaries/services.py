import os

import requests
from django.conf import settings
from preferences import preferences

from glossaries.helpers import get_glossary_username
from glossaries.processor import GlossaryProcessor


class AIGlossaryService:

    @staticmethod
    def _prepare_headers():
        return {
            "API-KEY": settings.GLOSSARY_API_KEY
        }

    def create_glossary(self, glossary):
        import logging
        logger = logging.getLogger(__name__)

        prepared_glossary: dict = GlossaryProcessor().form_glossary_object(glossary.file)

        payload = {
            "system": settings.GLOSSARY_SYSTEM,
            "username": get_glossary_username(glossary),
            "glossary": {
                "name": os.path.splitext(os.path.basename(glossary.file.name))[0],
                "description": "",
                "languages": [glossary.source_language.abbreviation.lower(),
                              glossary.target_language.abbreviation.lower()],
                "values": prepared_glossary,
            }
        }

        # Log the payload (without the full values to keep logs readable)
        payload_summary = {
            "system": payload["system"],
            "username": payload["username"],
            "glossary": {
                "name": payload["glossary"]["name"],
                "description": payload["glossary"]["description"],
                "languages": payload["glossary"]["languages"],
                "values_count": len(payload["glossary"]["values"]) if isinstance(payload["glossary"]["values"], (list, dict)) else "unknown"
            }
        }
        logger.info(f"🔵 API CREATE_GLOSSARY - Request payload: {payload_summary}")

        url = preferences.MainSettings.glossaries_url + "create_glossary"
        logger.info(f"🔵 API CREATE_GLOSSARY - URL: {url}")

        try:
            response = requests.post(
                url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=60  # 60 second timeout
            )
        except requests.exceptions.Timeout:
            error_msg = "L'API de glossaire n'a pas répondu dans le délai imparti (timeout de 60 secondes)"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Impossible de se connecter à l'API de glossaire à l'adresse {url}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de la requête à l'API de glossaire: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

        logger.info(f"🔵 API CREATE_GLOSSARY - Status code: {response.status_code}")
        logger.info(f"🔵 API CREATE_GLOSSARY - Response: {response.text[:500]}")  # First 500 chars

        if response.status_code // 100 != 2:
            logger.error(f"❌ API CREATE_GLOSSARY FAILED - Full response: {response.text}")
            error_msg = f"L'API de glossaire a retourné une erreur (HTTP {response.status_code})"
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'error' in error_data:
                    error_msg += f": {error_data['error']}"
                elif isinstance(error_data, dict) and 'detail' in error_data:
                    error_msg += f": {error_data['detail']}"
                else:
                    error_msg += f": {str(error_data)[:200]}"
            except:
                # Not JSON, just include first 200 chars of response
                error_msg += f": {response.text[:200]}"
            raise Exception(error_msg)
        else:
            try:
                glossary_id = response.json().get("glossary_id")
                logger.info(f"✅ API CREATE_GLOSSARY SUCCESS - glossary_id: {glossary_id}")
                return glossary_id
            except Exception as e:
                logger.error(f"❌ Failed to parse response JSON: {e}")
                logger.error(f"Response text: {response.text}")
                raise Exception(f"L'API a répondu mais le format de réponse est invalide: {str(e)}")

    def update_glossary(self, glossary):
        import logging
        logger = logging.getLogger(__name__)

        prepared_glossary: dict = GlossaryProcessor().form_glossary_object(glossary.file)

        payload = {
            "system": settings.GLOSSARY_SYSTEM,
            "username": get_glossary_username(glossary),
            "glossary_id": glossary.glossary_id,
            "glossary": {
                "name": os.path.splitext(os.path.basename(glossary.file.name))[0],
                "description": "",
                "languages": [glossary.source_language.abbreviation.lower(),
                              glossary.target_language.abbreviation.lower()],
                "values": prepared_glossary
            }
        }

        # Log the payload (without the full values to keep logs readable)
        payload_summary = {
            "system": payload["system"],
            "username": payload["username"],
            "glossary_id": payload["glossary_id"],
            "glossary": {
                "name": payload["glossary"]["name"],
                "description": payload["glossary"]["description"],
                "languages": payload["glossary"]["languages"],
                "values_count": len(payload["glossary"]["values"]) if isinstance(payload["glossary"]["values"], (list, dict)) else "unknown"
            }
        }
        logger.info(f"🔵 API UPDATE_GLOSSARY - Request payload: {payload_summary}")

        url = preferences.MainSettings.glossaries_url + "update_glossary"
        logger.info(f"🔵 API UPDATE_GLOSSARY - URL: {url}")

        try:
            response = requests.post(
                url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=60  # 60 second timeout
            )
        except requests.exceptions.Timeout:
            error_msg = "L'API de mise à jour n'a pas répondu dans le délai imparti (timeout de 60 secondes)"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Impossible de se connecter à l'API de glossaire à l'adresse {url}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Erreur lors de la requête à l'API de glossaire: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

        logger.info(f"🔵 API UPDATE_GLOSSARY - Status code: {response.status_code}")
        logger.info(f"🔵 API UPDATE_GLOSSARY - Response: {response.text[:500]}")  # First 500 chars

        if response.status_code // 100 != 2:
            logger.error(f"❌ API UPDATE_GLOSSARY FAILED - Full response: {response.text}")
            error_msg = f"L'API de mise à jour de glossaire a retourné une erreur (HTTP {response.status_code})"
            try:
                error_data = response.json()
                if isinstance(error_data, dict) and 'error' in error_data:
                    error_msg += f": {error_data['error']}"
                elif isinstance(error_data, dict) and 'detail' in error_data:
                    error_msg += f": {error_data['detail']}"
                else:
                    error_msg += f": {str(error_data)[:200]}"
            except:
                # Not JSON, just include first 200 chars of response
                error_msg += f": {response.text[:200]}"
            raise Exception(error_msg)
        else:
            logger.info(f"✅ API UPDATE_GLOSSARY SUCCESS")

    def delete_glossary(self, glossary):
        import logging
        logger = logging.getLogger(__name__)

        payload = {
            "system": settings.GLOSSARY_SYSTEM,
            "username": get_glossary_username(glossary),
            "glossary_id": glossary.glossary_id,
        }

        logger.info(f"🔵 API DELETE_GLOSSARY - Request payload: {payload}")

        url = preferences.MainSettings.glossaries_url + 'delete_glossary'
        logger.info(f"🔵 API DELETE_GLOSSARY - URL: {url}")

        response = requests.post(
            url,
            headers=self._prepare_headers(),
            json=payload
        )

        logger.info(f"🔵 API DELETE_GLOSSARY - Status code: {response.status_code}")
        logger.info(f"🔵 API DELETE_GLOSSARY - Response: {response.text[:500]}")

        if response.status_code // 100 != 2:
            logger.error(f"❌ API DELETE_GLOSSARY FAILED - Full response: {response.text}")
            raise Exception(response.text)
        else:
            logger.info(f"✅ API DELETE_GLOSSARY SUCCESS")
