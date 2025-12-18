import base64
import json
import logging
import os
import re
import time
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pprint import pprint
from urllib.parse import urlparse, unquote, urlencode

import django
import langdetect
import openpyxl
import requests
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now
from django.views.generic import TemplateView
from preferences import preferences
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from domains.models import Domain
from emails.models import EmailType
from emails.send_email import send_email
from glossaries.models import Glossary
from glossaries.processor import GlossaryProcessor
from languages.models import Language
from quoting.models import LanguageQuote, QuotePDF
from subscriptions.helpers import add_translations, translation_allowed
from subscriptions.models import SubscriptionType, UserSubscription
from subscriptions.permissions import SubscribedPermission, is_user_subscription_active
from subscriptions.utils import get_user_api_key
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from users.models import User, UserGroup

from .credentials import languages
from .helpers import (
    extract_language_codes_from_project,
    get_project_file,
    get_text_from_file,
    get_word_count,
    lowercase_file_extension,
    rename_file,
)

import csv
from typing import Optional

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile
from quoting.helpers import get_price_by_language_pair
from quoting.mail_helpers import generate_quote_pdf, send_quote_email
from quoting.services.quote import FormQuoteService

logger = logging.getLogger(__name__)


class BaseTemplateView(TemplateView):
    """
    Base TemplateView that adds environment variables to context
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SUPPORT_EMAIL'] = settings.SUPPORT_EMAIL
        context['SENDER_EMAIL'] = settings.SENDER_EMAIL
        context['QUOTE_CC_EMAIL'] = settings.QUOTE_CC_EMAIL
        return context


def _build_package_url(package_url: str) -> str:
    """
    Construit l'URL complète du package ZIP depuis l'URL relative retournée par Django.
    
    Détecte automatiquement les préfixes communs entre LARA_API_URL et package_url
    pour éviter les doublons sans hardcoder de valeurs.
    
    Args:
        package_url: URL relative du package retournée par Django
        
    Returns:
        str: URL complète du package
    """
    if not package_url:
        return ''
    
    # Si l'URL est déjà complète, la retourner telle quelle
    if package_url.startswith('http'):
        return package_url
    
    base_url = settings.LARA_API_URL.rstrip('/')
    package_path = package_url.lstrip('/')
    
    # Parser les URLs pour extraire uniquement les segments de chemin
    base_parsed = urlparse(base_url)
    package_segments = [seg for seg in package_path.split('/') if seg]
    
    # Extraire les segments de chemin de base_url (sans le protocole et le domaine)
    base_path_segments = [seg for seg in base_parsed.path.split('/') if seg]
    
    # Comparer le dernier segment de base_path avec le premier segment de package_path
    if base_path_segments and package_segments:
        if base_path_segments[-1] == package_segments[0]:
            # Le préfixe est déjà dans base_url, ne pas le répéter
            remaining_segments = '/'.join(package_segments[1:])
            return f"{base_url}/{remaining_segments}" if remaining_segments else base_url
    
    # Pas de préfixe commun, concaténation normale
    return f"{base_url}/{package_path}"


def _extract_error_message_from_response(exception: requests.HTTPError, default_message: str) -> str:
    """
    Extrait le message d'erreur depuis une exception HTTP.
    
    Args:
        exception: Exception HTTP de requests
        default_message: Message par défaut si l'extraction échoue
        
    Returns:
        str: Message d'erreur extrait ou message par défaut
    """
    if not hasattr(exception, 'response'):
        return default_message
    
    try:
        error_data = exception.response.json()
        return error_data.get('error', default_message)
    except (ValueError, AttributeError, json.JSONDecodeError):
        return default_message


def _build_admin_document_url(document_id: str) -> str:
    """
    Construit l'URL admin Django pour un document translation.
    
    Args:
        document_id: UUID du document
        
    Returns:
        str: URL complète vers la page admin du document
    """
    base_url = settings.LARA_API_URL.rstrip('/')
    return f"{base_url}/admin/translation/documenttranslation/{document_id}/change/"


def _get_user_email_from_uuid(user_uuid: str) -> str:
    """
    Récupère l'email d'un utilisateur depuis son UUID.
    
    Args:
        user_uuid: UUID de l'utilisateur
        
    Returns:
        str: Email de l'utilisateur ou SUPPORT_EMAIL par défaut
    """
    if not user_uuid:
        return settings.SUPPORT_EMAIL
    
    try:
        user = User.objects.filter(uuid=user_uuid).first()
        if user and user.email:
            return user.email
    except Exception as e:
        logger.warning(f"Could not retrieve user email for UUID {user_uuid}: {str(e)}")
    
    return settings.SUPPORT_EMAIL


def _send_quote_validation_notification(project_id: str, package_url: str, user_uuid: str = None) -> None:
    """
    Envoie un email de notification à l'admin lorsqu'un devis est validé.
    
    Args:
        project_id: UUID du document
        package_url: URL du package ZIP généré
        user_uuid: UUID de l'utilisateur qui a validé le devis (optionnel)
    """
    try:
        admin_url = _build_admin_document_url(project_id)
        full_package_url = _build_package_url(package_url)
        user_email = _get_user_email_from_uuid(user_uuid)
        
        send_email(
            settings.QUOTE_CC_EMAIL,
            EmailType.USER_ADM_VALIDE_QUOTE,
            'fr',
            {
                "lexa_username": 'admin',
                "lexa_sender_email": user_email,
                "url_admin_doctrans": admin_url,
                "url_translated_pack": full_package_url
            }
        )
    except Exception as e:
        logger.error(
            f"Error sending admin notification email for quote acceptance: {str(e)}",
            exc_info=True
        )
        # On continue même si l'email échoue


def _accept_quote_in_lara(project_id: str) -> tuple[bool, str, dict]:
    """
    Appelle lara-django pour accepter un devis et générer le package ZIP.
    
    Args:
        project_id: UUID du document
        
    Returns:
        tuple: (success: bool, error_message: str, response_data: dict)
    """
    try:
        response = requests.post(
            f"{settings.LARA_API_URL}/api/lara/document-status/{project_id}/accept-quote",
            timeout=30
        )
        response.raise_for_status()
        response_data = response.json()
        return True, "", response_data
    except requests.HTTPError as e:
        status_code = getattr(e.response, 'status_code', 'unknown') if hasattr(e, 'response') else 'unknown'
        logger.error(f"Failed to accept quote in LARA: HTTP {status_code}")
        error_msg = _extract_error_message_from_response(e, 'Échec de l\'acceptation du devis.')
        return False, error_msg, {}
    except requests.RequestException as e:
        logger.error(f"Network error accepting quote in LARA: {str(e)}")
        return False, "Une erreur est survenue lors de la communication avec le service de traduction.", {}
    except Exception as e:
        logger.error(f"Unexpected error accepting quote: {str(e)}", exc_info=True)
        return False, "Une erreur inattendue est survenue.", {}


class ExpertReviewAcceptView(BaseTemplateView):
    """
    Vue pour accepter un devis de révision experte.
    
    Quand l'utilisateur clique sur le lien dans le PDF, cette vue:
    - Appelle lara-django pour accepter le devis et générer le package ZIP
    - Affiche une page de confirmation
    """
    template_name = 'expert_review_accept.html'
    
    def get_context_data(self, **kwargs):
        """
        Traite l'acceptation du devis et prépare le contexte.
        """
        context = super().get_context_data(**kwargs)
        project_id = kwargs.get('project_id')
        
        if not project_id:
            context['error'] = "Identifiant de projet manquant."
            return context
        
        success, error_message, response_data = _accept_quote_in_lara(project_id)
        
        if success:
            context['success'] = True
            # Envoyer un email de notification à l'admin
            package_url = response_data.get('package_url', '')
            user_uuid = response_data.get('user_uuid')
            _send_quote_validation_notification(project_id, package_url, user_uuid)
        else:
            context['error'] = error_message
        
        context['project_id'] = project_id
        return context


# Constants
PAGINATION_PAGE_SIZE = 20
CACHE_TTL = 3600


def text_translation(request):
    """
    Text translation using LARA Translation API.

    Flow:
    1. Call /api/templates/find to get translation memory and glossary IDs (optional)
    2. Call /api/lara/translate-text with the text and optional parameters
    """
    
    text = request.POST.get('text')
    instructions = request.POST.get('instructions', '')
    words_count = get_word_count(text)
    symbols_count = len(text)
    
    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    user_uuid = request.user.uuid if request.user.is_authenticated else 'anonymous'
    
    logger.info(f"LARA_TRANSLATION_START - User: {user_id} ({user_uuid}) - Text length: {len(text)} chars - Words: {words_count} - Source: {request.POST.get('source_language')} -> Target: {request.POST.get('target_language')} - Domain: {request.POST.get('domain_name')}")

    if not translation_allowed(request=request, words_count=words_count, symbols_count=symbols_count):
        logger.warning(f"LARA_TRANSLATION_DENIED - User: {user_id} - Translation not allowed - Words: {words_count} - Symbols: {symbols_count}")
        return JsonResponse(
            {"detail": "You are not allowed to translate such amount of data"},
            status=status.HTTP_400_BAD_REQUEST
        )

    source_language = request.POST.get('source_language')
    target_language = request.POST.get('target_language')
    domain_name = request.POST.get('domain_name')

    # Step 1: Fetch template to get translation memory and glossary IDs (optional)
    translation_memory_id = None
    glossary_id = None

    logger.info(f"LARA_TEMPLATES_FIND_START - User: {user_id} - Params: domain={domain_name}, source={source_language}, target={target_language}")
    
    try:
        template_response = requests.get(
            f"{settings.LARA_API_URL}/api/templates/find",
            params={
                'domain': domain_name,
                'sourceLanguage': source_language,
                'targetLanguage': target_language,
            },
            timeout=10
        )

        logger.info(f"LARA_TEMPLATES_FIND_RESPONSE - User: {user_id} - Status: {template_response.status_code} - Response time: {template_response.elapsed.total_seconds()}s")
        
        if template_response.status_code == 200:
            templates = template_response.json()
            logger.debug(f"LARA_TEMPLATES_FIND_SUCCESS - User: {user_id} - Templates found: {len(templates) if templates else 0}")
            if templates and len(templates) > 0:
                template = templates[0]
                translation_memory_id = template.get('translationMemoryId')
                glossary_id = template.get('glossaryId')
                logger.info(f"LARA_TEMPLATES_SELECTED - User: {user_id} - TM ID: {translation_memory_id} - Glossary ID: {glossary_id}")
        else:
            logger.warning(f"LARA_TEMPLATES_FIND_ERROR - User: {user_id} - Status: {template_response.status_code} - Response: {template_response.text}")
    except requests.RequestException as e:
        logger.error(f"LARA_TEMPLATES_FIND_EXCEPTION - User: {user_id} - Exception: {str(e)}")
        # If template fetch fails, continue without memory/glossary
        pass

    # Step 2: Build translation request payload
    translate_payload = {
        "accessKeyId": settings.LARA_ACCESS_KEY_ID,
        "accessKeySecret": settings.LARA_ACCESS_KEY_SECRET,
        "text": text,
        "source": source_language,
        "target": target_language,
    }

    # Add domain if present
    if domain_name:
        translate_payload["domain"] = domain_name

    # Add custom instructions if provided
    if instructions:
        translate_payload["instructions"] = instructions

    # Add translation memory if found (optional)
    if translation_memory_id:
        translate_payload["adaptTo"] = str(translation_memory_id)

    # Add glossary if found (optional)
    if glossary_id:
        translate_payload["glossaries"] = str(glossary_id)

    logger.info(f"LARA_TRANSLATE_START - User: {user_id} - Payload: source={source_language}, target={target_language}, domain={domain_name}, instructions={bool(instructions)}, adaptTo={translation_memory_id}, glossaries={glossary_id}, text_length={len(text)}")

    # Step 3: Call LARA translation API
    try:
        response = requests.post(
            f"{settings.LARA_API_URL}/api/lara/translate-text",
            json=translate_payload,
            timeout=60
        )
        
        logger.info(f"LARA_TRANSLATE_RESPONSE - User: {user_id} - Status: {response.status_code} - Response time: {response.elapsed.total_seconds()}s")
        
    except requests.RequestException as e:
        logger.error(f"LARA_TRANSLATE_EXCEPTION - User: {user_id} - Exception: {str(e)}")
        return JsonResponse(
            {"detail": f"Translation service unavailable: {str(e)}"},
            status=status.HTTP_503_SERVICE_UNAVAILABLE
        )

    if response.status_code == 200:
        result = response.json()
        translated_text = result.get("translation", "")
        
        logger.info(f"LARA_TRANSLATE_SUCCESS - User: {user_id} - Translated text length: {len(translated_text)} - Quality feedback: {bool(result.get('quality_feedback'))}")
        logger.debug(f"LARA_TRANSLATE_RESULT - User: {user_id} - Original: '{text[:100]}...' - Translated: '{translated_text[:100]}...'")

        # Format response for frontend compatibility
        formatted_result = {
            "translated_text": [translated_text],
        }

        # Add quality feedback if available (text comment, not a score)
        if result.get("quality_feedback"):
            formatted_result["quality_feedback"] = result.get("quality_feedback")
            logger.debug(f"LARA_QUALITY_FEEDBACK - User: {user_id} - Feedback: {result.get('quality_feedback')}")

        # Update user translation quota
        add_translations(request, words_count=words_count, symbols_count=symbols_count)
        logger.info(f"LARA_TRANSLATION_COMPLETE - User: {user_id} - Quota updated: +{words_count} words, +{symbols_count} symbols")

        return JsonResponse(formatted_result)

    # Handle translation errors
    try:
        error_detail = response.json().get('detail', response.text)
    except (ValueError, KeyError):
        error_detail = response.text
    
    logger.error(f"LARA_TRANSLATE_ERROR - User: {user_id} - Status: {response.status_code} - Error: {error_detail}")
    
    return JsonResponse(
        {"detail": f"Translation error: {error_detail}"},
        status=response.status_code
    )


def file_translate(request):
    """
    Document translation using LARA Translation API (Django Lara).

    Flow:
    1. Call /api/templates/find to get translation memory and glossary IDs
    2. Call /api/lara/translate-document with the file and template parameters
    """

    files = request.FILES.getlist('document[]', [])
    # Vérification que l'utilisateur a une subscription active
    try:
        get_user_api_key(request.user)
    except ValueError:
        return JsonResponse({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)

    cache_data = cache.get(f"{request.user.uuid}")

    if cache_data:
        cache.delete(f"{request.user.uuid}")

    # Calculate statistics per file (not cumulative)
    total_words_count = 0
    total_symbols_count = 0
    processed_files = []
    file_stats = []  # Store individual stats for each file
    for file in files:
        # Ne plus renommer le fichier en "file.ext" afin de conserver le nom original
        file_words, file_texts, processed_file = get_text_from_file(file)
        file_words_count = len(file_words)
        file_symbols_count = sum(len(word) for word in file_texts)
        total_words_count += file_words_count
        total_symbols_count += file_symbols_count
        processed_files.append(processed_file)
        file_stats.append({
            'words_count': file_words_count,
            'symbols_count': file_symbols_count
        })

    if not translation_allowed(request, words_count=total_words_count, files_count=len(files), symbols_count=total_symbols_count):
        return JsonResponse({"detail": "You are out of translation for now"}, status=status.HTTP_400_BAD_REQUEST)

    source_language = request.POST.get('source_language')
    target_language = request.POST.get('target_language')
    domain_id = request.POST.get('domain_id')
    domain_name_param = request.POST.get('domain_name')  # Direct domain name from API

    # Get glossaries from request (comma-separated list of glossary IDs)
    glossary_param = request.POST.get('glossary', 'none')
    if glossary_param and glossary_param != 'none':
        user_glossaries = [g.strip() for g in glossary_param.split(',') if g.strip()]
    else:
        user_glossaries = []

    # Get domain: either by ID (from web interface) or by name (from API)
    domain = None
    domain_name = ''
    if domain_id:
        # Web interface sends domain_id
        domain = Domain.objects.filter(id=domain_id).first()
        if domain:
            domain_name = domain.name  # English name for templates/find
    elif domain_name_param:
        # API sends domain_name directly
        domain_name = domain_name_param
        # Try to find matching domain for domainId
        domain = Domain.objects.filter(name__iexact=domain_name_param).first()
        if not domain:
            domain = Domain.objects.filter(french_name__iexact=domain_name_param).first()

    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    logger.info(f"LARA_DOC_TRANSLATE_START - User: {user_id} - Files: {len(files)} - Source: {source_language} -> Target: {target_language} - Domain: {domain_name} (id: {domain_id}) - Glossaries: {user_glossaries}")

    # Template lookup is now done automatically by lara-django backend
    # We just need to send the domain and language info

    # Translate each document via Django Lara
    # Utiliser les fichiers traités (PDF convertis en DOCX si nécessaire)
    projects = []
    for idx, file in enumerate(processed_files):
        file = lowercase_file_extension(file)

        # Build form data for Django Lara
        # Note: Template, translation memory and glossary are now auto-detected by the backend
        # based on domain and language pair. User-selected glossaries are still sent.
        translate_data = {
            'accessKeyId': settings.LARA_ACCESS_KEY_ID,
            'accessKeySecret': settings.LARA_ACCESS_KEY_SECRET,
            'source': source_language,
            'target': target_language,
            'userToken': str(request.user.uuid) if request.user.is_authenticated else '',
        }

        # Send domain info: either from domain_id or from domain lookup by name
        if domain_id:
            translate_data['domainId'] = int(domain_id)
        elif domain:
            # Domain found by name lookup - send its ID
            translate_data['domainId'] = domain.id
        if domain_name:
            translate_data['domain'] = domain_name  # English domain name

        # Send user-selected glossaries (additional to auto-detected ones from template)
        if user_glossaries:
            translate_data['glossaries'] = ','.join(user_glossaries)

        # Add document statistics (per file, not cumulative)
        translate_data['wordsCount'] = file_stats[idx]['words_count']
        translate_data['charactersCount'] = file_stats[idx]['symbols_count']

        # Log payload complet avant envoi (sans les credentials)
        payload_log = {k: v for k, v in translate_data.items() if k not in ['accessKeyId', 'accessKeySecret']}
        logger.info(f"LARA_DOC_TRANSLATE_CALL - User: {user_id} - File: {file.name} - Payload: {payload_log}")

        try:
            response = requests.post(
                f"{settings.LARA_API_URL}/api/lara/translate-document",
                data=translate_data,
                files={'file': (file.name, file, file.content_type)},
                timeout=300  # 5 minutes timeout for large documents
            )

            logger.info(f"LARA_DOC_TRANSLATE_RESPONSE - User: {user_id} - File: {file.name} - Status: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                projects.append({
                    'id': result.get('id'),
                    'file_name': file.name,
                    'file_extension': os.path.splitext(file.name)[1],
                    'status': result.get('status'),
                    'download_url': result.get('downloadUrl')
                })
            else:
                logger.error(f"LARA_DOC_TRANSLATE_ERROR - User: {user_id} - File: {file.name} - Response: {response.text}")
                projects.append({
                    'id': None,
                    'file_name': file.name,
                    'file_extension': os.path.splitext(file.name)[1],
                    'status': 'Error',
                    'error': response.text
                })

        except requests.RequestException as e:
            logger.error(f"LARA_DOC_TRANSLATE_EXCEPTION - User: {user_id} - File: {file.name} - Exception: {str(e)}")
            projects.append({
                'id': None,
                'file_name': file.name,
                'file_extension': os.path.splitext(file.name)[1],
                'status': 'Error',
                'error': str(e)
            })

    # Send notification email for successful translations
    for project in projects:
        if project.get('id'):
            send_email(
                settings.QUOTE_CC_EMAIL,
                EmailType.USER_ADM_TR_FILE,
                'fr',
                {
                    "lexa_username": 'admin',
                    "lexa_sender_email": request.user.email if request.user.email else '(no email)',
                    "url_source_file": f"Document traduit via LARA - {project['file_name']}",
                    "translation_name": project['file_name'],
                    "file_ext": project['file_extension']
                }
            )

    # Check for errors in projects
    successful_projects = [p for p in projects if p.get('id')]
    failed_projects = [p for p in projects if not p.get('id')]

    # If all projects failed, return error
    if not successful_projects and failed_projects:
        error_messages = [p.get('error', 'Unknown error') for p in failed_projects]
        logger.error(f"LARA_DOC_TRANSLATE_ALL_FAILED - User: {user_id} - Errors: {error_messages}")
        return JsonResponse({
            "detail": "Translation failed",
            "errors": error_messages
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Update translation quota only for successful translations
    if successful_projects:
        add_translations(request, words_count=total_words_count,
                         files_count=len(successful_projects), symbols_count=total_symbols_count)

    logger.info(f"LARA_DOC_TRANSLATE_COMPLETE - User: {user_id} - Successful: {len(successful_projects)} - Failed: {len(failed_projects)}")

    # If some projects failed but some succeeded, return partial success with warning
    response_data = {
        "project_ids": [p.get('id') for p in successful_projects],
        "display_popup": False if get_price_by_language_pair(
            source_language=source_language,
            target_language=target_language) else True
    }

    if failed_projects:
        response_data["warnings"] = [{"file": p.get('file_name'), "error": p.get('error')} for p in failed_projects]
        return JsonResponse(response_data, status=status.HTTP_207_MULTI_STATUS)

    return JsonResponse(response_data)


class GetDomainsView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        # Récupérer les domaines directement depuis la base de données
        domains = Domain.objects.all().order_by('-featured', 'name')
        
        # Filtrer par domain_group si fourni
        if self.request.query_params.get('domain_group'):
            if request.LANGUAGE_CODE == 'fr':
                domains = domains.filter(
                    domain_group__french_name=self.request.query_params.get('domain_group'))
            else:
                domains = domains.filter(
                    domain_group__name=self.request.query_params.get('domain_group'))

        if domains.count() == 0 and preferences.DefaultTranslation.enabled:
            if request.LANGUAGE_CODE == 'fr':
                default_domain_name = preferences.DefaultTranslation.french_name if preferences.DefaultTranslation.french_name else preferences.DefaultTranslation.name
                return Response(
                    {"data": [{"name": default_domain_name, "icon": None}], "default_domain": True},
                )
            else:
                return Response({"data": [{"name": preferences.DefaultTranslation.name, "icon": None}], "default_domain": True}, )
        
        # Construire la liste avec id, nom et icône
        domain_data = []
        for domain in domains:
            if request.LANGUAGE_CODE == 'fr':
                domain_name = domain.french_name if domain.french_name else domain.name
            else:
                domain_name = domain.name

            domain_data.append({
                "id": domain.id,
                "name": domain_name,
                "english_name": domain.name,  # Toujours inclure le nom anglais pour LARA
                "icon": domain.icon
            })

        return Response({"data": domain_data, "default_domain": False}, status=status.HTTP_200_OK)


def _fetch_document_from_lara(project_id: str) -> dict:
    """
    Récupère les données d'un document depuis lara-django.
    
    Args:
        project_id: UUID du document
        
    Returns:
        dict: Données du document
        
    Raises:
        requests.RequestException: Si la requête échoue
        ValueError: Si le document n'est pas trouvé
    """
    try:
        response = requests.get(
            f"{settings.LARA_API_URL}/api/lara/document-status/{project_id}",
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.HTTPError as e:
        logger.error(f"Failed to fetch document from LARA: {response.status_code}")
        raise ValueError("Document not found in LARA") from e
    except requests.RequestException as e:
        logger.error(f"Network error fetching document from LARA: {str(e)}")
        raise


def _update_document_status_in_lara(project_id: str, new_status: str) -> None:
    """
    Met à jour le statut d'un document dans lara-django.
    
    Args:
        project_id: UUID du document
        new_status: Nouveau statut à assigner
        
    Raises:
        requests.RequestException: Si la requête échoue
        ValueError: Si la mise à jour échoue
    """
    try:
        response = requests.patch(
            f"{settings.LARA_API_URL}/api/lara/document-status/{project_id}/update",
            json={"status": new_status},
            timeout=10
        )
        response.raise_for_status()
    except requests.HTTPError as e:
        logger.error(f"Failed to update document status in LARA: {response.status_code}")
        raise ValueError("Failed to update document status") from e
    except requests.RequestException as e:
        logger.error(f"Network error updating document status in LARA: {str(e)}")
        raise


def _build_quote_context(
    doc_data: dict,
    quote_price: LanguageQuote,
    words_count: int,
    project_id: str,
    user: User,
    request
) -> dict:
    """
    Construit le contexte pour le template PDF de devis.
    
    Args:
        doc_data: Données du document depuis lara-django
        quote_price: Objet LanguageQuote avec les prix
        words_count: Nombre de mots à traduire
        project_id: UUID du document
        user: Utilisateur Django
        request: Objet request Django pour générer les URLs
        
    Returns:
        dict: Variables de contexte pour le template
    """
    source_lang = doc_data.get('source_language', '')
    target_lang = doc_data.get('target_language', '')
    
    # Calcul du prix total avec application du minimum
    total_price = max(
        words_count * quote_price.price,
        settings.MINIMUM_QUOTE_AMOUNT
    )
    
    working_days = FormQuoteService.get_working_days(words_count, quote_price)
    company_name = user.group.name if user.group else "Administrator"
    quote_number = (
        user.group.generate_quoting_number()
        if user.group
        else f"{now().strftime('%Y/%m')}/0"
    )
    sender_email = settings.SENDER_EMAIL
    
    return {
        "email": sender_email,
        "username": user.username,
        "user_email": user.email,
        "company": company_name,
        "contract_name": company_name,
        "language_pair": f"{source_lang.upper()} -> {target_lang.upper()}",
        "file_name": doc_data.get('filename', 'document'),
        "word_price": quote_price.price,
        "words_count": words_count,
        "working_days": working_days,
        "total_price": total_price,
        "created_at": now(),
        "seller_email": sender_email,
        "quote_number": quote_number,
        "accept_expert_revision_file_absolute_url": request.build_absolute_uri(
            f"/expert-review/accept/{project_id}"
        )
    }


def _create_quote_pdf_record(
    user: User,
    pdf_bytes: bytes,
    filename: str,
    context_variables: dict,
    language_quote: LanguageQuote,
    source_language: str,
    target_language: str
) -> QuotePDF:
    """
    Crée un enregistrement QuotePDF dans la base de données.
    
    Args:
        user: Utilisateur qui a créé le devis
        pdf_bytes: Contenu binaire du PDF
        filename: Nom du fichier PDF
        context_variables: Variables de contexte du PDF
        language_quote: Instance de LanguageQuote utilisée
        source_language: Code de la langue source
        target_language: Code de la langue cible
        
    Returns:
        QuotePDF: Instance créée
    """
    return QuotePDF.objects.create(
        user=user,
        words_count=context_variables.get('words_count', 0),
        total_amount=context_variables.get('total_price', 0),
        language_quote=language_quote,
        source_language=source_language.lower() if source_language else '',
        target_language=target_language.lower() if target_language else '',
        pdf_file=ContentFile(pdf_bytes, name=filename)
    )


class FileExpertRevisionView(APIView):
    """
    Vue pour la révision experte de fichiers.
    
    Gère la demande de devis pour une révision experte :
    - Met à jour le statut du document dans lara-django
    - Envoie un email avec un PDF de devis au client
    """
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        """
        Traite une demande de révision experte.
        
        Args:
            request.data contient:
                - project_id: UUID du document dans lara-django
                - file_url: URL du fichier traduit (optionnel)
        """
        project_id = request.data.get('project_id')
        
        if not project_id:
            return Response(
                {"detail": "project_id is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Récupérer les données du document
            doc_data = _fetch_document_from_lara(project_id)
            source_lang = doc_data.get('source_language', '')
            target_lang = doc_data.get('target_language', '')
            
            # Vérifier qu'un devis existe pour cette paire de langues
            quote_price = get_price_by_language_pair(source_lang, target_lang)
            if not quote_price:
                return Response(
                    {"detail": "No quote available for this language pair"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupérer le nombre de mots
            words_count = doc_data.get('words_count', 0) or 0
            if words_count == 0:
                logger.warning(f"Document {project_id} has no words_count, defaulting to 0")
            
            # Construire le contexte pour le PDF
            context_variables = _build_quote_context(
                doc_data, quote_price, words_count, project_id, request.user, request
            )
            
            # Mettre à jour le statut dans lara-django
            _update_document_status_in_lara(project_id, "quote_requested")
            
            # Générer le PDF
            pdf_bytes, filename = generate_quote_pdf(context_variables)
            
            # Envoyer l'email avec le PDF
            send_quote_email(
                request.user.id,
                request,
                context_variables,
                pdf_bytes,
                filename
            )
            
            # Créer l'enregistrement QuotePDF après l'envoi de l'email
            _create_quote_pdf_record(
                user=request.user,
                pdf_bytes=pdf_bytes,
                filename=filename,
                context_variables=context_variables,
                language_quote=quote_price,
                source_language=source_lang,
                target_language=target_lang
            )
            
            logger.info(f"Quote request sent for document {project_id} - User: {request.user.id}")
            return Response({"detail": "Quote request sent successfully"})
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(f"Validation error in expert revision request: {error_msg}")
            status_code = status.HTTP_404_NOT_FOUND if "not found" in error_msg.lower() else status.HTTP_500_INTERNAL_SERVER_ERROR
            return Response({"detail": error_msg}, status=status_code)
        except requests.RequestException as e:
            logger.error(f"Error communicating with LARA API: {str(e)}")
            return Response(
                {"detail": f"Error communicating with translation service: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        except Exception as e:
            logger.error(f"Unexpected error in expert revision request: {str(e)}", exc_info=True)
            return Response(
                {"detail": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


def _map_lara_project_to_frontend(lara_result: dict) -> dict:
    """
    Mappe une réponse de projet LARA vers le format attendu par le frontend.
    
    Args:
        lara_result: Dictionnaire de réponse LARA depuis document-status
        
    Returns:
        Dictionnaire au format frontend
    """
    source_lang, target_lang = extract_language_codes_from_project(lara_result)
    
    res = {
        'id': lara_result.get('id'),
        'status': map_lara_status_to_lexa(lara_result.get('status')),
        'source_file_name': lara_result.get('filename', ''),
        'source_language': source_lang,
        'target_language': target_lang,
        'translated_file': lara_result.get('downloadUrl') if lara_result.get('status') == 'translated' else None,
        'reviewed_file': None,  # LARA doesn't have post-editing yet
        'display_popup': not bool(get_price_by_language_pair(source_lang, target_lang))
    }
    
    # Add error reason if status is error
    if lara_result.get('status') == 'error':
        res['error_reason'] = lara_result.get('error_message', 'Translation failed')
    
    return res


def get_projects_by_ids(request):
    """
    Récupère le statut des projets de traduction par leurs IDs.
    
    Appelle l'endpoint Django Lara document-status et mappe les réponses
    vers le format attendu par le frontend.
    
    Args:
        request: Requête HTTP contenant les project_id[] en paramètres
        
    Returns:
        Liste de dictionnaires représentant les projets au format frontend
    """
    project_ids = request.query_params.getlist('project_id[]', [])
    responses = []

    for project_id in project_ids:
        try:
            response = requests.get(
                f"{settings.LARA_API_URL}/api/lara/document-status/{project_id}",
                timeout=10
            )

            if response.status_code == 200:
                lara_result = response.json()
                mapped_result = _map_lara_project_to_frontend(lara_result)
                responses.append(mapped_result)
            else:
                logger.error(f"LARA_DOC_STATUS_ERROR - Project: {project_id} - Status: {response.status_code}")
                responses.append({
                    'id': project_id,
                    'status': 'Error',
                    'error_reason': f'Failed to get status: {response.status_code}'
                })

        except requests.RequestException as e:
            logger.error(f"LARA_DOC_STATUS_EXCEPTION - Project: {project_id} - Exception: {str(e)}")
            responses.append({
                'id': project_id,
                'status': 'Error',
                'error_reason': str(e)
            })

    return responses


def map_lara_status_to_lexa(lara_status):
    """
    Map Django Lara status to Lexa frontend expected status.

    Lara statuses: pending, processing, translated, quote_requested, quote_accepted, error
    Lexa statuses: Being translated, Translated, Sent to post-editing not accepted yet, Sent to post-editing accepted, Error
    """
    status_map = {
        'pending': 'Being translated',
        'processing': 'Being translated',
        'translated': 'Translated',
        'quote_requested': 'Sent to post-editing, not accepted yet',
        'quote_accepted': 'Sent to post-editing, accepted',
        'error': 'Error'
    }
    return status_map.get(lara_status, 'Being translated')


class SingleProjectView(APIView):
    """
    Vue pour récupérer le statut des projets de traduction.
    
    Permet uniquement la lecture (GET) des statuts des projets.
    La suppression de projets n'est plus supportée.
    """
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        """
        Récupère le statut des projets de traduction par leurs IDs.
        
        Args:
            request: Requête HTTP contenant les project_id[] en paramètres de requête
            
        Returns:
            Response: Liste des statuts des projets au format JSON
        """
        responses = get_projects_by_ids(request)
        return Response(responses, status=status.HTTP_200_OK)


class LanguageDetectView(APIView):
    WORDS_COUNT_FOR_DETECTION = 500
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        files = request.FILES.getlist('document[]', [])
        words_count = 0
        symbols_count = 0
        result = []
        for file in files:
            file = lowercase_file_extension(file)

            try:
                get_user_api_key(request.user)  # Vérification de subscription active
            except ValueError:
                return JsonResponse({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
            text_for_detection, words_count, symbols_count = self.get_text_for_detection(
                file=file,
                words_count=words_count,
                symbols_count=symbols_count
            )
            if translation_allowed(request, files_count=len(files), words_count=words_count,
                                   symbols_count=symbols_count):

                try:
                    tmp_language = langdetect.detect(text_for_detection)
                    language = Language.objects.filter(abbreviation__iexact=tmp_language.upper()).values_list(
                        'abbreviation', flat=True).first()
                except langdetect.LangDetectException:
                    language = Language.objects.values_list(
                        'abbreviation', flat=True).first()
                if not language:
                    language = Language.objects.all().values_list(
                        'abbreviation', flat=True).first()

                result.append(
                    {
                        "file_name": f'{file.name}',
                        "abbreviation": language.upper()
                    }
                )
            else:
                return JsonResponse({"detail": "You are not allowed to translate such amount of data"},
                                    status=status.HTTP_400_BAD_REQUEST)
        cache.set(f"{request.user.uuid}", {"words_count": words_count, "symbols_count": symbols_count},
                  timeout=CACHE_TTL)
        return JsonResponse({'languages': result}, status=status.HTTP_200_OK)

    @staticmethod
    def rename_file(file: InMemoryUploadedFile, file_name: str = None):
        if not file_name:
            file_extension = os.path.splitext(file.name)[1]
            file.name = f'file{file_extension}'
        else:
            file.name = file_name
        return file

    def get_text_for_detection(self, file, words_count, symbols_count):
        """
        Extrait le texte d'un fichier pour la détection de langue.
        
        Args:
            file: Fichier à traiter
            words_count: Compteur de mots (sera incrémenté)
            symbols_count: Compteur de symboles (sera incrémenté)
            
        Returns:
            tuple: (text_for_detection, words_count, symbols_count)
        """
        file_name = file.name
        file = self.rename_file(file)
        formated_texts, full_text, processed_file = get_text_from_file(file)
        words_count += len(formated_texts)
        symbols_count += sum(len(word) for word in full_text)
        text_for_detection = ' '.join(
            formated_texts[:self.WORDS_COUNT_FOR_DETECTION])
        # Le fichier traité n'est pas utilisé pour la détection de langue,
        # seulement pour l'extraction de texte
        return text_for_detection, words_count, symbols_count


class DetectTextLanguageView(APIView):
    WORDS_COUNT_FOR_DETECTION = 500
    permission_classes = (SubscribedPermission, IsAuthenticated)

    @staticmethod
    def text_string_to_array(text):
        text = re.sub(r'<[^>]*>', '', text)
        text = text.split()
        return text

    def post(self, request):

        text = request.data.get('text')
        text_for_detection = self.get_text_for_detection(text)
        symbols_count = len(text_for_detection)
        texts = self.text_string_to_array(text)
        if translation_allowed(request, words_count=len(texts), symbols_count=symbols_count):
            try:
                tmp_language = langdetect.detect(text_for_detection)
                language = Language.objects.filter(abbreviation__iexact=tmp_language.upper()).values_list(
                    'abbreviation', flat=True).first()
                if not language:
                    language = Language.objects.all().values_list(
                        'abbreviation', flat=True).first()
            except langdetect.LangDetectException:
                return Response({"detail": "Source text should not be blank"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"language": language.upper()})
        return Response({"detail": "You are not allowed to translate such amount of data"},
                        status=status.HTTP_400_BAD_REQUEST)

    def get_text_for_detection(self, text):
        text = self.text_string_to_array(text)

        text_for_detection = ' '.join(text[:self.WORDS_COUNT_FOR_DETECTION])
        return text_for_detection




class DisplayMessage(BaseTemplateView):
    template_name = "alert.html"
    
    # SVG Icons dictionary
    ICONS = {
        'EXCLAMATION_POINT': {
            'svg': '<span class="text-white font-bold text-xl leading-none select-none">!</span>',
            'bg_color': '#EF4444',
            'border_color': '#FCA5A5'
        },
        'CHECK': {
            'svg': '<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"></path></svg>',
            'bg_color': '#10B981',
            'border_color': '#86EFAC'
        },
        'QUESTION': {
            'svg': '<span class="text-white font-bold text-xl leading-none select-none">?</span>',
            'bg_color': '#3B82F6',
            'border_color': '#93C5FD'
        },
        'INFO': {
            'svg': '<span class="text-white font-bold text-xl leading-none select-none">i</span>',
            'bg_color': '#0EA5E9',
            'border_color': '#7DD3FC'
        },
        'TRASH': {
            'svg': '<svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M20.25 4.5H16.5V3.75C16.5 3.15326 16.2629 2.58097 15.841 2.15901C15.419 1.73705 14.8467 1.5 14.25 1.5H9.75C9.15326 1.5 8.58097 1.73705 8.15901 2.15901C7.73705 2.58097 7.5 3.15326 7.5 3.75V4.5H3.75C3.55109 4.5 3.36032 4.57902 3.21967 4.71967C3.07902 4.86032 3 5.05109 3 5.25C3 5.44891 3.07902 5.63968 3.21967 5.78033C3.36032 5.92098 3.55109 6 3.75 6H4.5V19.5C4.5 19.8978 4.65804 20.2794 4.93934 20.5607C5.22064 20.842 5.60218 21 6 21H18C18.3978 21 18.7794 20.842 19.0607 20.5607C19.342 20.2794 19.5 19.8978 19.5 19.5V6H20.25C20.4489 6 20.6397 5.92098 20.7803 5.78033C20.921 5.63968 21 5.44891 21 5.25C21 5.05109 20.921 4.86032 20.7803 4.71967C20.6397 4.57902 20.4489 4.5 20.25 4.5ZM9 3.75C9 3.55109 9.07902 3.36032 9.21967 3.21967C9.36032 3.07902 9.55109 3 9.75 3H14.25C14.4489 3 14.6397 3.07902 14.7803 3.21967C14.921 3.36032 15 3.55109 15 3.75V4.5H9V3.75ZM18 19.5H6V6H18V19.5ZM10.5 9.75V15.75C10.5 15.9489 10.421 16.1397 10.2803 16.2803C10.1397 16.421 9.94891 16.5 9.75 16.5C9.55109 16.5 9.36032 16.421 9.21967 16.2803C9.07902 16.1397 9 15.9489 9 15.75V9.75C9 9.55109 9.07902 9.36032 9.21967 9.21967C9.36032 9.07902 9.55109 9 9.75 9C9.94891 9 10.1397 9.07902 10.2803 9.21967C10.421 9.36032 10.5 9.55109 10.5 9.75ZM15 9.75V15.75C15 15.9489 14.921 16.1397 14.7803 16.2803C14.6397 16.421 14.4489 16.5 14.25 16.5C14.0511 16.5 13.8603 16.421 13.7197 16.2803C13.579 16.1397 13.5 15.9489 13.5 15.75V9.75C13.5 9.55109 13.579 9.36032 13.7197 9.21967C13.8603 9.07902 14.0511 9 14.25 9C14.4489 9 14.6397 9.07902 14.7803 9.21967C14.921 9.36032 15 9.55109 15 9.75Z"/></svg>'
        },
        'X': {
            'svg': '<svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M6 18L18 6M6 6l12 12"></path></svg>'
        },
        'SAVE': {
            'svg': '<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>'
        }
    }
    
    def __init__(self, icon_name='EXCLAMATION_POINT', title='', message='', 
                 button1_text='Cancel', button1_bg_color='#FFFFFF', button1_text_color='#181932', button1_icon_name=None,
                 button2_text='Confirm', button2_bg_color='#EF4444', button2_text_color='#FFFFFF', button2_icon_name=None):
        super().__init__()
        self.icon_name = icon_name
        self.title = title
        self.message = message
        self.button1_text = button1_text
        self.button1_bg_color = button1_bg_color
        self.button1_text_color = button1_text_color
        self.button1_icon_name = button1_icon_name
        self.button2_text = button2_text
        self.button2_bg_color = button2_bg_color
        self.button2_text_color = button2_text_color
        self.button2_icon_name = button2_icon_name
        self.user_selection = 0
    
    def get_icon_data(self, icon_name):
        """Get icon data from the ICONS dictionary"""
        return self.ICONS.get(icon_name, self.ICONS['EXCLAMATION_POINT'])
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Main icon
        icon_data = self.get_icon_data(self.icon_name)
        context['icon_svg'] = icon_data['svg']
        context['icon_bg_color'] = icon_data['bg_color']
        context['icon_border_color'] = icon_data['border_color']
        
        # Text content
        context['title'] = self.title
        context['message'] = self.message
        
        # Button 1
        context['button1_text'] = self.button1_text
        context['button1_bg_color'] = self.button1_bg_color
        context['button1_text_color'] = self.button1_text_color
        if self.button1_icon_name:
            button1_icon_data = self.get_icon_data(self.button1_icon_name)
            context['button1_icon_svg'] = button1_icon_data['svg']
        else:
            context['button1_icon_svg'] = None
        
        # Button 2
        context['button2_text'] = self.button2_text
        context['button2_bg_color'] = self.button2_bg_color
        context['button2_text_color'] = self.button2_text_color
        if self.button2_icon_name:
            button2_icon_data = self.get_icon_data(self.button2_icon_name)
            context['button2_icon_svg'] = button2_icon_data['svg']
        else:
            context['button2_icon_svg'] = None
            
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle button selection"""
        try:
            data = json.loads(request.body)
            selection = data.get('selection', 0)
            self.user_selection = selection
            return JsonResponse({'status': 'success', 'selection': selection})
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    
    def get_user_selection(self):
        """Return the user's selection (1 or 2)"""
        return self.user_selection
    

