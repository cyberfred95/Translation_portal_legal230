import base64
import json
import os
import re
import time
import logging
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pprint import pprint
from urllib.parse import urlparse, unquote, urlencode

import openpyxl
from django.conf import settings
from django.urls import reverse
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

from glossaries.helpers import get_glossary_username
from glossaries.processor import GlossaryProcessor
from quoting.models import LanguageQuote
from django.utils.timezone import now
from subscriptions.models import UserSubscription
from subscriptions.permissions import is_user_subscription_active
from subscriptions.utils import get_user_api_key

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import django
from rest_framework.views import APIView


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

from subscriptions.models import SubscriptionType
from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url
from .helpers import get_translate_data, lowercase_file_extension, get_word_count, get_text_from_file, get_project_file, \
    rename_file

from emails.models import EmailType
from emails.send_email import send_email
from domains.models import Domain
from languages.models import Language
from users.models import User, UserGroup
from .credentials import languages
import requests
from preferences import preferences
import langdetect

from .services.post_editing import FileExpertRevisionService
from .tasks import send_statistic_request
from glossaries.models import Glossary
from typing import Optional
from django.core.files.uploadedfile import InMemoryUploadedFile
from subscriptions.permissions import SubscribedPermission
from django.core.cache import cache
from quoting.helpers import get_price_by_language_pair

import csv
from subscriptions.helpers import translation_allowed, add_translations

from quoting.services.quote import FormQuoteService

PAGINATION_PAGE_SIZE = 20
CACHE_TTL = 3600


def text_translation(request):
    """
    Text translation using LARA Translation API.

    Flow:
    1. Call /api/templates/find to get translation memory and glossary IDs (optional)
    2. Call /api/lara/translate-text with the text and optional parameters
    """
    logger = logging.getLogger(__name__)
    
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

        # Send statistics
        try:
            api_key = get_user_api_key(request.user)
            send_statistic_request(
                api_key=api_key,
                texts=[text],
                user_uuid=user_uuid,
                words_count=words_count,
                **get_translate_data(request, for_statistic=True),
            )
            logger.info(f"LARA_STATISTICS_SENT - User: {user_id} - API key found and stats sent")
        except ValueError:
            logger.warning(f"LARA_STATISTICS_FAILED - User: {user_id} - No active subscription for stats")
            # No active subscription for stats, but translation succeeded
            pass

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


def form_glossary_object(request) -> Optional[dict]:
    try:
        glossary = Glossary.objects.get(id=request.POST.get('glossary'))
        if glossary:
            return {
                "system": settings.GLOSSARY_SYSTEM,
                "username": get_glossary_username(glossary),
                "glossary_id": glossary.glossary_id,
            }
    except Glossary.DoesNotExist:
        return {}
    except ValueError:
        return {}


