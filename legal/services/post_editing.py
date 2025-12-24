"""
Service de post-édition pour les fichiers.

Ce module fournit des services pour la révision experte de fichiers.
Note: Certaines fonctionnalités utilisant CloudStorage ont été désactivées.
"""
from typing import Optional
from django.utils.timezone import now
from legal.helpers import get_project_file, get_text_from_file
from quoting.models import LanguageQuote
from users.models import UserGroup


class FileExpertRevisionService:
    """
    Service pour la révision experte de fichiers.
    
    Ce service gère la génération de devis pour la révision experte.
    Note: La fonctionnalité d'envoi vers post-édition (CloudStorage) a été supprimée.
    """

    @staticmethod
    def get_quote(request, project: dict) -> Optional[dict]:
        """
        Génère un devis pour un projet de révision experte.
        
        Args:
            request: Objet request Django contenant les données utilisateur
            project: Dictionnaire contenant les informations du projet
                    (doit contenir 'source_language', 'target_language', 'source_file')
        
        Returns:
            dict: Dictionnaire contenant les informations du devis si une LanguageQuote
                  correspondante est trouvée, None sinon.
                  
            Le dictionnaire retourné contient:
            - contract_name: Nom du contrat/entreprise
            - word_price: Prix par mot
            - words_count: Nombre de mots
            - total_price: Prix total
            - created_at: Date de création
            - quote_number: Numéro de devis
        """
        language_quote = LanguageQuote.objects.filter(
            source_language__abbreviation__iexact=project.get('source_language'),
            target_language__abbreviation__iexact=project.get('target_language')
        ).first()
        
        if not language_quote:
            return None
        
        # Extraction du texte pour compter les mots
        file = get_project_file(file_url=project['source_file'])
        _, full_text, _ = get_text_from_file(file)
        words_count = len(full_text)
        
        # Détermination du groupe utilisateur
        if request.data.get('company'):
            group = UserGroup.objects.filter(name=request.data.get('company')).first()
        else:
            group = request.user.group
        
        # Génération du nom de contrat
        contract_name = request.data.get(
            'company',
            request.user.group.name if request.user.group else "Administrator"
        )
        
        # Calcul du prix
        word_price = request.data.get('price', language_quote.price)
        words_count_from_data = request.data.get('words"count', words_count)
        total_price = words_count_from_data * request.data.get('price', language_quote.price)
        
        # Génération du numéro de devis
        quote_number = (
            group.generate_quoting_number()
            if group
            else f"{now().strftime('%Y/%m')}/0"
        )
        
        return {
            'contract_name': contract_name,
            'word_price': word_price,
            'words_count': words_count_from_data,
            'total_price': total_price,
            'created_at': now(),
            'quote_number': quote_number
        }
