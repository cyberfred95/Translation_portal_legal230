"""
Services pour la mise à jour des utilisateurs.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from django.contrib.auth import get_user_model
from django.utils import translation

logger = logging.getLogger(__name__)
User = get_user_model()


class UserUpdateService:
    """Service pour gérer les mises à jour des utilisateurs."""
    
    # Champs simples qui peuvent être mis à jour directement
    SIMPLE_FIELDS = ['username', 'email', 'first_name', 'last_name']
    
    @staticmethod
    def _validate_unique_field(field_name: str, value: str, current_user, empty_message: str, used_message: str) -> Optional[str]:
        """
        Valide un champ unique (username, email, etc.).
        
        Args:
            field_name: Nom du champ à valider
            value: Valeur à valider
            current_user: Utilisateur actuel
            empty_message: Message d'erreur si vide
            used_message: Message d'erreur si déjà utilisé
            
        Returns:
            Message d'erreur si invalide, None sinon
        """
        if not value:
            return empty_message
        
        current_value = getattr(current_user, field_name, None)
        if (User.objects.filter(**{field_name: value}).exists()
                and current_value != value):
            return used_message
        
        return None
    
    @staticmethod
    def validate_username(username: str, current_user) -> Optional[str]:
        """Valide un nom d'utilisateur."""
        return UserUpdateService._validate_unique_field(
            'username', username, current_user,
            "Username cannot be empty.",
            "This username is already used."
        )
    
    @staticmethod
    def validate_email(email: str, current_user) -> Optional[str]:
        """Valide un email."""
        return UserUpdateService._validate_unique_field(
            'email', email, current_user,
            "Email cannot be empty.",
            "This email is already used."
        )
    
    @staticmethod
    def validate_fields(data: Dict[str, Any], user) -> Dict[str, str]:
        """
        Valide les champs fournis dans les données.
        
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        field_validators = {
            'username': UserUpdateService.validate_username,
            'email': UserUpdateService.validate_email,
        }
        
        for field, validator in field_validators.items():
            if field in data:
                error = validator(data[field], user)
                if error:
                    errors[field] = error
        
        return errors
    
    @staticmethod
    def update_simple_fields(user, data: Dict[str, Any]) -> None:
        """Met à jour les champs simples de l'utilisateur."""
        for field in UserUpdateService.SIMPLE_FIELDS:
            if field in data:
                setattr(user, field, data[field])
    
    @staticmethod
    def update_language(user, language: str, request) -> None:
        """Met à jour la langue de l'utilisateur et de la session."""
        user.language = language
        translation.activate(language)
        request.session[translation.LANGUAGE_SESSION_KEY] = language
    
    @staticmethod
    def update_retention_period(user, retention_period: int, valid_choices: list) -> Tuple[Optional[str], bool]:
        """
        Met à jour la période de rétention de l'utilisateur.
        
        Returns:
            Tuple (error_message, period_reduced):
            - error_message: Message d'erreur si invalide, None sinon
            - period_reduced: True si la période a été réduite, False sinon
        """
        if retention_period not in valid_choices:
            return "Invalid retention period value.", False
        
        old_period = user.retention_period
        period_reduced = retention_period < old_period
        user.retention_period = retention_period
        return None, period_reduced
    
    @staticmethod
    def update_user(user, data: Dict[str, Any], request) -> Tuple[Optional[str], bool]:
        """
        Met à jour tous les champs de l'utilisateur fournis dans data.
        
        Returns:
            Tuple (error_message, period_reduced):
            - error_message: Message d'erreur si invalide, None sinon
            - period_reduced: True si la période de rétention a été réduite
        """
        period_reduced = False
        
        # Mettre à jour les champs simples
        UserUpdateService.update_simple_fields(user, data)
        
        # Mettre à jour la langue si fournie
        if 'language' in data:
            UserUpdateService.update_language(user, data['language'], request)
        
        # Mettre à jour la période de rétention si fournie
        if 'retention_period' in data:
            # Convertir en entier si nécessaire (peut venir comme string depuis JSON)
            retention_period = data['retention_period']
            try:
                retention_period = int(retention_period)
            except (ValueError, TypeError):
                return f"Invalid retention period value: {retention_period}", False
            
            valid_choices = User.get_valid_retention_periods()
            error, period_reduced = UserUpdateService.update_retention_period(
                user, retention_period, valid_choices
            )
            if error:
                return error, False
        
        return None, period_reduced
    
    @staticmethod
    def trigger_cleanup_if_needed(user, period_reduced: bool) -> None:
        """
        Déclenche le nettoyage des documents si la période de rétention a été réduite.
        
        Si Celery n'est pas disponible, l'erreur est loggée mais n'interrompt pas
        la mise à jour de l'utilisateur.
        
        Args:
            user: Utilisateur mis à jour
            period_reduced: True si la période a été réduite
        """
        if not period_reduced:
            return
        
        try:
            from ..tasks import cleanup_user_expired_documents
            cleanup_user_expired_documents.apply_async(args=[user.id])
        except Exception as e:
            logger.error(
                f"Failed to trigger cleanup task for user {user.id} after retention period reduction: {e}. "
                f"Cleanup will be performed by the scheduled daily task.",
                exc_info=True
            )

