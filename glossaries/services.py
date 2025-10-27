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

        url = preferences.MainSettings.glossaries_url + "create_glossary"

        try:
            response = requests.post(
                url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=60  # 60 second timeout
            )
        except requests.exceptions.Timeout:
            error_msg = "The glossary API did not respond within the timeout period (60 seconds)"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Unable to connect to the glossary API at {url}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Error while requesting the glossary API: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

        if response.status_code // 100 != 2:
            logger.error(f"❌ API CREATE_GLOSSARY FAILED - Full response: {response.text}")
            error_msg = f"The glossary API returned an error (HTTP {response.status_code})"
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
                return glossary_id
            except Exception as e:
                logger.error(f"❌ Failed to parse response JSON: {e}")
                logger.error(f"Response text: {response.text}")
                raise Exception(f"The API responded but the response format is invalid: {str(e)}")

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

        url = preferences.MainSettings.glossaries_url + "update_glossary"

        try:
            response = requests.post(
                url,
                headers=self._prepare_headers(),
                json=payload,
                timeout=60  # 60 second timeout
            )
        except requests.exceptions.Timeout:
            error_msg = "The update API did not respond within the timeout period (60 seconds)"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.ConnectionError as e:
            error_msg = f"Unable to connect to the glossary API at {url}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Error while requesting the glossary API: {str(e)}"
            logger.error(f"❌ {error_msg}")
            raise Exception(error_msg)

        if response.status_code // 100 != 2:
            logger.error(f"❌ API UPDATE_GLOSSARY FAILED - Full response: {response.text}")
            error_msg = f"The glossary update API returned an error (HTTP {response.status_code})"
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

    def delete_glossary(self, glossary):
        import logging
        logger = logging.getLogger(__name__)

        payload = {
            "system": settings.GLOSSARY_SYSTEM,
            "username": get_glossary_username(glossary),
            "glossary_id": glossary.glossary_id,
        }

        url = preferences.MainSettings.glossaries_url + 'delete_glossary'

        response = requests.post(
            url,
            headers=self._prepare_headers(),
            json=payload
        )

        if response.status_code // 100 != 2:
            logger.error(f"❌ API DELETE_GLOSSARY FAILED - Full response: {response.text}")
            raise Exception(response.text)
