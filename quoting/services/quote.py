import math
import os
from typing import Optional
from urllib.parse import urlencode
from preferences import preferences
from legal.helpers import get_project_file, get_text_from_file
from quoting.helpers import get_price_by_language_pair
from quoting.mail_helpers import send_quote_email
import requests
from django.urls import reverse
from django.utils.timezone import now

from quoting.models import LanguageQuote


class FormQuoteService:

    @staticmethod
    def get_expert_revision_url(project_id, context_variables: dict) -> str:
        base_url = f"{preferences.MainSettings.CLOUDSTORAGE_API_URL}post_editing/{project_id}/accept/"
        return f"{base_url}?{urlencode(context_variables)}"

    @staticmethod
    def get_working_days(words_count: int, quote_price: LanguageQuote) -> int:

        working_days_count = math.ceil(words_count / quote_price.daily_performance)
        working_days_count += quote_price.additional_time_for_order_processing
        return working_days_count

    def send_quote_to_user(self, request):
        project_id = request.data.get('project_id')

        response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={
                                    "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})

        project = response.json()
        quote_price = get_price_by_language_pair(source_language=project['source_language'],
                                                 target_language=project['target_language'])
        file = get_project_file(file_url=project['source_file'])
        words_count = len(get_text_from_file(file, api_key=None))
        file_name, extension = os.path.splitext(file.name)
        if quote_price:
            context_variables = {
                "email": preferences.MainSettings.sender_email,
                "username": request.user.username,
                "user_email": request.user.email,
                "company": request.user.group.name if request.user.group else "Administrator",
                'contract_name': request.data.get('company',
                                                  request.user.group.name if request.user.group else "Administrator"),
                "language_pair": f"{str(project['source_language']).upper()} -> {str(project['target_language']).upper()}",
                'file_name': file.name if len(str(file_name)) < 20 else f"{file_name[:20]}...-{extension}",
                'word_price': quote_price.price,
                'words_count': words_count,
                'working_days': self.get_working_days(words_count, quote_price=quote_price),
                'total_price': words_count * quote_price.price,
                'created_at': now(),
                'seller_email': preferences.MainSettings.sender_email,
                'quote_number': request.user.group.generate_quoting_number() if request.user.group else f"{now().strftime('%Y/%m')}/0"

            }
            context_variables['accept_expert_revision_file_absolute_url'] = self.get_expert_revision_url(project_id,
                                                                                                         context_variables=context_variables)

            send_quote_email(request.user.id, context_variables)
