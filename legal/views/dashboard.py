from django.conf import settings
from legal.views_all import BaseTemplateView
import requests

from legal.helpers import (
    get_user_emails_map,
    process_projects,
    extract_user_tokens_from_projects
)


class DashboardView(BaseTemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page', 1)

        translated_words_count = 0
        translated_symbols_count = 0
        translated_files_count = 0
        try:
            user_subscription = user.subscriptions.first()
            if user_subscription:
                translated_words_count = user_subscription.translated_words_count
                translated_symbols_count = user_subscription.translated_symbols_count
                translated_files_count = user_subscription.translated_files_count
                # Exposer les plafonds depuis le type d'abonnement si disponible (source de vérité)
                sub_type = getattr(user_subscription, 'subscription', None)
                if sub_type:
                    context['max_symbols_count'] = getattr(sub_type, 'max_symbols_count', -1)
                    context['max_words_count'] = getattr(sub_type, 'max_words_count', -1)
                    context['max_files_count'] = getattr(sub_type, 'max_files_count', -1)
                    context['max_glossaries_count'] = getattr(sub_type, 'custom_glossaries_count', -1)
                else:
                    # fallback sur les champs copiés dans UserSubscription
                    context['max_symbols_count'] = getattr(user_subscription, 'max_symbols_count', -1)
                    context['max_words_count'] = getattr(user_subscription, 'max_words_count', -1)
                    context['max_files_count'] = getattr(user_subscription, 'max_files_count', -1)
                    context['max_glossaries_count'] = getattr(user_subscription, 'custom_glossaries_count', -1)
        except Exception:
            translated_words_count = 0
            translated_symbols_count = 0
            translated_files_count = 0
            context['max_symbols_count'] = -1
            context['max_words_count'] = -1
            context['max_files_count'] = -1
            context['max_glossaries_count'] = -1

        context['translated_words_count'] = translated_words_count
        context['translated_symbols_count'] = translated_symbols_count
        context['translated_files_count'] = translated_files_count
        context['show_user_email'] = user.is_staff

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

        # Récupération des projets depuis Django Lara
        params = {
            "page_size": 5,
            "page": 1,
        }
        if not user.is_staff:
            params["user_token"] = str(user.uuid)

        try:
            response = requests.get(
                f"{settings.LARA_API_URL}/api/lara/documents",
                params=params,
                timeout=10
            ).json()

            if 'results' in response and response['results']:
                # Récupération des emails utilisateurs si staff
                email_map = {}
                if user.is_staff:
                    user_tokens = extract_user_tokens_from_projects(response['results'])
                    email_map = get_user_emails_map(user_tokens)

                # Traitement des projets
                process_projects(response['results'], user, email_map)

                # Ajout du status_mapped pour compatibilité
                for project in response['results']:
                    project['status_mapped'] = project.get('status', '')

                context['projects'] = response
            else:
                context['projects'] = {"results": []}
        except Exception:
            context['projects'] = {"results": []}

        return context

