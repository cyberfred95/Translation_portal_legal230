from django.conf import settings
import requests

from legal.views_all import BaseTemplateView, PAGINATION_PAGE_SIZE
from legal.credentials import languages
from quoting.helpers import get_price_by_language_pair
from legal.helpers import (
    get_user_emails_map,
    process_projects,
    extract_user_tokens_from_projects,
    extract_language_codes_from_project
)


class ProjectsHistoryView(BaseTemplateView):
    template_name = 'project_history/project_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page')
        context['languages'] = languages

        # Paramètres pour l'API Django Lara
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "page": page if page is not None else 1,
        }
        # Si l'utilisateur n'est pas staff, filtrer par son user_uuid
        if not user.is_staff:
            params["user_uuid"] = str(user.uuid)

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
                
                # Ajout des propriétés spécifiques à project_history
                for project in response['results']:
                    source_lang, target_lang = extract_language_codes_from_project(project)
                    project['display_popup'] = not bool(get_price_by_language_pair(
                        source_language=source_lang,
                        target_language=target_lang
                    ))
                
                context['projects'] = response
            else:
                context['projects'] = {"results": []}
        except Exception:
            context['projects'] = {"results": []}
        
        context['show_user_email'] = user.is_staff
        context['lara_api_url'] = settings.LARA_API_URL
        context['user_uuid'] = str(user.uuid) if hasattr(user, 'uuid') else None

        return context

