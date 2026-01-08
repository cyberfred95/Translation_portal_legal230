"""
Helper functions pour la gestion des abonnements et des traductions.

Ce module fournit des fonctions utilitaires pour :
- Vérifier les quotas de traduction (standards et limites techniques)
- Incrémenter les compteurs de traduction
- Gérer l'usage quotidien pour les abonnements API
- Récupérer et formater les informations d'abonnement pour l'affichage
"""
import logging
from typing import Tuple, Optional, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:
    from subscriptions.models import CountMetered

from django.conf import settings
from django.utils.timezone import now
from django.utils.translation import gettext as _

from subscriptions.models import SubscriptionType, UserSubscription
from subscriptions.permissions import (
    check_user_subscription_permission,
    SubscriptionPermissionError,
    validate_subscription
)


logger = logging.getLogger(__name__)


# Constantes pour les types de quotas
QUOTA_TYPE_FILES = 'files'
QUOTA_TYPE_WORDS = 'words'
QUOTA_TYPE_CHARACTERS = 'characters'

_QUOTA_LABELS: Dict[str, str] = {
    QUOTA_TYPE_FILES: _("file"),
    QUOTA_TYPE_WORDS: _("word"),
    QUOTA_TYPE_CHARACTERS: _("character")
}


def _check_technical_symbol_limit(
    subscription: UserSubscription,
    symbols_count: int
) -> Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
    """
    Vérifie si la limite technique de symboles est respectée.
    
    Cette vérification est ignorée si technical_maximum_symbol_removed est True.
    
    Args:
        subscription: La UserSubscription à vérifier
        symbols_count: Nombre de symboles à traduire
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
        - (True, None, None) si la limite est respectée ou ignorée
        - (False, error_code, error_message) si la limite est dépassée
    """
    # Ignorer la vérification si le flag est activé
    if subscription.technical_maximum_symbol_removed:
        return (True, None, None)
    
    # Ignorer si aucun symbole à vérifier
    if symbols_count <= 0:
        return (True, None, None)
    
    technical_limit = settings.TECHNICAL_MAXIMUM_SYMBOLS_AMOUNT
    total_symbols = subscription.translated_symbols_count + symbols_count
    
    if total_symbols > technical_limit:
        return (
            False,
            SubscriptionPermissionError.QUOTA_SYMBOLS_EXCEEDED,
            _("The technical maximum limit has been reached. "
              "Please contact support for assistance.")
        )
    
    return (True, None, None)


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
        quota_type: Type de quota pour le message d'erreur
        error_code: Code d'erreur à retourner en cas de dépassement
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]: Résultat
    """
    if limit < 0:  # Quota illimité
        return (True, None, None)
    
    if current + increment > limit:
        quota_label = _QUOTA_LABELS.get(quota_type, quota_type)
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


def _check_all_quotas(
    subscription: UserSubscription,
    words_count: int,
    symbols_count: int,
    files_count: Optional[int]
) -> Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]:
    """
    Vérifie tous les quotas de traduction pour une souscription.
    
    Effectue les vérifications dans l'ordre suivant :
    1. Limite technique pour les symboles (si applicable)
    2. Quotas standards (fichiers, mots, symboles)
    
    Args:
        subscription: La UserSubscription à vérifier
        words_count: Nombre de mots à traduire
        symbols_count: Nombre de symboles à traduire
        files_count: Nombre de fichiers à traduire (optionnel)
        
    Returns:
        Tuple[bool, Optional[SubscriptionPermissionError], Optional[str]]: Résultat
    """
    # Vérification de la limite technique pour les symboles (en premier)
    is_allowed, error_code, error_message = _check_technical_symbol_limit(
        subscription, symbols_count
    )
    if not is_allowed:
        return (False, error_code, error_message)
    
    # Vérification des quotas standards
    quota_checks: List[Tuple[Optional[int], int, int, str, SubscriptionPermissionError]] = [
        (files_count, subscription.translated_files_count, subscription.max_files_count,
         QUOTA_TYPE_FILES, SubscriptionPermissionError.QUOTA_FILES_EXCEEDED),
        (words_count, subscription.translated_words_count, subscription.max_words_count,
         QUOTA_TYPE_WORDS, SubscriptionPermissionError.QUOTA_WORDS_EXCEEDED),
        (symbols_count, subscription.translated_symbols_count, subscription.max_symbols_count,
         QUOTA_TYPE_CHARACTERS, SubscriptionPermissionError.QUOTA_SYMBOLS_EXCEEDED),
    ]
    
    for count, current, limit, quota_type, error_code in quota_checks:
        if count is None or count <= 0:
            continue
        
        is_allowed, error_code_result, error_message = _check_quota_limit(
            current=current,
            limit=limit,
            increment=count,
            quota_type=quota_type,
            error_code=error_code
        )
        
        if not is_allowed:
            return (False, error_code_result, error_message)
    
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
    is_allowed, error_code, error_message = check_user_subscription_permission(
        request.user,
        require_group=True,
        require_writing_access=False,
        check_dates=True
    )
    
    if not is_allowed:
        return (False, error_code, error_message)
    
    subscription = request.user.subscriptions.first()
    if not subscription:
        # Ne devrait pas arriver car validate_subscription a déjà vérifié
        return (
            False,
            SubscriptionPermissionError.NO_SUBSCRIPTION,
            _("Subscription not found. Please contact your group administrator.")
        )
    
    return _check_all_quotas(subscription, words_count, symbols_count, files_count)


def _increment_subscription_totals(
    subscription: UserSubscription,
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
    update_fields: List[str] = ['translated_words_count', 'translated_symbols_count']

    if files_count:
        subscription.translated_files_count += files_count
        update_fields.append('translated_files_count')

    subscription.save(update_fields=update_fields)


def _increment_daily_metered_usage(
    subscription: UserSubscription,
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
    update_fields: List[str] = ['daily_translated_words_count', 'daily_translated_symbols_count']

    if files_count:
        count_metered.daily_translated_files_count += files_count
        update_fields.append('daily_translated_files_count')

    count_metered.save(update_fields=update_fields)


def _get_active_metered_entry(subscription: UserSubscription) -> Optional['CountMetered']:
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


def _is_api_subscription(subscription: UserSubscription) -> bool:
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

    _increment_subscription_totals(subscription, words_count, symbols_count, files_count)

    if _is_api_subscription(subscription):
        _increment_daily_metered_usage(subscription, words_count, symbols_count, files_count)


# ============================================================================
# Fonctions utilitaires pour l'affichage des abonnements
# ============================================================================

# Constantes pour les statuts d'affichage
SUBSCRIPTION_STATUS_ACTIVE = 'active'
SUBSCRIPTION_STATUS_NO_SUBSCRIPTION = 'no_subscription'
SUBSCRIPTION_STATUS_ERROR = 'error'


def get_active_user_subscriptions(user) -> List[UserSubscription]:
    """
    Récupère tous les abonnements actifs d'un utilisateur.
    
    Un abonnement est considéré actif si :
    - Son statut est actif (via is_user_subscription_active)
    - La date actuelle est dans l'intervalle [start_date, end_date]
    
    Args:
        user: L'utilisateur dont on veut récupérer les abonnements
        
    Returns:
        List[UserSubscription]: Liste des abonnements actifs, triée par date de début (plus récent en premier)
    """
    from subscriptions.permissions import is_user_subscription_active
    
    current_time = now()
    all_subscriptions = UserSubscription.objects.filter(
        user=user
    ).select_related('subscription')
    
    active_subscriptions = [
        sub for sub in all_subscriptions
        if is_user_subscription_active(sub.status)
        and current_time >= sub.start_date
        and current_time <= sub.end_date
    ]
    
    # Trier par date de début (plus récent en premier) pour cohérence
    active_subscriptions.sort(key=lambda s: s.start_date, reverse=True)
    
    return active_subscriptions


def _build_subscription_error_message(subscription_names: List[str]) -> str:
    """
    Construit le message d'erreur pour plusieurs abonnements actifs.
    
    Args:
        subscription_names: Liste des noms d'abonnements
        
    Returns:
        str: Message d'erreur formaté et traduit
    """
    names = ", ".join(subscription_names)
    return _("Multiple active subscriptions found: {subscription_names}").format(
        subscription_names=names
    )


def _format_no_subscription_response() -> Dict[str, Optional[str]]:
    """Retourne la réponse formatée pour aucun abonnement."""
    return {
        'status': SUBSCRIPTION_STATUS_NO_SUBSCRIPTION,
        'name': None,
        'product_type': None,
        'error_details': _("No active subscription found.")
    }


def _format_active_subscription_response(subscription: UserSubscription) -> Dict[str, Optional[str]]:
    """Retourne la réponse formatée pour un abonnement actif."""
    return {
        'status': SUBSCRIPTION_STATUS_ACTIVE,
        'name': subscription.subscription.name,
        'product_type': subscription.subscription.product_type,
        'error_details': None
    }


def _format_multiple_subscriptions_error_response(active_subscriptions: List[UserSubscription]) -> Dict[str, Optional[str]]:
    """Retourne la réponse formatée pour plusieurs abonnements actifs (erreur)."""
    subscription_names = [sub.subscription.name for sub in active_subscriptions]
    return {
        'status': SUBSCRIPTION_STATUS_ERROR,
        'name': None,
        'product_type': None,
        'error_details': _build_subscription_error_message(subscription_names)
    }


def format_subscription_info_for_display(user) -> Dict[str, Optional[str]]:
    """
    Formate les informations d'abonnement d'un utilisateur pour l'affichage dans les templates.
    
    Args:
        user: L'utilisateur dont on veut formater les informations d'abonnement
        
    Returns:
        dict: {
            'status': 'active' | 'no_subscription' | 'error',
            'name': str | None (nom de l'abonnement),
            'product_type': str | None (type de produit),
            'error_details': str | None (détails de l'erreur si status == 'error' ou 'no_subscription')
        }
    """
    active_subscriptions = get_active_user_subscriptions(user)
    
    if not active_subscriptions:
        return _format_no_subscription_response()
    
    if len(active_subscriptions) == 1:
        return _format_active_subscription_response(active_subscriptions[0])
    
    # Plusieurs abonnements actifs - c'est une erreur
    return _format_multiple_subscriptions_error_response(active_subscriptions)
