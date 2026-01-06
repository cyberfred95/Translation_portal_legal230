"""
Services pour la mise à jour des utilisateurs.
"""
from typing import Dict, Any, Optional
from django.contrib.auth import get_user_model
from django.utils import translation

User = get_user_model()


class UserUpdateService:
    """Service pour gérer les mises à jour des utilisateurs."""
    
    # Champs simples qui peuvent être mis à jour directement
    SIMPLE_FIELDS = ['username', 'email', 'first_name', 'last_name']
    
    @staticmethod
    def validate_username(username: str, current_user) -> Optional[str]:
        """
        Valide un nom d'utilisateur.
        
        Returns:
            Message d'erreur si invalide, None sinon
        """
        if not username:
            return "Username cannot be empty."
        
        if (User.objects.filter(username=username).exists()
                and current_user.username != username):
            return "This username is already used."
        
        return None
    
    @staticmethod
    def validate_email(email: str, current_user) -> Optional[str]:
        """
        Valide un email.
        
        Returns:
            Message d'erreur si invalide, None sinon
        """
        if not email:
            return "Email cannot be empty."
        
        if (User.objects.filter(email=email).exists()
                and current_user.email != email):
            return "This email is already used."
        
        return None
    
    @staticmethod
    def validate_fields(data: Dict[str, Any], user) -> Dict[str, str]:
        """
        Valide les champs fournis dans les données.
        
        Returns:
            Dictionnaire d'erreurs (vide si aucune erreur)
        """
        errors = {}
        validators = {
            'username': UserUpdateService.validate_username,
            'email': UserUpdateService.validate_email,
        }
        
        for field, validator in validators.items():
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
    def update_retention_period(user, retention_period: int, valid_choices: list) -> Optional[str]:
        """
        Met à jour la période de rétention de l'utilisateur.
        
        Returns:
            Message d'erreur si invalide, None sinon
        """
        if retention_period not in valid_choices:
            return "Invalid retention period value."
        
        user.retention_period = retention_period
        return None

