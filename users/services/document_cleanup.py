"""
Services pour le nettoyage automatique des documents expirés.

Ce module contient les fonctions utilitaires pour la tâche Celery
de suppression automatique des documents de traduction expirés.
"""
import logging
import requests
from datetime import timedelta, datetime
from typing import List, Optional, Tuple, Any
from django.conf import settings
from django.utils import timezone
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)

# Constantes
PAGE_SIZE = 100
REQUEST_TIMEOUT = 30


def parse_creation_date(date_str: str) -> Optional[datetime]:
    """
    Parse une chaîne de date en objet datetime.
    
    Args:
        date_str: Chaîne de date à parser
        
    Returns:
        Objet datetime ou None si le parsing échoue
    """
    if not date_str:
        return None
    
    # Essayer d'abord avec parse_datetime (gère mieux les timezones)
    parsed = parse_datetime(date_str)
    if parsed:
        return parsed
    
    # Fallback: essayer avec fromisoformat
    try:
        if 'T' in date_str:
            date_str_clean = date_str.replace('Z', '+00:00')
            return datetime.fromisoformat(date_str_clean)
        else:
            return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
    except (ValueError, AttributeError, TypeError) as e:
        logger.warning(f"Error parsing date '{date_str}': {e}")
        return None


def _to_date(dt: datetime) -> Any:
    """Convertit un datetime en date."""
    return dt.date() if hasattr(dt, 'date') else dt


def _has_next_page(data: dict, current_page: int, page_size: int = PAGE_SIZE) -> bool:
    """
    Vérifie s'il y a une page suivante dans les résultats paginés.
    
    Args:
        data: Données de réponse de l'API contenant 'count'
        current_page: Numéro de page actuel
        page_size: Taille de la page
        
    Returns:
        True s'il y a une page suivante, False sinon
    """
    total_count = data.get('count', 0)
    if total_count == 0:
        return False
    
    total_pages = (total_count + page_size - 1) // page_size
    return current_page < total_pages


def is_document_expired(created_at_str: str, retention_days: int, today: Optional = None) -> bool:
    """
    Vérifie si un document est expiré selon sa date de création et la période de rétention.
    
    Args:
        created_at_str: Date de création du document (chaîne)
        retention_days: Nombre de jours de rétention
        today: Date de référence (par défaut: aujourd'hui)
        
    Returns:
        True si le document est expiré, False sinon
    """
    if today is None:
        today = timezone.now().date()
    
    created_at = parse_creation_date(created_at_str)
    if not created_at:
        return False
    
    created_date = _to_date(created_at)
    expiration_date = created_date + timedelta(days=retention_days)
    return expiration_date < today


def _build_documents_url() -> str:
    """Construit l'URL de l'endpoint documents."""
    return f"{settings.LARA_API_URL}/api/lara/documents"


def _build_document_delete_url(document_id: str) -> str:
    """Construit l'URL de l'endpoint de suppression d'un document."""
    return f"{settings.LARA_API_URL}/api/lara/documents/{document_id}/delete"


def fetch_user_documents(user_uuid: str, page: int = 1, page_size: int = PAGE_SIZE) -> Tuple[Optional[dict], Optional[str]]:
    """
    Récupère une page de documents pour un utilisateur.
    
    Args:
        user_uuid: UUID de l'utilisateur
        page: Numéro de page
        page_size: Taille de la page
        
    Returns:
        Tuple (data, error_message) où data contient les résultats ou None en cas d'erreur
    """
    try:
        response = requests.get(
            _build_documents_url(),
            params={
                "user_uuid": user_uuid,
                "page": page,
                "page_size": page_size
            },
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code != 200:
            error_msg = f"HTTP {response.status_code}"
            logger.error(f"Error fetching documents for user {user_uuid} (page {page}): {error_msg}")
            return None, error_msg
        
        return response.json(), None
        
    except requests.RequestException as e:
        error_msg = f"Network error: {e}"
        logger.error(f"Network error fetching documents for user {user_uuid} (page {page}): {e}")
        return None, error_msg


def _extract_expired_document_ids(results: List[dict], retention_days: int, today) -> List[str]:
    """
    Extrait les IDs des documents expirés d'une liste de résultats.
    
    Args:
        results: Liste de documents depuis l'API
        retention_days: Nombre de jours de rétention
        today: Date de référence
        
    Returns:
        Liste des IDs des documents expirés
    """
    expired_documents = []
    
    for doc in results:
        document_id = doc.get('id')
        created_at_str = doc.get('created_at')
        
        if not document_id or not created_at_str:
            continue
        
        if is_document_expired(created_at_str, retention_days, today):
            expired_documents.append(document_id)
    
    return expired_documents


def get_all_expired_documents(user_uuid: str, retention_days: int) -> List[str]:
    """
    Récupère tous les documents expirés pour un utilisateur.
    
    Args:
        user_uuid: UUID de l'utilisateur
        retention_days: Nombre de jours de rétention
        
    Returns:
        Liste des IDs des documents expirés
    """
    expired_documents = []
    page = 1
    today = timezone.now().date()
    
    while True:
        data, error = fetch_user_documents(user_uuid, page, PAGE_SIZE)
        
        if error or not data:
            break
        
        results = data.get('results', [])
        if not results:
            break
        
        # Extraire les documents expirés de cette page
        expired_documents.extend(_extract_expired_document_ids(results, retention_days, today))
        
        # Vérifier s'il y a une page suivante
        if not _has_next_page(data, page):
            break
        
        page += 1
    
    return expired_documents


def delete_document(document_id: str, user_uuid: str) -> Tuple[bool, Optional[str]]:
    """
    Supprime un document via l'API Lara-bridge.
    
    Args:
        document_id: ID du document à supprimer
        user_uuid: UUID de l'utilisateur
        
    Returns:
        Tuple (success, error_message)
    """
    try:
        response = requests.post(
            _build_document_delete_url(document_id),
            params={"user_uuid": user_uuid},
            timeout=REQUEST_TIMEOUT
        )
        
        if response.status_code in [200, 201]:
            return True, None
        else:
            error_msg = f"HTTP {response.status_code}"
            logger.error(f"Error deleting document {document_id} for user {user_uuid}: {error_msg}")
            return False, error_msg
            
    except requests.RequestException as e:
        error_msg = f"Network error: {e}"
        logger.error(f"Network error deleting document {document_id} for user {user_uuid}: {e}")
        return False, error_msg