def file_translate(request):
    """
    Document translation using LARA Translation API (Django Lara).

    Flow:
    1. Call /api/templates/find to get translation memory and glossary IDs
    2. Call /api/lara/translate-document with the file and template parameters
    """
    logger = logging.getLogger(__name__)

    files = request.FILES.getlist('document[]', [])
    try:
        api_key = get_user_api_key(request.user)
    except ValueError:
        return JsonResponse({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)

    cache_data = cache.get(f"{request.user.uuid}")

    if cache_data:
        words_count = cache_data['words_count']
        symbols_count = cache_data['symbols_count']
        cache.delete(f"{request.user.uuid}")
    words_count = 0
    symbols_count = 0
    for file in files:
        files = request.FILES.getlist('document[]', [])
        file_name = file.name
        file = rename_file(file=file)
        file_words, file_texts = get_text_from_file(file, api_key)
        words_count += len(file_words)
        symbols_count += sum(len(word) for word in file_texts)
        file = rename_file(file=file, file_name=file_name)

    if not translation_allowed(request, words_count=words_count, files_count=len(files), symbols_count=symbols_count):
        return JsonResponse({"detail": "You are out of translation for now"}, status=status.HTTP_400_BAD_REQUEST)

    source_language = request.POST.get('source_language')
    target_language = request.POST.get('target_language')
    domain_name_raw = request.POST.get('domain_name')

    # Convert domain name from French to English if needed
    # Django Lara templates use English domain names
    domain = Domain.objects.filter(french_name=domain_name_raw).first()
    if not domain:
        domain = Domain.objects.filter(name=domain_name_raw).first()
    domain_name = domain.name if domain else domain_name_raw

    user_id = request.user.id if request.user.is_authenticated else 'anonymous'
    logger.info(f"LARA_DOC_TRANSLATE_START - User: {user_id} - Files: {len(files)} - Source: {source_language} -> Target: {target_language} - Domain: {domain_name} (raw: {domain_name_raw})")

    # Step 1: Fetch template to get translation memory and glossary IDs
    translation_memory_id = None
    glossary_id = None
    template_id = None
    template_name = None

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

        logger.info(f"LARA_DOC_TEMPLATES_RESPONSE - User: {user_id} - Status: {template_response.status_code}")

        if template_response.status_code == 200:
            templates = template_response.json()
            if templates and len(templates) > 0:
                template = templates[0]
                template_id = template.get('id')
                template_name = template.get('name')
                translation_memory_id = template.get('translationMemoryId')
                glossary_id = template.get('glossaryId')
                logger.info(f"LARA_DOC_TEMPLATE_SELECTED - User: {user_id} - Template: {template_name} (ID: {template_id}) - TM ID: {translation_memory_id} - Glossary ID: {glossary_id}")
    except requests.RequestException as e:
        logger.error(f"LARA_DOC_TEMPLATES_EXCEPTION - User: {user_id} - Exception: {str(e)}")
        # Continue without template info

    # Step 2: Translate each document via Django Lara
    projects = []
    for file in files:
        file = lowercase_file_extension(file)

        # Build form data for Django Lara
        translate_data = {
            'accessKeyId': settings.LARA_ACCESS_KEY_ID,
            'accessKeySecret': settings.LARA_ACCESS_KEY_SECRET,
            'source': source_language,
            'target': target_language,
            'userToken': str(request.user.uuid) if request.user.is_authenticated else '',
        }

        if domain_name:
            translate_data['domain'] = domain_name
        if template_id:
            translate_data['templateId'] = str(template_id)
        if template_name:
            translate_data['templateName'] = template_name
        if translation_memory_id:
            translate_data['adaptTo'] = str(translation_memory_id)
        if glossary_id:
            translate_data['glossaries'] = str(glossary_id)

        logger.info(f"LARA_DOC_TRANSLATE_CALL - User: {user_id} - File: {file.name} - adaptTo: {translation_memory_id} - glossaries: {glossary_id}")

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

    # Update translation quota
    add_translations(request, words_count=words_count,
                     files_count=len(files), symbols_count=symbols_count)

    logger.info(f"LARA_DOC_TRANSLATE_COMPLETE - User: {user_id} - Projects: {len(projects)} - Quota updated")

    return JsonResponse({
        "project_ids": [project.get('id') for project in projects if project.get('id')],
        "display_popup": False if get_price_by_language_pair(
            source_language=source_language,
            target_language=target_language) else True
    })


class GetTemplatesView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        if 'source_language' not in self.request.query_params or 'target_language' not in self.request.query_params:
            return Response({"detail": "Missing source language or target language"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user_api_key = get_user_api_key(self.request.user)
        except ValueError:
            return Response({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
        templates = requests.post(
            url=settings.CUSTOM_MT_CONSOLE_URL + "translation/get-templates",
            data={
                "source_language": self.request.query_params['source_language'].lower(),
                "target_language": self.request.query_params['target_language'].lower()
            },
            headers={
                'token': user_api_key
            }
        )
        template_names = []
        for template in templates.json():
            template_names.append(template['template_name'])

        return Response({"data": template_names}, status=status.HTTP_200_OK)


class GetDomainsView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        if 'source_language' not in self.request.query_params or 'target_language' not in self.request.query_params:
            return Response({"message": "Missing source language or target language"},
                            status=status.HTTP_400_BAD_REQUEST)
        try:
            user_api_key = get_user_api_key(self.request.user)
        except ValueError:
            return Response({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
        domains = requests.post(
            settings.CUSTOM_MT_CONSOLE_URL + "translation/get-domains",
            data={
                "source_language": self.request.query_params['source_language'].lower(),
                "target_language": self.request.query_params['target_language'].lower()
            },
            headers={
                'token': user_api_key
            }
        )
        domain_names = []
        for domain in domains.json():
            domain_names.append(domain['domain_name'])
        domains = Domain.objects.filter(
            name__in=domain_names).order_by('-featured', 'name')
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
        
        # Construire la liste avec nom et icône
        domain_data = []
        for domain in domains:
            if request.LANGUAGE_CODE == 'fr':
                domain_name = domain.french_name if domain.french_name else domain.name
            else:
                domain_name = domain.name
            
            domain_data.append({
                "name": domain_name,
                "icon": domain.icon
            })
        
        return Response({"data": domain_data, "default_domain": False}, status=status.HTTP_200_OK)


class FileExpertRevisionView(APIView):

    def get(self, request):
        project_id = request.query_params.get('project_id')
        post_editing_service = FileExpertRevisionService()
        post_editing_service.send_to_post_editing(
            request=request, project_id=project_id)
        quote_service = FormQuoteService()
        quote_service.send_quote_to_user(request)
        return HttpResponse(
            f'<h1>Sent to post-editing</h1><br/><a href="{request.build_absolute_uri(reverse("main_index"))}">Return to main page</a>')

    def post(self, request):
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        project_id = request.POST['project_id']
        post_editing_service = FileExpertRevisionService()
        post_editing_service.send_to_post_editing(
            request=request, project_id=project_id)
        quote_service = FormQuoteService()
        quote_service.send_quote_to_user(request)
        return Response({"detail": "Sent to post editing"}, status=status.HTTP_200_OK)


def get_projects_by_ids(request):
    """
    Get project status by IDs - now supports Django Lara documents.

    Calls Django Lara document-status endpoint and maps response to
    match frontend expected format.
    """
    logger = logging.getLogger(__name__)

    project_ids = request.query_params.getlist('project_id[]', [])
    responses = []

    for project_id in project_ids:
        try:
            # Call Django Lara document-status endpoint
            response = requests.get(
                f"{settings.LARA_API_URL}/api/lara/document-status/{project_id}",
                timeout=10
            )

            if response.status_code == 200:
                lara_result = response.json()

                # Map Django Lara response to frontend expected format
                # Frontend expects: id, status, source_file_name, translated_file, source_language, target_language
                res = {
                    'id': lara_result.get('id'),
                    'status': map_lara_status_to_lexa(lara_result.get('status')),
                    'source_file_name': lara_result.get('filename', ''),
                    'source_language': lara_result.get('source_language', ''),
                    'target_language': lara_result.get('target_language', ''),
                    'translated_file': lara_result.get('downloadUrl') if lara_result.get('status') == 'translated' else None,
                    'reviewed_file': None,  # LARA doesn't have post-editing yet
                    'display_popup': False if get_price_by_language_pair(
                        source_language=lara_result.get('source_language', ''),
                        target_language=lara_result.get('target_language', '')
                    ) else True
                }

                # Add error reason if status is error
                if lara_result.get('status') == 'error':
                    res['error_reason'] = lara_result.get('error_message', 'Translation failed')

                responses.append(res)
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

    Lara statuses: pending, processing, translated, error
    Lexa statuses: Being translated, Translated, Error
    """
    status_map = {
        'pending': 'Being translated',
        'processing': 'Being translated',
        'translated': 'Translated',
        'error': 'Error'
    }
    return status_map.get(lara_status, 'Being translated')


class SingleProjectView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        responses = get_projects_by_ids(request)
        return Response(responses, status=status.HTTP_200_OK)

    def delete(self, request):
        project_id = self.request.data.get('project_id')

        try:
            user_api_key = get_user_api_key(request.user)
        except ValueError:
            return Response({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
        response = requests.delete(settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                   headers={
                                       "token": user_api_key})

        return Response({"detail": "Sucessfully deleted"}, status=status.HTTP_204_NO_CONTENT)


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
                api_key = get_user_api_key(request.user)
            except ValueError:
                return JsonResponse({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
            text_for_detection, words_count, symbols_count = self.get_text_for_detection(
                api_key=api_key,
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

    def get_text_for_detection(self, file, api_key, words_count, symbols_count):
        file_name = file.name
        file = self.rename_file(file)
        formated_texts, full_text = get_text_from_file(file, api_key)
        words_count += len(formated_texts)
        symbols_count += sum(len(word) for word in full_text)
        text_for_detection = ' '.join(
            formated_texts[:self.WORDS_COUNT_FOR_DETECTION])
        file = self.rename_file(file, file_name=file_name)
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
