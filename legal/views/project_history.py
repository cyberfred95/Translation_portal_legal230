from django.conf import settings
from django.contrib.auth import get_user_model
from datetime import datetime
from urllib.parse import urlparse, unquote
import requests
import django

from legal.views_all import BaseTemplateView, PAGINATION_PAGE_SIZE
from legal.credentials import languages
from subscriptions.utils import get_user_api_key
from quoting.helpers import get_price_by_language_pair


class ProjectsHistoryView(BaseTemplateView):
    template_name = 'project_history/project_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page')
        context['languages'] = languages
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        try:
            user_api_key = get_user_api_key(user)
        except ValueError:
            # En cas d'absence de subscription, on ne peut pas afficher les projets
            context['projects'] = []
            return context
        headers = {
            "token": user_api_key
        }

        if page is not None:
            params["page"] = int(page)

        response = requests.get(
            settings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        if 'results' in response:
            for project in response['results']:
                file_name = urlparse(project['source_file']).path.lstrip(
                    '/').split('/')[-1]
                original_filename = unquote(file_name)
                project['source_file_name'] = original_filename
                project['created_at'] = datetime.fromisoformat(
                    project['created_at'].replace('Z', '+00:00'))
                project['display_popup'] = False if get_price_by_language_pair(
                    source_language=project['source_language'],
                    target_language=project['target_language']
                ) else True
                if user.is_staff:
                    try:
                        UserModel = get_user_model()
                        project['username'] = UserModel.objects.get(
                            uuid=project['user_custom_mt_token'])
                    except Exception:
                        project['username'] = None
            context['projects'] = response

        return context

