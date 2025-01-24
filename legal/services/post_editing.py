from typing import Optional
from preferences import preferences
from django.utils.timezone import now
import requests
from legal.helpers import get_project_file, get_text_from_file
from quoting.models import LanguageQuote
from users.models import UserGroup


class FileExpertRevisionService:

    @staticmethod
    def get_quote(request, project: dict) -> Optional[dict]:
        language_quote = LanguageQuote.objects.filter(
            source_language__abbreviation__iexact=project.get('source_language'),
            target_language__abbreviation__iexact=project.get('target_language')).first()
        if language_quote:
            api_key = None
            file = get_project_file(file_url=project['source_file'])
            words_count = len(get_text_from_file(file, api_key=api_key))
            if request.data.get('company'):
                group = UserGroup.objects.filter(name=request.data.get('company')).first()
            else:
                group = request.user.group
            return {
                'contract_name': request.data.get('company',
                                                  request.user.group.name if request.user.group else "Administrator"),
                'word_price': request.data.get('price', language_quote.price),
                'words_count': request.data.get('words"count', words_count),
                'total_price': request.data.get('words"count', words_count) * request.data.get('price',
                                                                                               language_quote.price),
                'created_at': now(),
                'quote_number': group.generate_quoting_number() if group else f"{now().strftime('%Y/%m')}/0"
            }
        return

    def send_to_post_editing(self, request, project_id):
        project = requests.get(
            preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
            headers={
                "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
            }

        ).json()
        response = requests.post(
            preferences.MainSettings.CLOUDSTORAGE_API_URL + f"post_editing/{project_id}/",
            headers={
                "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key},
            data={
                "email": preferences.MainSettings.sender_email,
                "username": request.user.username,
                "user_email": request.user.email,
                "company": request.user.group.name if request.user.group else "Administrator",
                **self.get_quote(request, project)
            })
