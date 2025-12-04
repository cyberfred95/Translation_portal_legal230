import json
import os

from django.conf import settings
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile
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
        return f"{settings.FILES_PROCESSING_API_URL}/api/{self.file_extension_route_mapping[file_extension]}"

    def get_texts(self, file: InMemoryUploadedFile):
        file_extension = os.path.splitext(file.name)[1]
        file_name = file.name
        file_content = file.read()
        if file_extension == '.pdf':
            converted_file_response = requests.post(
                f"{settings.FILES_PROCESSING_API_URL}/api/pdf/convert",
                headers={
                    "Content-Type": file_extension,
                    "Content-Disposition": f'attachment; '
                                           f'filename="{file_name}"',
                },
                data=file_content
            )
            file_content = converted_file_response.content
            file_extension = '.docx'

        response = requests.post(
            self.get_files_processing_api_url(file_extension) + '/export',
            headers={
                "Content-Type": file_extension,
                "Content-Disposition": f'attachment; '
                                       f'filename="{file_name}"',
            },
            data=file_content
        )
        file.seek(0)
        return response.json()

    def get_chars(self, file):
        response = self.get_texts(file)
        chars = 0
        for paragraph in response.json()['texts']:
            chars += len(paragraph['text'])
        return chars

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
