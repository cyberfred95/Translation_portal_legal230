import base64
import json
import os
import re
import time
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


def translate_via_delta_docx(delta, api_key, request, plain_text, words_count, symbols_count):
    """
    Translate text using Delta JSON -> DOCX -> Translation -> HTML conversion.
    This method preserves formatting including colors, lists, bold, italic, underline.
    """
    import uuid
    from docx import Document
    from docx.shared import RGBColor
    from docx import Document as DocxDocument

    doc = Document()
    para = doc.add_paragraph()

    # Convert Delta to DOCX
    for op in delta.get('ops', []):
        text_insert = op.get('insert', '')
        attrs = op.get('attributes', {})

        if not text_insert:
            continue

        # Handle newlines
        if '\n' in text_insert:
            parts = text_insert.split('\n')
            for i, part in enumerate(parts):
                if part:  # Add text to current paragraph
                    run = para.add_run(part)
                    # Apply text formatting (bold, italic, underline, color)
                    if attrs.get('bold'):
                        run.bold = True
                    if attrs.get('italic'):
                        run.italic = True
                    if attrs.get('underline'):
                        run.underline = True
                    if 'color' in attrs:
                        color_hex = attrs['color'].lstrip('#')
                        if len(color_hex) == 6:
                            r = int(color_hex[0:2], 16)
                            g = int(color_hex[2:4], 16)
                            b = int(color_hex[4:6], 16)
                            run.font.color.rgb = RGBColor(r, g, b)

                # Create new paragraph for each newline (except the last one)
                if i < len(parts) - 1:
                    # Check if this is a list item
                    list_type = attrs.get('list')
                    if list_type == 'bullet':
                        para = doc.add_paragraph(style='List Bullet')
                    elif list_type == 'ordered':
                        para = doc.add_paragraph(style='List Number')
                    else:
                        para = doc.add_paragraph()
        else:
            # No newlines - just add the text to current paragraph
            run = para.add_run(text_insert)
            # Apply text formatting
            if attrs.get('bold'):
                run.bold = True
            if attrs.get('italic'):
                run.italic = True
            if attrs.get('underline'):
                run.underline = True
            if 'color' in attrs:
                color_hex = attrs['color'].lstrip('#')
                if len(color_hex) == 6:
                    r = int(color_hex[0:2], 16)
                    g = int(color_hex[2:4], 16)
                    b = int(color_hex[4:6], 16)
                    run.font.color.rgb = RGBColor(r, g, b)

    # Save to temporary file
    temp_filename = f"text_translation_{uuid.uuid4().hex}.docx"
    temp_path = os.path.join(settings.MEDIA_ROOT, 'docx', temp_filename)
    doc.save(temp_path)

    # Indique si la traduction s'est terminée avec succès.
    # En cas d'erreur, on conserve le fichier temporaire pour analyse.
    success = False

    try:
        # Read the file and create InMemoryUploadedFile
        with open(temp_path, 'rb') as f:
            file_content = f.read()

        file = InMemoryUploadedFile(
            BytesIO(file_content),
            None,
            temp_filename,
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            len(file_content),
            None
        )

        # Submit for translation
        data = {
            "user_custom_mt_token": request.user.uuid,
            **get_translate_data(request),
            "glossary": json.dumps(form_glossary_object(request))
        }

        response = requests.post(
            settings.CLOUDSTORAGE_API_URL,
            data=data,
            headers={
                "token": api_key,
                "X-API-Key": settings.STATS_API_KEY
            },
            files={
                'source_file': file
            }
        )

        if response.status_code != 200:
            return JsonResponse({"detail": "Translation submission failed"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        project_id = response.json().get('id')

        # Poll for translation completion (max 120 seconds for long texts)
        max_attempts = 60
        attempt = 0
        translated_file_url = None

        while attempt < max_attempts:
            time.sleep(2)
            status_response = requests.get(
                settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                headers={"token": api_key}
            )

            if status_response.status_code == 200:
                project_data = status_response.json()
                if project_data.get('status') == 'Translated':
                    translated_file_url = project_data.get('translated_file')
                    break
                elif project_data.get('status') == 'Error':
                    # Exposer les détails de l'erreur renvoyée par le service de traduction
                    error_info = project_data.get('error') or project_data
                    return JsonResponse(
                        {
                            "detail": "Translation failed",
                            "translation_error": error_info,
                        },
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            attempt += 1

        if not translated_file_url:
            return JsonResponse({"detail": "Translation timeout"}, status=status.HTTP_408_REQUEST_TIMEOUT)

        # Download translated DOCX
        translated_response = requests.get(translated_file_url)
        if translated_response.status_code != 200:
            return JsonResponse({"detail": "Failed to download translated file"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Convert translated DOCX to HTML preserving colors and lists
        translated_doc = DocxDocument(BytesIO(translated_response.content))
        html_parts = []
        current_list_type = None
        list_items = []

        for para in translated_doc.paragraphs:
            para_html = []

            # Check if this is a list item
            style_name_lower = para.style.name.lower()
            is_bullet_list = 'bullet' in style_name_lower or para.style.name == 'List Bullet'
            is_number_list = 'number' in style_name_lower or para.style.name == 'List Number'
            is_list = is_bullet_list or is_number_list

            # Build the content with formatting
            for run in para.runs:
                text_content = run.text
                if not text_content:
                    continue

                # Build style attributes
                styles = []
                if run.bold:
                    styles.append("font-weight: bold")
                if run.italic:
                    styles.append("font-style: italic")
                if run.underline:
                    styles.append("text-decoration: underline")

                # Preserve color
                if run.font.color and run.font.color.rgb:
                    rgb = run.font.color.rgb
                    r, g, b = rgb[0], rgb[1], rgb[2]
                    styles.append(f"color: rgb({r}, {g}, {b})")

                style_attr = f' style="{"; ".join(styles)}"' if styles else ''
                para_html.append(f'<span{style_attr}>{text_content}</span>')

            content = "".join(para_html)

            # Handle list items - Quill uses <ol> for both bullets and numbered lists
            if is_list:
                data_list_attr = 'bullet' if is_bullet_list else 'ordered'

                # Starting a new list or continuing same list type
                if current_list_type != data_list_attr:
                    # Close previous list if exists
                    if current_list_type:
                        html_parts.append(f'<ol>{"".join(list_items)}</ol>')
                        list_items = []
                    current_list_type = data_list_attr

                # Add item to current list with Quill's data-list attribute
                list_items.append(f'<li data-list="{data_list_attr}">{content}</li>')
            else:
                # Close any open list
                if current_list_type:
                    html_parts.append(f'<ol>{"".join(list_items)}</ol>')
                    list_items = []
                    current_list_type = None

                # Regular paragraph
                html_parts.append(f'<p>{content}</p>')

        # Close final list if still open
        if current_list_type:
            html_parts.append(f'<ol>{"".join(list_items)}</ol>')

        translated_html = "".join(html_parts)

        # Send statistics
        send_statistic_request(
            api_key=api_key, texts=[plain_text],
            user_uuid=request.user.uuid,
            words_count=words_count,
            **get_translate_data(request, for_statistic=True),
        )
        add_translations(request, words_count=words_count, symbols_count=symbols_count)

        success = True
        return JsonResponse({"translated_text": [translated_html]})

    finally:
        # Clean up temporary file uniquement si la traduction a réussi
        if success and os.path.exists(temp_path):
            os.remove(temp_path)


def translate_via_text_api(html_text, api_key, request, plain_text, words_count, symbols_count):
    """
    Translate text using the original direct text translation API.
    This is the old method that sends HTML directly to the translation API without DOCX conversion.
    Used for PASDOC tests or single-paragraph texts.
    """
    # Call the original text translation API directly
    response = requests.post(
        settings.CUSTOM_MT_CONSOLE_URL + "translation/translate",
        data={
            "text": [html_text],
            **get_translate_data(request)
        },
        headers={"token": api_key}
    )

    # Check if the request was successful
    if response.status_code != 200:
        return JsonResponse(
            {"detail": f"Translation API error: {response.status_code}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    result = response.json()

    # Check if the response contains an error
    if 'error' in result:
        error_message = result.get('error', 'Unknown error from translation API')
        return JsonResponse(
            {"detail": f"Translation error: {error_message}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    # Success - send statistics
    send_statistic_request(
        api_key=api_key,
        texts=[plain_text],
        user_uuid=request.user.uuid,
        words_count=words_count,
        **get_translate_data(request, for_statistic=True),
    )
    add_translations(request, words_count=words_count, symbols_count=symbols_count)

    return JsonResponse(result)


def text_translation(request):
    text_input = request.POST.get('text')  # Can be Delta JSON (from Quill) or plain text/HTML (from API)

    import json

    # Try to parse as Delta JSON, fallback to plain text/HTML for API compatibility
    delta = None
    is_delta_format = False

    try:
        parsed = json.loads(text_input)
        # Check if it's a valid Delta format (must have 'ops' key with a list)
        if isinstance(parsed, dict) and 'ops' in parsed and isinstance(parsed.get('ops'), list):
            delta = parsed
            is_delta_format = True
            # Get plain text from Delta for word count
            plain_text = ''.join([op.get('insert', '') for op in delta.get('ops', [])])
        else:
            # It's JSON but not Delta format, treat as plain text
            plain_text = text_input
    except (json.JSONDecodeError, TypeError):
        # Not JSON, treat as plain text or HTML (API compatibility)
        plain_text = text_input if text_input else ''

    words_count = get_word_count(plain_text)
    symbols_count = len(plain_text)

    if translation_allowed(request=request, words_count=words_count, symbols_count=symbols_count):
        try:
            api_key = get_user_api_key(request.user)
        except ValueError:
            return JsonResponse({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)

        # If not Delta format, always use the old text API method (for API compatibility)
        if not is_delta_format:
            html_text = request.POST.get('html_content', '') or text_input
            return translate_via_text_api(html_text, api_key, request, plain_text, words_count, symbols_count)

        # For Delta format: check if we should use the new Delta->DOCX method or the old text API method
        # Use old method if: text starts with "PASDOC" OR text has only one paragraph
        starts_with_pasdoc = plain_text.strip().upper().startswith('PASDOC')
        paragraph_count = plain_text.count('\n')
        use_old_method = starts_with_pasdoc or paragraph_count <= 1

        if use_old_method:
            # Use HTML sent from frontend (Quill's root.innerHTML)
            html_text = request.POST.get('html_content', '')
            return translate_via_text_api(html_text, api_key, request, plain_text, words_count, symbols_count)
        else:
            # Use new Delta->DOCX method
            return translate_via_delta_docx(delta, api_key, request, plain_text, words_count, symbols_count)
    
    return JsonResponse({"detail": "You are not allowed to translate such amount of data"},
                        status=status.HTTP_400_BAD_REQUEST)


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

    if translation_allowed(request, words_count=words_count, files_count=len(files), symbols_count=symbols_count):
        data = {
            "user_custom_mt_token": request.user.uuid,
            **get_translate_data(request),
            "glossary": json.dumps(form_glossary_object(request))
        }
        projects = []
        for file in files:
            file = lowercase_file_extension(file)
            response = requests.post(
                settings.CLOUDSTORAGE_API_URL,
                data=data,
                headers={
                    "token": api_key,
                    "X-API-Key": settings.STATS_API_KEY
                },
                files={
                    'source_file': file
                }
            )
            projects.append({
                'id': response.json().get('id'),
                'file_name': file.name,
                'file_extension': os.path.splitext(file.name)[1]
            })
        time.sleep(0.1)
        for project in projects:
            project_id = project.get('id')
            res = requests.get(settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                               headers={
                                   "token": api_key})
            
            send_email(
                settings.QUOTE_CC_EMAIL,
                EmailType.USER_ADM_TR_FILE,
                'fr',
                {
                    "lexa_username": 'admin',
                    "lexa_sender_email": request.user.email if request.user.email else '(no email)',
                    "url_source_file": res.json().get('source_file'),
                    "translation_name": project['file_name'],
                    "file_ext": project['file_extension']
                }
            )
            
        add_translations(request, words_count=words_count,
                         files_count=len(files), symbols_count=symbols_count)
        return JsonResponse({"project_ids": [project.get('id') for project in projects],
                            "display_popup": False if get_price_by_language_pair(
            source_language=request.POST.get(
                'source_language'),
            target_language=request.POST.get('target_language')) else True})
    return JsonResponse({"detail": "You are out of translation for now"}, status=status.HTTP_400_BAD_REQUEST)


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
    project_ids = request.query_params.getlist('project_id[]', [])
    responses = []
    try:
        user_api_key = get_user_api_key(request.user)
    except ValueError:
        return Response({"detail": "No active subscription found"}, status=status.HTTP_403_FORBIDDEN)
    for project_id in project_ids:
        response = requests.get(settings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={
                                    "token": user_api_key})
        res = response.json()
        file_name = urlparse(response.json()['source_file']).path.lstrip(
            '/').split('/')[-1]
        original_filename = unquote(file_name)
        res['source_file_name'] = original_filename
        res['display_popup'] = False if get_price_by_language_pair(source_language=res['source_language'],
                                                                   target_language=res['target_language']) else True

        responses.append(res)
    return responses


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
