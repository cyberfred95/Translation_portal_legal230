import os

from django.conf import settings
import requests
from .models import UserStats


class StatsCalculator:
    file_extension_route_mapping = {
        '.docx': 'word',
        '.pptx': 'powerpoint',
        '.txt': 'text',
        '.pdf': 'word',
        '.xlsx': 'excel',
    }

    def get_files_processing_api_url(self, file_extension):
        return f"{settings.FILES_PROCESSING_API_URL}/api/{self.file_extension_route_mapping[file_extension]}/export"

    def get_chars(self, file):
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
        chars = 0
        for paragraph in response.json()['texts']:
            chars += len(paragraph['text'])
        return chars

    def calculate_statistics(self, files, user):
        for file in files:
            chars = self.get_chars(file)
            print(chars)
            stats = UserStats.objects.create(user=user, chars=chars)
