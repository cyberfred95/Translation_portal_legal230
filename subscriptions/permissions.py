"""
Module de gestion des permissions d'abonnement.

Ce module fournit des fonctions pour vérifier les permissions des utilisateurs
basées sur leur abonnement, avec gestion d'erreurs détaillée et support i18n.
"""
from rest_framework import permissions
from .models import UserSubscription
from django.utils.timezone import now
from django.utils.translation import gettext as _, gettext_lazy
from typing import Optional, Tuple
from enum import Enum


class SubscriptionPermissionError(Enum):
    """Codes d'erreur pour les vérifications de permissions d'abonnement."""
    NO_SUBSCRIPTION = "no_subscription"
    INACTIVE_STATUS = "inactive_status"
    EXPIRED = "expired"
    NOT_STARTED = "not_started"
    NO_GROUP = "no_group"
    QUOTA_SYMBOLS_EXCEEDED = "quota_symbols_exceeded"
    QUOTA_WORDS_EXCEEDED = "quota_words_exceeded"
    QUOTA_FILES_EXCEEDED = "quota_files_exceeded"
    NO_WRITING_ACCESS = "no_writing_access"
    SUCCESS = "success"


# Constantes
_DATE_FORMAT = "%Y-%m-%d"
_ACTIVE_SUBSCRIPTION_STATES = {
    UserSubscription.UserSubscriptionChoices.INCOMPLETE,
    UserSubscription.UserSubscriptionChoices.ACTIVE,
    UserSubscription.UserSubscriptionChoices.TRIALING,
    UserSubscription.UserSubscriptionChoices.PAST_DUE,
}


def is_user_subscription_active(status: UserSubscription.UserSubscriptionChoices) -> bool:
    """
    Vérifie si un statut d'abonnement est considéré comme actif.
    
    Args:
        status: Le statut de l'abonnement à vérifier
        
    Returns:
        True si le statut est actif, False sinon
    """
    return status in _ACTIVE_SUBSCRIPTION_STATES


def _check_subscription_status(subscription: UserSubscription) -> Tuple[bool, SubscriptionPermissionError, str]:
    """
    Vérifie uniquement le statut d'une souscription.
    
    Args:
        subscription: La UserSubscription à vérifier
        
    Returns:
        Tuple[bool, SubscriptionPermissionError, str]: Résultat de la vérification
    """
    if not is_user_subscription_active(subscription.status):
        return (
            False,
            SubscriptionPermissionError.INACTIVE_STATUS,
            _("Your subscription is not active (status: {status}). Please contact your group administrator.").format(
                status=subscription.get_status_display()
            )
        )
    return (True, SubscriptionPermissionError.SUCCESS, "")


def _check_subscription_dates(subscription: UserSubscription) -> Tuple[bool, SubscriptionPermissionError, str]:
    """
    Vérifie uniquement les dates de validité d'une souscription.
    
    Args:
        subscription: La UserSubscription à vérifier
        
    Returns:
        Tuple[bool, SubscriptionPermissionError, str]: Résultat de la vérification
    """
    current_time = now()
    
    if current_time > subscription.end_date:
        return (
            False,
            SubscriptionPermissionError.EXPIRED,
            _("Your subscription has expired on {end_date}. Please renew your subscription.").format(
                end_date=subscription.end_date.strftime(_DATE_FORMAT)
            )
        )
    
    if current_time < subscription.start_date:
        return (
            False,
            SubscriptionPermissionError.NOT_STARTED,
            _("Your subscription will start on {start_date}.").format(
                start_date=subscription.start_date.strftime(_DATE_FORMAT)
            )
        )
    
    return (True, SubscriptionPermissionError.SUCCESS, "")


def validate_subscription(
    subscription: Optional[UserSubscription],
    check_dates: bool = True
) -> Tuple[bool, SubscriptionPermissionError, str]:
    """
    Valide une UserSubscription (existence, statut, dates optionnelles).
    
    Args:
        subscription: La UserSubscription à valider ou None
        check_dates: Si True, vérifie aussi les dates de validité
        
    Returns:
        Tuple[bool, SubscriptionPermissionError, str]:
        - (True, SubscriptionPermissionError.SUCCESS, message) si valide
        - (False, error_code, message_i18n) si invalide
    """
    if not subscription:
        return (
            False,
            SubscriptionPermissionError.NO_SUBSCRIPTION,
            _("You do not have an active subscription. Please contact your group administrator.")
        )
    
    is_valid, error_code, error_message = _check_subscription_status(subscription)
    if not is_valid:
        return (False, error_code, error_message)
    
    if check_dates:
        is_valid, error_code, error_message = _check_subscription_dates(subscription)
        if not is_valid:
            return (False, error_code, error_message)
    
    return (True, SubscriptionPermissionError.SUCCESS, "")


