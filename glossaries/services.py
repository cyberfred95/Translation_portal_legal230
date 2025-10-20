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

        response = requests.post(
            url,
            headers=self._prepare_headers(),
            json=payload
        )

        logger.info(f"🔵 API CREATE_GLOSSARY - Status code: {response.status_code}")
        logger.info(f"🔵 API CREATE_GLOSSARY - Response: {response.text[:500]}")  # First 500 chars

        if response.status_code // 100 != 2:
            logger.error(f"❌ API CREATE_GLOSSARY FAILED - Full response: {response.text}")
            raise Exception(response.text)
        else:
            glossary_id = response.json().get("glossary_id")
            logger.info(f"✅ API CREATE_GLOSSARY SUCCESS - glossary_id: {glossary_id}")
            return glossary_id

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

        response = requests.post(
            url,
            headers=self._prepare_headers(),
            json=payload
        )

        logger.info(f"🔵 API UPDATE_GLOSSARY - Status code: {response.status_code}")
        logger.info(f"🔵 API UPDATE_GLOSSARY - Response: {response.text[:500]}")  # First 500 chars

        if response.status_code // 100 != 2:
            logger.error(f"❌ API UPDATE_GLOSSARY FAILED - Full response: {response.text}")
            raise Exception(response.text)
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
