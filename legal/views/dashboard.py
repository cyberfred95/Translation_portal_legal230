from django.conf import settings
from legal.views_all import BaseTemplateView
from datetime import datetime
from urllib.parse import urlparse, unquote
import requests

from subscriptions.utils import get_user_api_key


class DashboardView(BaseTemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page', 1)
        type_filter = self.request.GET.get('type', '')
        status_filter = self.request.GET.get('status', '')
        language_filter = self.request.GET.get('language', '')

        params = {
            "page_size": 5,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        try:
            user_api_key = get_user_api_key(user)
        except ValueError:
            context['projects'] = []
            return context
        headers = {"token": user_api_key}

        context['current_type_filter'] = type_filter
        context['current_status_filter'] = status_filter
        context['current_language_filter'] = language_filter

        translated_words_count = 0
        translated_symbols_count = 0
        translated_files_count = 0
        try:
            user_subscription = user.subscriptions.first()
            if user_subscription:
                translated_words_count = user_subscription.translated_words_count
                translated_symbols_count = user_subscription.translated_symbols_count
                translated_files_count = user_subscription.translated_files_count
        except Exception:
            translated_words_count = 0
            translated_symbols_count = 0
            translated_files_count = 0

        context['translated_words_count'] = translated_words_count
        context['translated_symbols_count'] = translated_symbols_count
        context['translated_files_count'] = translated_files_count

        glossaries_count = 0
        try:
            from glossaries.models import Glossary
            glossaries_count = Glossary.objects.filter(user=user).count()
        except Exception:
            glossaries_count = 0
        context['user_glossaries_count'] = glossaries_count

        try:
            is_group_admin = False
            user_group = getattr(user, 'group', None)
            if user.is_staff or user.is_superuser:
                is_group_admin = True
            elif user_group:
                is_group_admin = user_group.admin.filter(id=user.id).exists()
            context['is_group_admin'] = is_group_admin
        except Exception:
            context['is_group_admin'] = False

        try:
            response = requests.get(
                settings.CLOUDSTORAGE_API_URL,
                params=params,
                headers=headers
            ).json()

            if 'results' in response:
                for project in response['results']:
                    file_name = urlparse(project['source_file']).path.lstrip('/').split('/')[-1]
                    original_filename = unquote(file_name)
                    project['source_file_name'] = original_filename

                    project['created_at'] = datetime.fromisoformat(
                        project['created_at'].replace('Z', '+00:00'))

                    project['status_mapped'] = project['status']
                    project['document_type'] = 'text' if project['source_file_name'].lower().endswith('.txt') else 'document'

                context['projects'] = response
            else:
                context['projects'] = {"results": []}
        except Exception:
            context['projects'] = {"results": []}

        return context


