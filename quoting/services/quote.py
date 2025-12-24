"""
Service de gestion des devis.

Ce module fournit des services pour la génération et l'envoi de devis.
Note: Certaines fonctionnalités utilisant CloudStorage ont été temporairement désactivées
      et sont conservées en commentaire pour une future refonte.
"""
import math
from typing import Optional
from django.utils.timezone import now

from quoting.models import LanguageQuote
# Imports désactivés - utilisés uniquement dans le code commenté (CloudStorage)
# import os
# from urllib.parse import urlencode
# from django.conf import settings
# from quoting.helpers import get_price_by_language_pair
# from quoting.mail_helpers import send_quote_email
# from subscriptions.utils import get_user_api_key
# import requests


class FormQuoteService:

    @staticmethod
    def get_working_days(words_count: int, quote_price: LanguageQuote) -> int:
        """
        Calcule le nombre de jours ouvrables nécessaires pour un devis.
        
        Args:
            words_count: Nombre de mots à traduire
            quote_price: Objet LanguageQuote contenant les informations de tarification
            
        Returns:
            int: Nombre de jours ouvrables nécessaires
        """
        working_days_count = math.ceil(words_count / quote_price.daily_performance)
        working_days_count += quote_price.additional_time_for_order_processing
        return working_days_count

    # ============================================================================
    # CODE COMMENTÉ - SERA UTILE POUR UNE FUTURE REFONTE
    # ============================================================================
    # Les fonctions suivantes utilisaient le service CloudStorage qui n'est plus disponible.
    # Le code est conservé en commentaire pour référence future.
    # ============================================================================
    
    # @staticmethod
    # def get_expert_revision_url(project_id, context_variables: dict) -> str:
    #     """
    #     Génère l'URL d'acceptation de révision experte.
    #     
    #     Args:
    #         project_id: ID du projet
    #         context_variables: Variables de contexte pour l'URL
    #         
    #     Returns:
    #         str: URL complète avec paramètres
    #     """
    #     base_url = f"{settings.CLOUDSTORAGE_API_URL}post_editing/{project_id}/accept/"
    #     return f"{base_url}?{urlencode(context_variables)}"
    
    # def send_quote_to_user(self, request):
    #     """
    #     Envoie un devis par email à l'utilisateur.
    #     
    #     Cette fonction récupère les informations du projet depuis CloudStorage,
    #     calcule le devis et envoie un email avec les détails.
    #     
    #     Args:
    #         request: Objet request Django contenant les données du formulaire
    #     """
    #     data = getattr(request, 'data', getattr(request, 'POST', {}))
    #     project_id = data.get('project_id')
    #
    #     # Résolution de la clé API depuis la subscription utilisateur
    #     try:
    #         user_api_key = get_user_api_key(request.user)
    #     except ValueError:
    #         print("no subscription")
    #         return  # Sortie anticipée si aucune subscription trouvée
    #
    #     # Récupération du projet depuis CloudStorage
    #     response = requests.get(
    #         settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
    #         headers={"token": user_api_key}
    #     )
    #     project = response.json()
    #
    #     # Calcul du prix selon la paire de langues
    #     quote_price = get_price_by_language_pair(
    #         source_language=project.get('source_language'),
    #         target_language=project.get('target_language')
    #     )
    #
    #     # Pour éviter des appels externes lourds, ne pas télécharger le fichier ici
    #     words_count = 0
    #     file_url = project.get('source_file') or ''
    #     file_basename = os.path.basename(file_url) if file_url else ''
    #     file_name, extension = os.path.splitext(file_basename)
    #
    #     if quote_price:
    #         context_variables = {
    #             "email": settings.SENDER_EMAIL,
    #             "username": request.user.username,
    #             "user_email": request.user.email,
    #             "company": request.user.group.name if request.user.group else "Administrator",
    #             'contract_name': request.data.get(
    #                 'company',
    #                 request.user.group.name if request.user.group else "Administrator"
    #             ),
    #             "language_pair": (
    #                 f"{str(project['source_language']).upper()} -> "
    #                 f"{str(project['target_language']).upper()}"
    #             ),
    #             'file_name': (
    #                 file.name if len(str(file_name)) < 20
    #                 else f"{file_name[:20]}...-{extension}"
    #             ),
    #             'word_price': quote_price.price,
    #             'words_count': words_count,
    #             'working_days': self.get_working_days(words_count, quote_price=quote_price),
    #             'total_price': words_count * quote_price.price,
    #             'created_at': now(),
    #             'seller_email': settings.SENDER_EMAIL,
    #             'quote_number': (
    #                 request.user.group.generate_quoting_number()
    #                 if request.user.group
    #                 else f"{now().strftime('%Y/%m')}/0"
    #             )
    #         }
    #         context_variables['accept_expert_revision_file_absolute_url'] = (
    #             self.get_expert_revision_url(project_id, context_variables=context_variables)
    #         )
    #
    #         send_quote_email(request.user.id, request, context_variables)
