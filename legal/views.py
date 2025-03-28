import json
import os
import re
import time
from datetime import datetime
from decimal import Decimal
from io import BytesIO
from pprint import pprint
from urllib.parse import urlparse, unquote

from django.urls import reverse

from quoting.models import LanguageQuote
from django.utils.timezone import now

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponse
import django
from rest_framework.views import APIView
from .helpers import get_translate_data, lowercase_file_extension, get_word_count, get_text_from_file, get_project_file, \
    rename_file

from domains.models import Domain
from languages.models import Language
from users.models import User, UserGroup
from .credentials import languages
from .mail_helpers import send_expert_revision_text, \
    send_file_translation, send_text_translation
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
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
            add_translations(request, words_count=words_count, symbols_count=symbols_count)
        result = response.json()
        return JsonResponse(result)
    return JsonResponse({"detail": "You are not allowed to translate such amount of data"},
                        status=status.HTTP_400_BAD_REQUEST)


def form_glossary_object(request) -> Optional[dict]:
    try:
        glossary = Glossary.objects.get(id=request.POST.get('glossary'))
        if glossary:

            value = []
            with glossary.file.open(mode='r') as file:
                csv_reader = csv.reader(file)
                next(csv_reader, None)

                for row in csv_reader:
                    value.append(f"{row[0]}={row[1]}")

                return {
                    "file_name": glossary.file.name,
                    "value": value,
                    "adaptive": True,
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
    else:
        words_count = 0
        symbols_count = 0
        for file in files:
            files = request.FILES.getlist('document[]', [])
            file_name = file.name
            file = rename_file(file=file)
            file_texts = get_text_from_file(file, api_key)
            words_count += len(file_texts)
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
            print(response.json())
            projects.append({
                'id': response.json().get('id'),
                'file_name': file.name,
                'file_extension': os.path.splitext(file.name)[1]
            })
        print(projects)

        time.sleep(0.1)
        for project in projects:
            project_id = project.get('id')
            res = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                               headers={
                                   "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
            send_file_translation(user_id=request.user.id, source_file_url=res.json().get('source_file'),
                                  translation_name=request.POST.get('translation_name'),
                                  file_name=project['file_name'],
                                  file_ext=project['file_extension'])
        add_translations(request, words_count=words_count, files_count=len(files), symbols_count=symbols_count)
        return JsonResponse({"project_ids": [project.get('id') for project in projects],
                             "display_popup": False if get_price_by_language_pair(
                                 source_language=request.POST.get('source_language'),
                                 target_language=request.POST.get('target_language')) else True})
    return JsonResponse({"detail": "You are out of translation for now"}, status=status.HTTP_400_BAD_REQUEST)


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['translate_languages'] = self.get_languages()
        context['access_to_default_glossaries'] = self.default_glossary_allowed()
        return context

    def default_glossary_allowed(self):

        if self.request.user.is_staff:
            return True
        group = self.request.user.group
        if group:
            group_subscription = group.subscriptions.first()
            if group_subscription and group_subscription.access_to_official_glossaries:
                return True
        return False

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def post(self, request):
        if not request.user.is_staff and not request.user.group:
            return HttpResponseBadRequest({"detail": "You have to be staff or to be in group"})
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
        domains = Domain.objects.filter(name__in=domain_names).order_by('-featured', 'name')
        print(domains)
        if self.request.query_params.get('domain_group'):
            if request.LANGUAGE_CODE == 'fr':
                domains = domains.filter(domain_group__french_name=self.request.query_params.get('domain_group'))
            else:
                domains = domains.filter(domain_group__name=self.request.query_params.get('domain_group'))

        if domains.count() == 0 and preferences.DefaultTranslation.enabled:
            if request.LANGUAGE_CODE == 'fr':
                default_domain_name = preferences.DefaultTranslation.french_name if preferences.DefaultTranslation.french_name else preferences.DefaultTranslation.name
                return Response(
                    {"data": [default_domain_name], "default_domain": True},
                )
            else:
                return Response({"data": [preferences.DefaultTranslation.name], "default_domain": True}, )
        if request.LANGUAGE_CODE == 'en':
            domain_names = domains.values_list('name', flat=True)
        elif request.LANGUAGE_CODE == 'fr':
            domain_names = [domain.french_name if domain.french_name else domain.name for domain in domains]
        return Response({"data": domain_names, "default_domain": False}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def expert_revision(request):
    send_expert_revision_text(
        user_id=request.user.id,
        text=request.POST['result'],
        source_text=request.POST['source_text']
    )
    return JsonResponse({})


class FileExpertRevisionView(APIView):

    def get(self, request):
        project_id = request.query_params.get('project_id')
        post_editing_service = FileExpertRevisionService()
        post_editing_service.send_to_post_editing(request=request, project_id=project_id)
        quote_service = FormQuoteService()
        quote_service.send_quote_to_user(request)
        return HttpResponse(
            f'<h1>Sent to post-editing</h1><br/><a href="{request.build_absolute_uri(reverse("main_index"))}">Return to main page</a>')

    def post(self, request):
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        project_id = request.POST['project_id']
        post_editing_service = FileExpertRevisionService()
        post_editing_service.send_to_post_editing(request=request, project_id=project_id)
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
        headers = {"token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key}

        if page is not None:
            params["page"] = int(page)

        response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        pprint(response['results'])
        if 'results' in response:
            for project in response['results']:
                file_name = urlparse(project['source_file']).path.lstrip('/').split('/')[-1]
                original_filename = unquote(file_name)
                project['source_file_name'] = original_filename
                project['created_at'] = datetime.fromisoformat(project['created_at'].replace('Z', '+00:00'))
                project['display_popup'] = False if get_price_by_language_pair(
                    source_language=project['source_language'],
                    target_language=project['target_language']
                ) else True
                if user.is_staff:
                    try:
                        project['username'] = User.objects.get(uuid=project['user_custom_mt_token'])
                    except User.DoesNotExist:
                        project['username'] = None
                    except django.core.exceptions.ValidationError:
                        project['username'] = None
            context['projects'] = response

        return context


class SingleProjectView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def get(self, request):
        project_ids = request.query_params.getlist('project_id[]', [])
        responses = []
        for project_id in project_ids:
            print(project_id)
            response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                    headers={
                                        "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
            res = response.json()
            file_name = urlparse(response.json()['source_file']).path.lstrip('/').split('/')[-1]
            original_filename = unquote(file_name)
            res['source_file_name'] = original_filename
            res['display_popup'] = False if get_price_by_language_pair(source_language=res['source_language'],
                                                                       target_language=res['target_language']) else True

            responses.append(res)
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
            print(text_for_detection)
            if translation_allowed(request, files_count=len(files), words_count=words_count,
                                   symbols_count=symbols_count):

                try:
                    tmp_language = langdetect.detect(text_for_detection)
                    language = Language.objects.filter(abbreviation__iexact=tmp_language.upper()).values_list(
                        'abbreviation', flat=True).first()
                except langdetect.LangDetectException:
                    language = Language.objects.values_list('abbreviation', flat=True).first()
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
        formated_texts = get_text_from_file(file, api_key)
        words_count += len(formated_texts)
        symbols_count += sum(len(word) for word in formated_texts)
        text_for_detection = ' '.join(formated_texts[:self.WORDS_COUNT_FOR_DETECTION])
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
    template_name = 'profile_details.html'
