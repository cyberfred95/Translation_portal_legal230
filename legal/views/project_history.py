from django.conf import settings
import requests

from legal.views_all import BaseTemplateView, PAGINATION_PAGE_SIZE
from legal.credentials import languages
from subscriptions.utils import get_user_api_key
from quoting.helpers import get_price_by_language_pair
from legal.helpers import (
    get_user_emails_map,
    process_projects,
    extract_user_tokens_from_projects
)


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
            context['projects'] = {"results": []}
            context['show_user_email'] = user.is_staff
            return context
        headers = {
            "token": user_api_key
        }

        if page is not None:
            params["page"] = int(page)

        try:
            response = requests.get(
                settings.CLOUDSTORAGE_API_URL, 
                params=params, 
                headers=headers
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
                    project['display_popup'] = not bool(get_price_by_language_pair(
                        source_language=project['source_language'],
                        target_language=project['target_language']
                    ))
                
                context['projects'] = response
            else:
                context['projects'] = {"results": []}
        except Exception:
            context['projects'] = {"results": []}
        
        context['show_user_email'] = user.is_staff

        return context

