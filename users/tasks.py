"""
Tâches Celery pour la gestion des utilisateurs.
"""
import logging
from typing import Tuple
from celery import shared_task
from .models import UserGroup, User
from .services.document_cleanup import (
    get_all_expired_documents,
    delete_document
)

logger = logging.getLogger(__name__)


@shared_task
def reset_quote_number():
    """Réinitialise le numéro de devis mensuel pour tous les groupes."""
    user_groups = UserGroup.objects.all()
    for user_group in user_groups:
        user_group.quote_monthly_number = 0
        user_group.save()


def _delete_expired_documents_for_user(user_uuid: str, retention_days: int) -> Tuple[int, int]:
    """
    Supprime tous les documents expirés pour un utilisateur.
    
    Args:
        user_uuid: UUID de l'utilisateur
        retention_days: Nombre de jours de rétention
        
    Returns:
        Tuple (deleted_count, error_count)
    """
    expired_documents = get_all_expired_documents(user_uuid, retention_days)
    
    if not expired_documents:
        return 0, 0
    
    deleted_count = 0
    error_count = 0
    
    for document_id in expired_documents:
        success, _ = delete_document(document_id, user_uuid)
        if success:
            deleted_count += 1
        else:
            error_count += 1
    
    return deleted_count, error_count


def _process_user_documents(user) -> Tuple[int, int]:
    """
    Traite les documents expirés pour un utilisateur.
    
    Returns:
        Tuple (deleted_count, error_count)
    """
    user_uuid = str(user.uuid)
    retention_days = user.retention_period
    return _delete_expired_documents_for_user(user_uuid, retention_days)


@shared_task
def cleanup_user_expired_documents(user_id: int):
    """
    Tâche Celery pour supprimer les documents expirés d'un utilisateur spécifique.
    
    Args:
        user_id: ID de l'utilisateur
        
    Returns:
        dict: Statistiques (documents_deleted, errors)
    """
    try:
        user = User.objects.get(id=user_id, is_active=True)
    except User.DoesNotExist:
        logger.warning(f"User {user_id} not found or inactive")
        return {'documents_deleted': 0, 'errors': 0}
    
    try:
        deleted, errors = _process_user_documents(user)
        if deleted > 0:
            logger.info(
                f"User {user.id}: {deleted} documents deleted, {errors} errors"
            )
        return {'documents_deleted': deleted, 'errors': errors}
    except Exception as e:
        logger.error(
            f"Error in cleanup_user_expired_documents for user {user.id}: {e}",
            exc_info=True
        )
        return {'documents_deleted': 0, 'errors': 1}


@shared_task
def cleanup_expired_documents():
    """
    Tâche quotidienne pour supprimer les documents de traduction expirés.
    
    Pour chaque utilisateur actif :
    1. Récupère tous ses documents via l'API Lara-bridge (avec pagination)
    2. Vérifie si created_at + retention_period < aujourd'hui
    3. Si oui, supprime le document via l'endpoint DELETE
    
    Exécutée tous les jours à minuit.
    
    Returns:
        dict: Statistiques de l'exécution (users_processed, documents_deleted, errors)
    """
    active_users = User.objects.filter(is_active=True)
    stats = {
        'users_processed': 0,
        'documents_deleted': 0,
        'errors': 0
    }
    
    logger.info(f"Starting cleanup_expired_documents for {active_users.count()} active users")
    
    for user in active_users:
        try:
            deleted, errors = _process_user_documents(user)
            stats['documents_deleted'] += deleted
            stats['errors'] += errors
            stats['users_processed'] += 1
            
        except Exception as e:
            stats['errors'] += 1
            logger.error(
                f"Unexpected error processing user {user.id} ({user.uuid}): {e}",
                exc_info=True
            )
    
    logger.info(
        f"cleanup_expired_documents completed: "
        f"{stats['users_processed']} users processed, "
        f"{stats['documents_deleted']} documents deleted, "
        f"{stats['errors']} errors"
    )
    
    return stats
