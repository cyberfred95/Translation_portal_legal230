"""
Service de génération de clés API locales.

Ce module fournit des fonctionnalités pour générer des clés API de manière locale,
sans dépendre d'un service externe. Il garantit l'unicité des clés générées.
"""

import secrets
import string
from typing import Optional, TYPE_CHECKING

# Éviter la dépendance circulaire en utilisant TYPE_CHECKING
if TYPE_CHECKING:
    from subscriptions.models import UserSubscription


class APIKeyGenerator:
    """
    Générateur de clés API avec vérification d'unicité.
    
    Cette classe encapsule la logique de génération de clés API et garantit
    qu'aucune clé dupliquée n'est créée dans la base de données.
    """
    
    # Format UUID : 8-4-4-4-12 caractères hexadécimaux avec tirets
    # Exemple : 522b1b18-4c91-4186-81e8-c9c74f2a7bee (36 caractères au total)
    UUID_FORMAT = "{}-{}-{}-{}-{}"
    UUID_SEGMENTS = [8, 4, 4, 4, 12]  # Longueurs des segments
    
    # Caractères hexadécimaux (0-9, a-f)
    HEXADECIMAL_CHARACTERS = string.hexdigits.lower()
    
    # Nombre maximum de tentatives pour générer une clé unique
    MAX_GENERATION_ATTEMPTS = 100
    
    @classmethod
    def _generate_hex_segment(cls, length: int) -> str:
        """
        Génère un segment hexadécimal de longueur donnée.
        
        Args:
            length: Longueur du segment à générer.
            
        Returns:
            str: Segment hexadécimal généré.
        """
        return ''.join(secrets.choice(cls.HEXADECIMAL_CHARACTERS) for _ in range(length))
    
    @classmethod
    def generate_key(cls) -> str:
        """
        Génère une clé API au format UUID (avec tirets).
        
        Format : 8-4-4-4-12 caractères hexadécimaux
        Exemple : 522b1b18-4c91-4186-81e8-c9c74f2a7bee
        
        Returns:
            str: Clé API générée au format UUID (36 caractères).
        """
        segments = [cls._generate_hex_segment(length) for length in cls.UUID_SEGMENTS]
        return cls.UUID_FORMAT.format(*segments)
    
    @classmethod
    def is_key_unique(cls, api_key: str, exclude_subscription_id: Optional[int] = None) -> bool:
        """
        Vérifie si une clé API est unique dans la base de données.
        
        Args:
            api_key: La clé API à vérifier.
            exclude_subscription_id: ID d'une subscription à exclure de la vérification
                                    (utile lors de la mise à jour d'une subscription existante).
            
        Returns:
            bool: True si la clé est unique, False sinon.
        """
        if not api_key:
            return False
        
        # Import différé pour éviter la dépendance circulaire
        from subscriptions.models import UserSubscription
        
        query = UserSubscription.objects.filter(api_key=api_key)
        if exclude_subscription_id is not None:
            query = query.exclude(id=exclude_subscription_id)
        
        return not query.exists()
    
    @classmethod
    def generate_unique_key(
        cls, 
        exclude_subscription_id: Optional[int] = None
    ) -> str:
        """
        Génère une clé API unique au format UUID en vérifiant qu'elle n'existe pas déjà.
        
        Cette méthode génère une clé et vérifie son unicité. Si la clé existe déjà,
        elle en génère une nouvelle jusqu'à trouver une clé unique ou atteindre
        le nombre maximum de tentatives.
        
        Args:
            exclude_subscription_id: ID d'une subscription à exclure de la vérification.
            
        Returns:
            str: Clé API unique générée au format UUID.
            
        Raises:
            RuntimeError: Si aucune clé unique n'a pu être générée après MAX_GENERATION_ATTEMPTS tentatives.
        """
        for _ in range(cls.MAX_GENERATION_ATTEMPTS):
            key = cls.generate_key()
            if cls.is_key_unique(key, exclude_subscription_id):
                return key
        
        raise RuntimeError(
            f"Impossible de générer une clé API unique après {cls.MAX_GENERATION_ATTEMPTS} tentatives. "
            f"Veuillez vérifier la base de données."
        )


class APIKeyService:
    """
    Service de gestion des clés API pour les UserSubscription.
    
    Cette classe fournit une interface de haut niveau pour la génération et
    la gestion des clés API, en utilisant APIKeyGenerator pour la génération.
    """
    
    @staticmethod
    def create_api_key_for_subscription(subscription: 'UserSubscription') -> str:
        """
        Crée une clé API unique au format UUID pour une UserSubscription.
        
        Cette méthode génère une clé API unique au format UUID et vérifie qu'elle
        n'existe pas déjà dans la base de données avant de la retourner.
        
        Args:
            subscription: L'instance UserSubscription pour laquelle générer la clé.
            
        Returns:
            str: Clé API unique générée au format UUID.
            
        Raises:
            RuntimeError: Si aucune clé unique n'a pu être générée.
        """
        exclude_id = subscription.id if subscription.pk else None
        return APIKeyGenerator.generate_unique_key(exclude_subscription_id=exclude_id)
