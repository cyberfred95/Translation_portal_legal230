"""
Helper functions pour la gestion des abonnements et des traductions.

Ce module fournit des fonctions utilitaires pour :
- Vérifier les quotas de traduction
- Incrémenter les compteurs de traduction
- Gérer l'usage quotidien pour les abonnements API
"""
import logging
from typing import Tuple, Optional

from django.utils.timezone import now
from django.utils.translation import gettext as _

from subscriptions.models import SubscriptionType
from subscriptions.permissions import (
    check_user_subscription_permission,
    SubscriptionPermissionError,
    validate_subscription
)


logger = logging.getLogger(__name__)


def _check_quota_limit(
    current: int,
    limit: int,
    increment: int,
    quota_type: str,
    error_code: SubscriptionPermissionError
) -> Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
    """
    Vérifie si un quota peut être dépassé.
    
    Args:
        current: Valeur actuelle du quota
        limit: Limite du quota (-1 pour illimité)
        increment: Valeur à ajouter
        quota_type: Type de quota pour le message d'erreur ('files', 'words', 'characters')
        error_code: Code d'erreur à retourner en cas de dépassement
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]: Résultat
    """
    # Quota illimité
    if limit < 0:
        return (True, None, None)
    
    new_value = current + increment
    if new_value > limit:
        quota_labels = {
            'files': _("file"),
            'words': _("word"),
            'characters': _("character")
        }
        quota_label = quota_labels.get(quota_type, quota_type)
        
        return (
            False,
            error_code,
            _("You have exceeded your {quota_type} translation quota. "
              "You have used {used}/{max} {quota_label}. "
              "Please upgrade your subscription or contact your group administrator.").format(
                quota_type=quota_type,
                used=current,
                max=limit,
                quota_label=quota_label
            )
        )
    
    return (True, None, None)


def translation_allowed(
    request,
    symbols_count: int,
    words_count: int,
    files_count: Optional[int] = None
) -> Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
    """
    Vérifie si une traduction est autorisée pour l'utilisateur.
    
    Effectue les vérifications suivantes dans l'ordre :
    1. Permissions de base de l'abonnement (groupe, statut, dates)
    2. Quotas de traduction (symboles, mots, fichiers)
    
    Args:
        request: La requête HTTP contenant l'utilisateur
        symbols_count: Nombre de symboles à traduire
        words_count: Nombre de mots à traduire
        files_count: Nombre de fichiers à traduire (optionnel)
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
        - (True, None, None) si autorisé
        - (False, error_code, error_message) si non autorisé
    """
    # Vérification des permissions de base de l'abonnement
    is_allowed, error_code, error_message = check_user_subscription_permission(
        request.user,
        require_group=True,
        require_writing_access=False,
        check_dates=True
    )
    
    if not is_allowed:
        return (False, error_code, error_message)
    
    # Les staffs ont toujours accès, pas de vérification de quota
    if request.user.is_staff:
        return (True, None, None)
    
    # Récupération de l'abonnement (déjà validé par check_user_subscription_permission)
    subscription = request.user.subscriptions.first()
    
    # Vérification des quotas
    # Fichiers
    if files_count is not None and files_count > 0:
        is_allowed, error_code, error_message = _check_quota_limit(
            current=subscription.translated_files_count,
            limit=subscription.max_files_count,
            increment=files_count,
            quota_type='files',
            error_code=SubscriptionPermissionError.QUOTA_FILES_EXCEEDED
        )
        if not is_allowed:
            return (False, error_code, error_message)
    
    # Mots
    is_allowed, error_code, error_message = _check_quota_limit(
        current=subscription.translated_words_count,
        limit=subscription.max_words_count,
        increment=words_count,
        quota_type='words',
        error_code=SubscriptionPermissionError.QUOTA_WORDS_EXCEEDED
    )
    if not is_allowed:
        return (False, error_code, error_message)
    
    # Symboles
    is_allowed, error_code, error_message = _check_quota_limit(
        current=subscription.translated_symbols_count,
        limit=subscription.max_symbols_count,
        increment=symbols_count,
        quota_type='characters',
        error_code=SubscriptionPermissionError.QUOTA_SYMBOLS_EXCEEDED
    )
    if not is_allowed:
        return (False, error_code, error_message)
    
    return (True, None, None)


