import os

from django.conf import settings
import requests
from preferences import preferences


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
        return f"{settings.FILES_PROCESSING_API_URL}/api/{self.file_extension_route_mapping[file_extension]}/export"

    def get_texts(self, file):
        file_extension = os.path.splitext(file.name)[1]

        response = requests.post(
            self.get_files_processing_api_url(file_extension),
            headers={
                "Content-Type": file_extension,
                "Content-Disposition": f'attachment; '
                                       f'filename="{file.name}"',
            },
            data=file.read()
        )
        return response.json()

    def get_chars(self, file):
        response = self.get_texts(file)
        chars = 0
        for paragraph in response.json()['texts']:
            chars += len(paragraph['text'])
        return chars

    def get_template_name(self, source_language, target_language, domain_name):
        response = requests.post(
            preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "get_template_by_language_pair_and_domain",
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

                     ):
        template_name = self.get_template_name(source_language, target_language, domain_name)
        response = requests.post(
            preferences.StatisticSettings.URL + "add_statistic/",
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-Key': preferences.MainSettings.api_key,
            },
            data={
                "messages": texts,
                "uuid": user_uuid,
                'custom_mt_api_key': preferences.MainSettings.api_key,
                'template_name': template_name,
                'file_name': file_name
            }
        )
        print(response.text)
        print(response.status_code)
