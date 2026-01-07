from django.conf import settings
from legal.views_all import BaseTemplateView
import requests

from legal.helpers import (
    get_user_emails_map,
    process_projects,
    extract_user_tokens_from_projects
)


class DashboardView(BaseTemplateView):
    """
    Vue pour afficher le tableau de bord utilisateur.
    
    Affiche les statistiques de traduction, les glossaires et les projets récents.
    """
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        """Construit le contexte pour le template du dashboard."""
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Statistiques d'abonnement et quotas
        self._add_subscription_stats(context, user)
        
        # Compteur de glossaires
        context['user_glossaries_count'] = self._get_user_glossaries_count(user)
        
        # Permissions d'administration de groupe
        context['is_group_admin'] = self._is_user_group_admin(user)
        context['show_user_email'] = user.is_staff

        # Projets récents depuis l'API LARA
        context['projects'] = self._get_recent_projects(user)

        return context

    def _add_subscription_stats(self, context, user):
        """
        Ajoute les statistiques d'abonnement au contexte.
        
        Args:
            context: Dictionnaire de contexte Django
            user: Utilisateur Django
        """
        default_values = {
            'translated_words_count': 0,
            'translated_symbols_count': 0,
            'translated_files_count': 0,
            'max_symbols_count': -1,
            'max_words_count': -1,
            'max_files_count': -1,
            'max_glossaries_count': -1,
        }
        context.update(default_values)

        try:
            user_subscription = user.subscriptions.select_related('subscription').first()
            if user_subscription:
                # Compteurs de traduction consommés
                context['translated_words_count'] = user_subscription.translated_words_count
                context['translated_symbols_count'] = user_subscription.translated_symbols_count
                context['translated_files_count'] = user_subscription.translated_files_count
                
                # Limites maximales de l'abonnement
                context['max_symbols_count'] = user_subscription.max_symbols_count
                context['max_words_count'] = user_subscription.max_words_count
                context['max_files_count'] = user_subscription.max_files_count
                context['max_glossaries_count'] = user_subscription.custom_glossaries_count
        except Exception:
            pass  # Valeurs par défaut déjà définies

    def _get_user_glossaries_count(self, user):
        """
        Récupère le nombre de glossaires de l'utilisateur.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            int: Nombre de glossaires
        """
        try:
            from glossaries.models import Glossary
            return Glossary.objects.filter(user=user).count()
        except Exception:
            return 0

    def _is_user_group_admin(self, user):
        """
        Vérifie si l'utilisateur est administrateur de son groupe.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            bool: True si l'utilisateur est admin de groupe ou staff
        """
        try:
            if user.is_staff or user.is_superuser:
                return True
            
            user_group = getattr(user, 'group', None)
            if user_group:
                return user_group.admin.filter(id=user.id).exists()
            
            return False
        except Exception:
            return False

    def _get_recent_projects(self, user):
        """
        Récupère les projets récents depuis l'API LARA.
        
        Args:
            user: Utilisateur Django
            
        Returns:
            dict: Dictionnaire avec 'results' contenant la liste des projets
        """
        params = {
            "page_size": 5,
            "page": 1,
        }
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

                # Ajout du status_mapped pour compatibilité
                for project in response['results']:
                    project['status_mapped'] = project.get('status', '')

                return response
            else:
                return {"results": []}
        except Exception:
            return {"results": []}

