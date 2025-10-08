import json
import os
import re
import time
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pprint import pprint
from urllib.parse import urlparse, unquote

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

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import django
from rest_framework.views import APIView

from subscriptions.models import SubscriptionType
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
    text = request.POST.get('text')
    words_count = get_word_count(text)
    symbols_count = len(text)
    if translation_allowed(request=request, words_count=words_count, symbols_count=symbols_count):
        api_key = preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
        response = requests.post(preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "translation/translate", data={
            "text": [text],
            **get_translate_data(request)
        }, headers={
            "token": api_key})
        if response.status_code == 200:
            send_statistic_request(
                api_key=api_key, texts=[text],
                user_uuid=request.user.uuid,
                words_count=get_word_count(text),
                **get_translate_data(request, for_statistic=True),
            )
            add_translations(request, words_count=words_count,
                             symbols_count=symbols_count)
        result = response.json()
        return JsonResponse(result)
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
    api_key = preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
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
                preferences.MainSettings.CLOUDSTORAGE_API_URL,
                data=data,
                headers={
                    "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key,
                    "X-API-Key": preferences.StatisticSettings.API_KEY
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
            res = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                               headers={
                                   "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
            
            send_email(
                preferences.MainSettings.quote_cc_email,
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


class TranslateView(TemplateView):
    template_name = "translate/translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['translate_languages'] = self.get_languages()
        context['access_to_default_glossaries'] = self.default_glossary_allowed()
        context['subscription_types'] = SubscriptionType.objects.all()
        return context

    def default_glossary_allowed(self):
        if self.request.user.is_staff:
            return True

        user_subscription = self.request.user.subscriptions.first()
        if self.request.user.group:
            if user_subscription and user_subscription.access_to_official_glossaries:
                return True
        return False

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def post(self, request):
        if not request.user.is_staff and not request.user.group:
            return JsonResponse({"detail": "You have to be staff or to be in group"}, status=400)
        if request.POST.get('action') == 'text_translate':
            return text_translation(request)
        elif request.POST.get('action') == 'file_translate':
            return file_translate(request)
        return JsonResponse({})


class GetTemplatesView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        if 'source_language' not in self.request.query_params or 'target_language' not in self.request.query_params:
            return Response({"detail": "Missing source language or target language"},
                            status=status.HTTP_400_BAD_REQUEST)
        templates = requests.post(
            url=preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "translation/get-templates",
            data={
                "source_language": self.request.query_params['source_language'].lower(),
                "target_language": self.request.query_params['target_language'].lower()
            },
            headers={
                'token': preferences.MainSettings.api_key if self.request.user.is_staff else self.request.user.group.api_key
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
        domains = requests.post(
            preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "translation/get-domains",
            data={
                "source_language": self.request.query_params['source_language'].lower(),
                "target_language": self.request.query_params['target_language'].lower()
            },
            headers={
                'token': preferences.MainSettings.api_key if self.request.user.is_staff else self.request.user.group.api_key
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


class ProjectsHistoryView(TemplateView):
    template_name = 'project_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page')
        context['languages'] = languages
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        headers = {
            "token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key}

        if page is not None:
            params["page"] = int(page)

        response = requests.get(
            preferences.MainSettings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        if 'results' in response:
            for project in response['results']:
                file_name = urlparse(project['source_file']).path.lstrip(
                    '/').split('/')[-1]
                original_filename = unquote(file_name)
                project['source_file_name'] = original_filename
                project['created_at'] = datetime.fromisoformat(
                    project['created_at'].replace('Z', '+00:00'))
                project['display_popup'] = False if get_price_by_language_pair(
                    source_language=project['source_language'],
                    target_language=project['target_language']
                ) else True
                if user.is_staff:
                    try:
                        project['username'] = User.objects.get(
                            uuid=project['user_custom_mt_token'])
                    except User.DoesNotExist:
                        project['username'] = None
                    except django.core.exceptions.ValidationError:
                        project['username'] = None
            context['projects'] = response

        return context


class ProjectsHistory2View(TemplateView):
    """Nouvelle vue pour project_history_2.html avec design Builder.io"""
    template_name = 'project_history_2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page')
        context['languages'] = languages
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        headers = {
            "token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key}

        if page is not None:
            params["page"] = int(page)

        response = requests.get(
            preferences.MainSettings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        if 'results' in response:
            for project in response['results']:
                file_name = urlparse(project['source_file']).path.lstrip(
                    '/').split('/')[-1]
                original_filename = unquote(file_name)
                project['source_file_name'] = original_filename
                project['created_at'] = datetime.fromisoformat(
                    project['created_at'].replace('Z', '+00:00'))
                project['display_popup'] = False if get_price_by_language_pair(
                    source_language=project['source_language'],
                    target_language=project['target_language']
                ) else True
                
                # Mapper les statuts pour correspondre aux badges Builder.io
                status_mapping = {
                    'Translated': 'completed',
                    'Error': 'error',
                    'In progress': 'in-progress',
                    'Processing': 'in-progress',
                    'Needs attention': 'needs-attention'
                }
                project['status_mapped'] = status_mapping.get(project['status'], project['status'].lower())
                
                if user.is_staff:
                    try:
                        project['username'] = User.objects.get(
                            uuid=project['user_custom_mt_token'])
                    except User.DoesNotExist:
                        project['username'] = None
                    except django.core.exceptions.ValidationError:
                        project['username'] = None
            context['projects'] = response

        return context


def get_projects_by_ids(request):
    project_ids = request.query_params.getlist('project_id[]', [])
    responses = []
    for project_id in project_ids:
        response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={
                                    "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
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

        response = requests.delete(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                   headers={
                                       "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})

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

            api_key = preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
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


class ProfileDetailsView(TemplateView):
    template_name = 'profile_details/profile_details.html'
    
class DashboardView(TemplateView):
    template_name = "dashboard/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page', 1)
        type_filter = self.request.GET.get('type', '')
        status_filter = self.request.GET.get('status', '')
        language_filter = self.request.GET.get('language', '')
        
        # Paramètres pour l'API - limiter à 5 projets récents pour le dashboard
        params = {
            "page_size": 5,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        headers = {
            "token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key
        }

        # Ajouter les filtres au contexte pour maintenir l'état
        context['current_type_filter'] = type_filter
        context['current_status_filter'] = status_filter
        context['current_language_filter'] = language_filter

        # Récupérer les compteurs depuis la subscription de l'utilisateur
        translated_words_count = 0
        translated_symbols_count = 0
        translated_files_count = 0
        try:
            user_subscription = user.subscriptions.first()
            if user_subscription:
                translated_words_count = user_subscription.translated_words_count
                translated_symbols_count = user_subscription.translated_symbols_count
                translated_files_count = user_subscription.translated_files_count
        except Exception as e:
            # En cas d'erreur, garder la valeur par défaut
            translated_words_count = 0
            translated_symbols_count = 0
            translated_files_count = 0
        
        context['translated_words_count'] = translated_words_count
        context['translated_symbols_count'] = translated_symbols_count
        context['translated_files_count'] = translated_files_count

        # Récupérer le nombre de glossaires ajoutés par l'utilisateur
        glossaries_count = 0
        try:
            from glossaries.models import Glossary
            glossaries_count = Glossary.objects.filter(user=user).count()
        except Exception as e:
            # En cas d'erreur, garder la valeur par défaut
            glossaries_count = 0
        
        context['user_glossaries_count'] = glossaries_count

        # Déterminer si l'utilisateur est admin de groupe
        try:
            is_group_admin = False
            user_group = getattr(user, 'group', None)
            
            # L'utilisateur est admin s'il est staff, superuser ou admin de son groupe
            if user.is_staff or user.is_superuser:
                is_group_admin = True
            elif user_group:
                is_group_admin = user_group.admin.filter(id=user.id).exists()
            
            context['is_group_admin'] = is_group_admin
        except Exception:
            context['is_group_admin'] = False

        try:
            # Récupérer les projets depuis l'API
            response = requests.get(
                preferences.MainSettings.CLOUDSTORAGE_API_URL, 
                params=params, 
                headers=headers
            ).json()
            
            if 'results' in response:
                for project in response['results']:
                    # Traitement du nom de fichier
                    file_name = urlparse(project['source_file']).path.lstrip('/').split('/')[-1]
                    original_filename = unquote(file_name)
                    project['source_file_name'] = original_filename
                    
                    # Conversion de la date
                    project['created_at'] = datetime.fromisoformat(
                        project['created_at'].replace('Z', '+00:00'))
                    
                    # Utiliser le statut original sans mapping
                    project['status_mapped'] = project['status']
                    
                    # Déterminer le type de document
                    project['document_type'] = 'text' if project['source_file_name'].lower().endswith('.txt') else 'document'
                    
                    # Popup pour expert revision
                    project['display_popup'] = False if get_price_by_language_pair(
                        source_language=project['source_language'],
                        target_language=project['target_language']
                    ) else True
                
                context['projects'] = response
                
                # Récupérer le nombre total de traductions pour les statistiques
                context['total_translations'] = response.get('count', 0)
                
                # Collecter dynamiquement les statuts disponibles (statuts originaux)
                available_statuses = set()
                available_languages = set()
                for project in response['results']:
                    available_statuses.add(project['status'])
                    # Créer la paire de langues (source → target)
                    language_pair = f"{project['source_language'].upper()} → {project['target_language'].upper()}"
                    available_languages.add(language_pair)
                
                # Créer la liste des statuts disponibles (triés alphabétiquement)
                context['available_statuses'] = [
                    {'value': status, 'label': status}
                    for status in sorted(available_statuses)
                ]
                
                # Créer la liste des langues de traduction disponibles (triées alphabétiquement)
                context['available_languages'] = [
                    {'value': lang_pair, 'label': lang_pair}
                    for lang_pair in sorted(available_languages)
                ]
                
                # Informations de pagination
                current_page = int(page)
                total_pages = (response.get('count', 0) + 4) // 5  # Arrondir vers le haut
                
                # Calculer la plage de pages à afficher
                page_range = []
                if total_pages <= 5:
                    page_range = list(range(1, total_pages + 1))
                else:
                    if current_page <= 3:
                        page_range = list(range(1, 6))
                    elif current_page >= total_pages - 2:
                        page_range = list(range(total_pages - 4, total_pages + 1))
                    else:
                        page_range = list(range(current_page - 2, current_page + 3))
                
                context['paginator'] = {
                    'current_page': current_page,
                    'total_pages': total_pages,
                    'has_previous': response.get('previous') is not None,
                    'has_next': response.get('next') is not None,
                    'previous_page_number': current_page - 1 if current_page > 1 else None,
                    'next_page_number': current_page + 1 if response.get('next') else None,
                    'count': response.get('count', 0),
                    'start_index': (current_page - 1) * 5 + 1,
                    'end_index': min(current_page * 5, response.get('count', 0)),
                    'has_multiple_pages': response.get('count', 0) > 5,
                    'page_range': page_range
                }
            else:
                context['projects'] = {'results': [], 'count': 0}
                context['total_translations'] = 0
                context['paginator'] = {
                    'current_page': 1,
                    'total_pages': 1,
                    'has_previous': False,
                    'has_next': False,
                    'has_multiple_pages': False,
                    'count': 0,
                    'page_range': [1]
                }
        except Exception as e:
            # En cas d'erreur, retourner des données vides
            context['projects'] = {'results': [], 'count': 0}
            context['total_translations'] = 0
            context['paginator'] = {
                'current_page': 1,
                'total_pages': 1,
                'has_previous': False,
                'has_next': False,
                'has_multiple_pages': False,
                'count': 0,
                'page_range': [1]
            }
        
        return context


class TextTranslate2View(TemplateView):
    template_name = "translate_2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add context variables here if needed
        return context


class DocumentTranslate2View(TemplateView):
    template_name = "translate/document_translate/document_translate_2.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['translate_languages'] = self.get_languages()
        context['access_to_default_glossaries'] = self.default_glossary_allowed()
        context['subscription_types'] = SubscriptionType.objects.all()
        return context

    def default_glossary_allowed(self):
        if self.request.user.is_staff:
            return True

        user_subscription = self.request.user.subscriptions.first()
        if self.request.user.group:
            if user_subscription and user_subscription.access_to_official_glossaries:
                return True
        return False

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()


class DisplayMessage(TemplateView):
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
            'svg': '<svg class="w-6 h-6 text-white" fill="currentColor" viewBox="0 0 24 24"><path d="M20.25 4.5H16.5V3.75C16.5 3.15326 16.2629 2.58097 15.841 2.15901C15.419 1.73705 14.8467 1.5 14.25 1.5H9.75C9.15326 1.5 8.58097 1.73705 8.15901 2.15901C7.73705 2.58097 7.5 3.15326 7.5 3.75V4.5H3.75C3.55109 4.5 3.36032 4.57902 3.21967 4.71967C3.07902 4.86032 3 5.05109 3 5.25C3 5.44891 3.07902 5.63968 3.21967 5.78033C3.36032 5.92098 3.55109 6 3.75 6H4.5V19.5C4.5 19.8978 4.65804 20.2794 4.93934 20.5607C5.22064 20.842 5.60218 21 6 21H18C18.3978 21 18.7794 20.842 19.0607 20.5607C19.342 20.2794 19.5 19.8978 19.5 19.5V6H20.25C20.4489 6 20.6397 5.92098 20.7803 5.78033C20.921 5.63968 21 5.44891 21 5.25C21 5.05109 20.921 4.86032 20.7803 4.71967C20.6397 4.57902 20.4489 4.5 20.25 4.5ZM9 3.75C9 3.55109 9.07902 3.36032 9.21967 3.21967C9.36032 3.07902 9.55109 3 9.75 3H14.25C14.4489 3 14.6397 3.07902 14.7803 3.21967C14.921 3.36032 15 3.55109 15 3.75V4.5H9V3.75ZM18 19.5H6V6H18V19.5ZM10.5 9.75V15.75C10.5 15.9489 10.421 16.1397 10.2803 16.2803C10.1397 16.421 9.94891 16.5 9.75 16.5C9.55109 16.5 9.36032 16.421 9.21967 16.2803C9.07902 16.1397 9 15.9489 9 15.75V9.75C9 9.55109 9.07902 9.36032 9.21967 9.21967C9.36032 9.07902 9.55109 9 9.75 9C9.94891 9 10.1397 9.07902 10.2803 9.21967C10.421 9.36032 10.5 9.55109 10.5 9.75ZM15 9.75V15.75C15 15.9489 14.921 16.1397 14.7803 16.2803C14.6397 16.421 14.4489 16.5 14.25 16.5C14.0511 16.5 13.8603 16.421 13.7197 16.2803C13.579 16.1397 13.5 15.9489 13.5 15.75V9.75C13.5 9.55109 13.579 9.36032 13.7197 9.21967C13.8603 9.07902 14.0511 9 14.25 9C14.4489 9 14.6397 9.07902 14.7803 9.21967C14.921 9.36032 15 9.55109 15 9.75Z"/></svg>',
            'bg_color': '#EF4444',
            'border_color': '#FCA5A5'
        },
        'X': {
            'svg': '<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path></svg>',
            'bg_color': '#6B7280',
            'border_color': '#D1D5DB'
        },
        'SAVE': {
            'svg': '<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4"></path></svg>',
            'bg_color': '#10B981',
            'border_color': '#86EFAC'
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


class MyTeamView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    """
    Team management view for administrators.
    Only group administrators can access this view.
    """
    template_name = 'my_team/my_team.html'
    
    def test_func(self):
        """Check if user is an admin of any group"""
        print(f"\n=== MY TEAM ACCESS CHECK ===")
        print(f"User: {self.request.user.username} (ID: {self.request.user.id})")
        print(f"Is staff: {self.request.user.is_staff}")
        
        # Check if user is staff or is admin of their group
        if self.request.user.is_staff:
            print(f"Access granted: User is staff")
            return True
        
        # Check if user is admin of their group
        user_group = getattr(self.request.user, 'group', None)
        print(f"User group: {user_group}")
        
        if user_group:
            is_admin = user_group.admin.filter(id=self.request.user.id).exists()
            print(f"Is admin of group '{user_group.name}': {is_admin}")
            if is_admin:
                print(f"Access granted: User is admin of their group")
            else:
                print(f"Access denied: User is not admin of their group")
            return is_admin
        
        print(f"Access denied: User has no group")
        print(f"=== END ACCESS CHECK ===\n")
        return False
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get team members based on user's group membership
        team_members, paginator_info = self.get_team_members()
        
        # Calculate stats on the full dataset
        stats = self.get_team_stats()
        
        # Get group name
        if self.request.user.is_staff:
            group_name = "All Users"
        else:
            user_group = getattr(self.request.user, 'group', None)
            group_name = user_group.name if user_group else "No Group"
        
        context.update({
            'team_members': team_members,
            'stats': stats,
            'paginator': paginator_info,
            'group_name': group_name,
        })
        
        return context
    
    def get_team_members(self):
        """Get all team members sorted by creation date (newest first)"""
        # Debug: Print current user info
        print(f"\n=== MY TEAM DEBUG ===")
        print(f"Current user: {self.request.user.username} (ID: {self.request.user.id})")
        print(f"Is staff: {self.request.user.is_staff}")
        print(f"Is superuser: {self.request.user.is_superuser}")
        
        # If user is staff, show all users; otherwise show group members
        if self.request.user.is_staff:
            print(f"User is staff - showing ALL users")
            queryset = User.objects.all()
        else:
            # Get users from the same group
            user_group = getattr(self.request.user, 'group', None)
            print(f"User group attribute: {user_group}")
            
            if user_group:
                print(f"User group found: {user_group.name} (ID: {user_group.id})")
                queryset = User.objects.filter(group=user_group)
                print(f"Number of users in this group: {queryset.count()}")
            else:
                print(f"No group found for user - showing NO users")
                queryset = User.objects.none()
        
        # Sort by date_joined descending (newest first)
        queryset = queryset.select_related('group').order_by('-date_joined')
        
        # Debug: Print all users that will be displayed
        print(f"\nUsers to display ({queryset.count()} total):")
        for user in queryset[:5]:  # Show first 5 users
            user_group_name = user.group.name if hasattr(user, 'group') and user.group else 'No group'
            print(f"  - {user.username} ({user.email}) - Group: {user_group_name}")
        if queryset.count() > 5:
            print(f"  ... and {queryset.count() - 5} more users")
        print(f"=== END DEBUG ===\n")
        
        # Add computed fields for each member
        members_with_data = []
        for user in queryset:
            member_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name or 'Unknown',
                'last_name': user.last_name or 'User',
                'email': user.email,
                'initials': self.get_user_initials(user),
                'is_admin': self.check_admin_status(user),
                'is_buyer': self.check_buyer_status(user),
                'is_premium': self.check_premium_status(user),
                'date_joined': user.date_joined,
                'license': self.get_user_license(user),
            }
            members_with_data.append(member_data)
        
        # Return empty paginator info since pagination is removed
        paginator_info = {
            'current_page': 1,
            'total_pages': 1,
            'has_previous': False,
            'has_next': False,
            'previous_page_number': None,
            'next_page_number': None,
            'page_range': [1],
            'has_multiple_pages': False,
        }
        
        return members_with_data, paginator_info
    
    def get_team_stats(self):
        """Calculate team statistics from the full dataset"""
        # Get the same queryset used for team members, but without pagination
        if self.request.user.is_staff:
            queryset = User.objects.all()
        else:
            # Get users from the same group
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                queryset = User.objects.filter(group=user_group)
            else:
                queryset = User.objects.none()
        
        # Calculate statistics on the full queryset
        total_users = queryset.count()
        
        # Count admin users
        admin_users = 0
        premium_users = 0
        
        for user in queryset:
            if self.check_admin_status(user):
                admin_users += 1
            if self.check_premium_status(user):
                premium_users += 1
        
        return {
            'total_users': total_users,
            'admin_users': admin_users,
            'premium_users': premium_users,
        }
    
    def get_user_initials(self, user):
        """Generate user initials from first and last name"""
        first_initial = user.first_name[0].upper() if user.first_name else 'U'
        last_initial = user.last_name[0].upper() if user.last_name else 'U'
        return f"{first_initial}{last_initial}"
    
    def check_admin_status(self, user):
        """Check if user is admin of their group"""
        if user.is_staff or user.is_superuser:
            return True
        
        user_group = getattr(user, 'group', None)
        if user_group:
            return user_group.admin.filter(id=user.id).exists()
        
        return False
    
    def check_premium_status(self, user):
        """Check if user has premium subscription"""
        # This would be replaced with actual subscription logic
        # For now, we'll consider staff users as premium
        return user.is_staff or hasattr(user, 'subscription') and getattr(user.subscription, 'is_premium', False)
    
    def check_buyer_status(self, user):
        """Check if user has a Stripe customer ID"""
        return bool(user.stripe_customer_id)
    
    def get_user_license(self, user):
        """Get user's active license/subscription"""
        # Get all subscriptions for this user
        all_subscriptions = UserSubscription.objects.filter(user=user)
        
        # Filter active subscriptions
        active_subscriptions = []
        current_time = now()
        
        for sub in all_subscriptions:
            # Check if subscription status is active
            if is_user_subscription_active(sub.status):
                # Check if subscription is within date range
                if current_time >= sub.start_date and current_time <= sub.end_date:
                    active_subscriptions.append(sub)
        
        # Return appropriate value based on number of active subscriptions
        if len(active_subscriptions) == 0:
            return {
                'status': 'no_subscription',
                'name': 'No subscription'
            }
        elif len(active_subscriptions) == 1:
            return {
                'status': 'active',
                'name': active_subscriptions[0].subscription.name
            }
        else:
            return {
                'status': 'error',
                'name': 'Error: Multiple subscriptions'
            }
