import os
import time
from urllib.parse import urlparse, unquote

from django.core.files.uploadedfile import InMemoryUploadedFile
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView
from django.http import JsonResponse, HttpResponseBadRequest
import django
from rest_framework.views import APIView
from .helpers import get_translate_data

from domains.models import Domain
from languages.models import Language
from users.models import User
from .credentials import languages
from .mail_helpers import send_expert_revision_text, \
    send_file_translation, send_text_translation
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import requests
from preferences import preferences
from gpt_processing.prompts_list import prompts_list
from stats.calculator import StatsProcessor
import langdetect
from stats.views import PORTAL_STATISTIC_URL

PAGINATION_PAGE_SIZE = 30
PORTAL_API_KEY = ""


def text_translation(request):
    text = request.POST.get('text')
    response = requests.post(preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "translate", data={
        "text": [text],
        **get_translate_data(request),
    }, headers={
        "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
    send_text_translation(user_id=request.user.id, text=text, translation_name=request.POST.get('translation_name'))
    StatsProcessor.send_request(texts=[text], request=request)
    return response.json()


def file_translate(request):
    data = {**get_translate_data(request),
            "user_custom_mt_token": request.user.uuid,
            "source_language": request.POST.get('source_language')}
    projects = []
    files = request.FILES.getlist('document[]', [])
    for file in files:
        response = requests.post(
            preferences.MainSettings.CLOUDSTORAGE_API_URL,
            data=data,
            headers={
                "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key},
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
        send_file_translation(user_id=request.user.id, source_file_url=res.json().get('source_file'),
                              translation_name=request.POST.get('translation_name'),
                              file_name=project['file_name'],
                              file_ext=project['file_extension'])
    # StatsProcessor().calculate_statistics(files=files, user=request.user)
    return {"project_ids": [project.get('id') for project in projects]}


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['translate_languages'] = Language.objects.all()
        context['prompts'] = self.get_prompts()
        return context

    def get_prompts(self):
        user_prompts = {}
        for prompts in prompts_list:
            language_prompts = []
            for prompt in prompts_list[prompts]:
                language_prompts.append(
                    {"slug": prompt['slug'], "description": prompt['description'], "name": prompt['name']})
            user_prompts[prompts] = language_prompts
        return user_prompts

    def post(self, request):
        if not request.user.is_staff and not request.user.group:
            return HttpResponseBadRequest({"message": "You have to be staff or to be in group"})
        if request.POST.get('action') == 'text_translate':
            return JsonResponse(text_translation(request))
        elif request.POST.get('action') == 'file_translate':
            return JsonResponse(file_translate(request))
        return JsonResponse({})


class GetTemplatesView(APIView):

    def get(self, request):
        if not request.user.is_staff and not request.user.group:
            return Response({"message": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        if 'source_language' not in self.request.query_params or 'target_language' not in self.request.query_params:
            return Response({"message": "Missing source language or target language"},
                            status=status.HTTP_400_BAD_REQUEST)
        templates = requests.post(
            url=preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "get-templates",
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

    def get(self, request):
        if 'source_language' not in self.request.query_params or 'target_language' not in self.request.query_params:
            return Response({"message": "Missing source language or target language"},
                            status=status.HTTP_400_BAD_REQUEST)
        domains = requests.post(
            preferences.MainSettings.CUSTOM_MT_CONSOLE_URL + "get-domains",
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
        domains = Domain.objects.filter(name__in=domain_names)

        if request.LANGUAGE_CODE == 'en':
            domain_names = domains.values_list('name', flat=True)
        elif request.LANGUAGE_CODE == 'fr':
            domain_names = [domain.french_name if domain.french_name else domain.name for domain in domains]
        return Response({"data": domain_names}, status=status.HTTP_200_OK)


@csrf_exempt
@api_view(['POST'])
def expert_revision(request):
    send_expert_revision_text(
        user_id=request.user.id,
        text=request.POST['result'],
        source_text=request.POST['source_text']
    )
    return JsonResponse({})


@csrf_exempt
@api_view(['POST'])
def expert_revision_file(request):
    if not request.user.is_staff and not request.user.group:
        return Response({"message": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
    project_id = request.POST['project_id']
    project = requests.get(
        preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
        headers={
            "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
        }

    ).json()
    response = requests.post(
        preferences.MainSettings.CLOUDSTORAGE_API_URL + f"post_editing/{request.POST.get('project_id')}/",
        headers={
            "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key},
        data={"email": preferences.MainSettings.sender_email})
    return Response({"message": "Sent to post editing"}, status=status.HTTP_200_OK)


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
        if 'results' in response:
            for project in response['results']:
                file_name = urlparse(project['source_file']).path.lstrip('/').split('/')[-1]
                original_filename = unquote(file_name)
                project['source_file_name'] = original_filename
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

            responses.append(res)
        return Response(responses, status=status.HTTP_200_OK)

    def delete(self, request):
        project_id = self.request.data.get('project_id')

        response = requests.delete(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                   headers={
                                       "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})

        return Response({"message": "Sucessfully deleted"}, status=status.HTTP_204_NO_CONTENT)


class LanguageDetectView(APIView):

    def get(self, request):
        files = request.FILES.getlist('document[]', [])
        result = {}
        for file in files:
            text = StatsProcessor().get_texts(file=file)['texts'][0]['text']
            tmp_language = langdetect.detect(text)
            language = Language.objects.filter(abbreviation__iexact=tmp_language).first()
            result[f'{file.name}'] = language.french_name if request.LANGUAGE_CODE != 'fr' else language.name
        return JsonResponse({'languages': result}, status=status.HTTP_200_OK)
