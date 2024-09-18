import os

from django.conf import settings
import requests
from preferences import preferences


class StatsProcessor:
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

    @staticmethod
    def send_request(texts: list, request):
        print(f'api_key {preferences.MainSettings.api_key}')
        response = requests.post(
            preferences.StatisticSettings.URL + "add_statistic/",
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-Key': preferences.MainSettings.api_key,
            },
            data={
                "texts": texts,
                "uuid": request.user.uuid,
                'custom_mt_api_key': preferences.MainSettings.api_key,
            }
        )
        print(response.status_code)