# Function to create and display a message dialog
def show_alert_dialog(icon_name='EXCLAMATION_POINT', title='', message='', 
                      button1_text='Cancel', button1_bg_color='#FFFFFF', button1_text_color='#181932', button1_icon_name=None,
                      button2_text='Confirm', button2_bg_color='#EF4444', button2_text_color='#FFFFFF', button2_icon_name=None):
    """
    Create and return a DisplayMessage instance with the specified parameters
    
    Parameters:
    - icon_name: Icon to display at top of modal (from ICONS dictionary)
    - title: Title of the message
    - message: Message text below title
    - button1_text: Text for first button
    - button1_bg_color: Background color for first button
    - button1_text_color: Text color for first button
    - button1_icon_name: Icon for first button (optional)
    - button2_text: Text for second button
    - button2_bg_color: Background color for second button
    - button2_text_color: Text color for second button
    - button2_icon_name: Icon for second button (optional)
    
    Returns:
    - DisplayMessage instance
    """
    return DisplayMessage(
        icon_name=icon_name,
        title=title,
        message=message,
        button1_text=button1_text,
        button1_bg_color=button1_bg_color,
        button1_text_color=button1_text_color,
        button1_icon_name=button1_icon_name,
        button2_text=button2_text,
        button2_bg_color=button2_bg_color,
        button2_text_color=button2_text_color,
        button2_icon_name=button2_icon_name
    )
