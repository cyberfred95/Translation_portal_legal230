import math
import os
from typing import Optional
from urllib.parse import urlencode, urlparse
from django.conf import settings
from preferences import preferences
from legal.helpers import get_project_file, get_text_from_file
from quoting.helpers import get_price_by_language_pair
from quoting.mail_helpers import send_quote_email
import requests
from django.urls import reverse
from django.utils.timezone import now

from quoting.models import LanguageQuote
from subscriptions.utils import get_user_api_key


class FormQuoteService:

    @staticmethod
    def get_expert_revision_url(project_id, context_variables: dict) -> str:
        base_url = f"{settings.CLOUDSTORAGE_API_URL}post_editing/{project_id}/accept/"
        return f"{base_url}?{urlencode(context_variables)}"

    @staticmethod
    def get_working_days(words_count: int, quote_price: LanguageQuote) -> int:

        working_days_count = math.ceil(words_count / quote_price.daily_performance)
        working_days_count += quote_price.additional_time_for_order_processing
        return working_days_count

    def send_quote_to_user(self, request):
        data = getattr(request, 'data', getattr(request, 'POST', {}))
        project_id = data.get('project_id')

        # Resolve API key based on user subscription
        try:
            user_api_key = get_user_api_key(request.user)
        except ValueError:
            print("no subscription")
            return  # Exit early if no subscription found

        response = requests.get(settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={"token": user_api_key})

        project = response.json()
        quote_price = get_price_by_language_pair(source_language=project.get('source_language'),
                                                 target_language=project.get('target_language'))
        # Pour éviter des appels externes lourds, ne pas télécharger le fichier ici
        words_count = 0
        file_url = project.get('source_file') or ''
        # Nettoyer l'URL en retirant la query string avant d'extraire le nom de fichier
        if file_url:
            parsed_url = urlparse(file_url)
            file_basename = os.path.basename(parsed_url.path)
        else:
            file_basename = ''
        file_name, extension = os.path.splitext(file_basename)
        if quote_price:
            context_variables = {
                "email": settings.SENDER_EMAIL,
                "username": request.user.username,
                "user_email": request.user.email,
                "company": request.user.group.name if request.user.group else "Administrator",
                'contract_name': request.data.get('company',
                                                  request.user.group.name if request.user.group else "Administrator"),
                "language_pair": f"{str(project['source_language']).upper()} -> {str(project['target_language']).upper()}",
                'file_name': file_name if len(str(file_name)) < 20 else f"{file_name[:20]}...{extension}",
                'word_price': quote_price.price,
                'words_count': words_count,
                'working_days': self.get_working_days(words_count, quote_price=quote_price),
                'total_price': words_count * quote_price.price,
                'created_at': now(),
                'seller_email': settings.SENDER_EMAIL,
                'quote_number': request.user.group.generate_quoting_number() if request.user.group else f"{now().strftime('%Y/%m')}/0"

            }
            context_variables['accept_expert_revision_file_absolute_url'] = self.get_expert_revision_url(project_id,
                                                                                                         context_variables=context_variables)

            send_quote_email(request.user.id, request, context_variables)
