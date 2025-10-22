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
        prepared_glossary: dict = GlossaryProcessor().form_glossary_object(glossary.file)
        response = requests.post(
            settings.GLOSSARY_API_URL + "create_glossary",
            headers=self._prepare_headers(),
            json={
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
        )
        if response.status_code // 100 != 2:
            raise Exception(response.text)
        else:
            return response.json().get("glossary_id")

    def update_glossary(self, glossary):
        prepared_glossary: dict = GlossaryProcessor().form_glossary_object(glossary.file)
        response = requests.post(
            settings.GLOSSARY_API_URL + "update_glossary",
            headers=self._prepare_headers(),
            json={
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
        )

        if response.status_code // 100 != 2:
            raise Exception(response.text)

    def delete_glossary(self, glossary):
        response = requests.post(
            settings.GLOSSARY_API_URL + 'delete_glossary',
            headers=self._prepare_headers(),
            json={
                "system": settings.GLOSSARY_SYSTEM,
                "username": get_glossary_username(glossary),
                "glossary_id": glossary.glossary_id,
            }
        )

        if response.status_code // 100 != 2:
            raise Exception(response.text)