def _check_user_group(user, require_group: bool) -> Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
    """
    Vérifie si l'utilisateur appartient à un groupe.
    
    Args:
        user: L'utilisateur à vérifier
        require_group: Si False, retourne toujours True
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]: Résultat
    """
    if not require_group:
        return (True, None, None)
    
    if not hasattr(user, 'group') or not user.group:
        return (
            False,
            SubscriptionPermissionError.NO_GROUP,
            _("You must belong to a group to use this feature. Please contact your group administrator.")
        )
    
    return (True, None, None)


def _check_writing_access(subscription: UserSubscription) -> Tuple[bool, SubscriptionPermissionError, str]:
    """
    Vérifie si l'abonnement inclut l'accès aux fonctionnalités d'écriture.
    
    Args:
        subscription: La UserSubscription à vérifier
        
    Returns:
        Tuple[bool, SubscriptionPermissionError, str]: Résultat
    """
    if not subscription.access_to_writing:
        return (
            False,
            SubscriptionPermissionError.NO_WRITING_ACCESS,
            _("Your subscription does not include access to writing features. Please upgrade your subscription.")
        )
    return (True, SubscriptionPermissionError.SUCCESS, "")


def check_user_subscription_permission(
    user,
    require_group: bool = True,
    require_writing_access: bool = False,
    check_dates: bool = True
) -> Tuple[bool, SubscriptionPermissionError, str]:
    """
    Vérifie les permissions de souscription complètes d'un utilisateur.
    
    Args:
        user: L'utilisateur à vérifier
        require_group: Si True, vérifie que l'utilisateur a un groupe
        require_writing_access: Si True, vérifie que l'abonnement a accès à l'écriture
        check_dates: Si True, vérifie les dates de validité de l'abonnement
        
    Returns:
        Tuple[bool, SubscriptionPermissionError, str]:
        - (True, SubscriptionPermissionError.SUCCESS, message) si autorisé
        - (False, error_code, message_i18n) si non autorisé
    """
    is_valid, error_code, error_message = _check_user_group(user, require_group)
    if not is_valid:
        return (False, error_code, error_message)
    
    subscription = user.subscriptions.first()
    is_valid, error_code, error_message = validate_subscription(subscription, check_dates=check_dates)
    if not is_valid:
        return (False, error_code, error_message)
    
    if require_writing_access:
        is_valid, error_code, error_message = _check_writing_access(subscription)
        if not is_valid:
            return (False, error_code, error_message)
    
    return (True, SubscriptionPermissionError.SUCCESS, _("User has valid subscription permissions."))


class SubscribedPermission(permissions.BasePermission):
    """
    Permission DRF pour vérifier qu'un utilisateur a un abonnement valide.
    
    Tous les utilisateurs (y compris staff) doivent avoir :
    - Un groupe
    - Une souscription valide (statut actif, dates valides)
    - Optionnellement, l'accès à l'écriture (si requires_writing_access=True sur la vue)
    
    Note: Les utilisateurs staff ne bénéficient plus d'un passe-droit automatique
    et doivent respecter les mêmes règles d'abonnement que les autres utilisateurs.
    """
    message = gettext_lazy(
        "You are not allowed to perform this action, please contact your group administrator"
    )

    def has_permission(self, request, view):
        """Vérifie les permissions de l'utilisateur."""
        if not request.user or not request.user.is_authenticated:
            return False
        
        require_writing_access = getattr(view, 'requires_writing_access', False)
        is_allowed, error_code, error_message = check_user_subscription_permission(
            request.user,
            require_group=True,
            require_writing_access=require_writing_access,
            check_dates=True
        )
        
        if not is_allowed and error_message:
            self.message = error_message
        
        return is_allowed