def _increment_subscription_totals(
    subscription: 'UserSubscription',
    words_count: int,
    symbols_count: int,
    files_count: Optional[int]
) -> None:
    """
    Incrémente les compteurs totaux de la souscription.
    
    Args:
        subscription: La UserSubscription à mettre à jour
        words_count: Nombre de mots à ajouter
        symbols_count: Nombre de symboles à ajouter
        files_count: Nombre de fichiers à ajouter (optionnel)
    """
    subscription.translated_words_count += words_count
    subscription.translated_symbols_count += symbols_count
    update_fields = ['translated_words_count', 'translated_symbols_count']

    if files_count:
        subscription.translated_files_count += files_count
        update_fields.append('translated_files_count')

    subscription.save(update_fields=update_fields)


def _increment_daily_metered_usage(
    subscription: 'UserSubscription',
    words_count: int,
    symbols_count: int,
    files_count: Optional[int]
) -> None:
    """
    Incrémente les compteurs quotidiens du CountMetered actif pour les abonnements API.
    
    Args:
        subscription: La UserSubscription concernée
        words_count: Nombre de mots à ajouter
        symbols_count: Nombre de symboles à ajouter
        files_count: Nombre de fichiers à ajouter (optionnel)
    """
    count_metered = _get_active_metered_entry(subscription)
    if not count_metered:
        return

    count_metered.daily_translated_words_count += words_count
    count_metered.daily_translated_symbols_count += symbols_count
    update_fields = ['daily_translated_words_count', 'daily_translated_symbols_count']

    if files_count:
        count_metered.daily_translated_files_count += files_count
        update_fields.append('daily_translated_files_count')

    count_metered.save(update_fields=update_fields)


def _get_active_metered_entry(subscription: 'UserSubscription') -> Optional['CountMetered']:
    """
    Récupère le CountMetered actif (non reporté) pour aujourd'hui.
    
    Args:
        subscription: La UserSubscription concernée
        
    Returns:
        Le CountMetered actif ou None s'il n'existe pas ou est déjà reporté
    """
    try:
        count_metered = subscription.get_today_count_metered()
    except ValueError as error:
        logger.error(
            "Multiple CountMetered entries detected for subscription %s: %s",
            subscription.id,
            error,
        )
        return None

    if count_metered is None:
        logger.error(
            "No CountMetered entry found for subscription %s on %s.",
            subscription.id,
            now().date(),
        )
        return None

    if count_metered.reported:
        logger.error(
            "Attempt to update already reported CountMetered for subscription %s on %s.",
            subscription.id,
            count_metered.date,
        )
        return None

    return count_metered


def _is_api_subscription(subscription: 'UserSubscription') -> bool:
    """
    Vérifie si la souscription est de type API.
    
    Args:
        subscription: La UserSubscription à vérifier
        
    Returns:
        True si c'est une souscription API, False sinon
    """
    return (
        subscription.subscription is not None
        and subscription.subscription.product_type == SubscriptionType.ProductChoices.API
    )


def add_translations(
    request,
    words_count: int,
    symbols_count: int,
    files_count: Optional[int] = None
) -> None:
    """
    Ajoute les compteurs de traduction à l'abonnement de l'utilisateur.
    
    Pour les abonnements API, incrémente aussi les compteurs quotidiens.
    
    Args:
        request: La requête HTTP contenant l'utilisateur
        words_count: Nombre de mots traduits
        symbols_count: Nombre de symboles traduits
        files_count: Nombre de fichiers traduits (optionnel)
    """
    if not request.user.group:
        return

    subscription = request.user.subscriptions.first()
    if not subscription:
        return

    # Validation rapide de l'abonnement avant incrémentation
    is_valid, _, _ = validate_subscription(subscription, check_dates=False)
    if not is_valid:
        logger.warning(
            "Attempt to add translations for invalid subscription %s (user: %s)",
            subscription.id,
            request.user.id
        )
        return

    # Incrémentation des totaux
    _increment_subscription_totals(
        subscription,
        words_count,
        symbols_count,
        files_count,
    )

    # Incrémentation quotidienne pour les abonnements API
    if _is_api_subscription(subscription):
        _increment_daily_metered_usage(
            subscription,
            words_count,
            symbols_count,
            files_count,
        )
