import json
import os
from pprint import pprint
from urllib.parse import urlparse, unquote
from rest_framework.response import Response
from rest_framework import status
from django.views.generic import TemplateView, View, DetailView, ListView
from django.http import JsonResponse, HttpResponseBadRequest, Http404, HttpResponseNotFound, FileResponse, HttpResponse
import django
from rest_framework.views import APIView

from languages.models import Language
from users.models import User
from .credentials import languages
from .keys import CUSTOM_MT_CONSOLE_URL, CLOUDSTORAGE_API_URL
from .mail_helpers import send_expert_revision_text, \
    send_expert_revision_file, send_file_translation, send_text_translation
import base64
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import requests
from preferences import preferences
from gpt_processing.prompts_list import prompts_list

PAGINATION_PAGE_SIZE = 30


def text_translation(request):
    text = request.POST.get('text')
    response = requests.post(CUSTOM_MT_CONSOLE_URL + "translate", data={
        "text": [text],
        "template_name": request.POST.get('template_name')
    }, headers={
        "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
    send_text_translation(user_id=request.user.id, text=text, template_name=request.POST.get('template_name'))
    return response.json()


def file_translate(request):
    response = requests.post(
        url=CLOUDSTORAGE_API_URL,
        data={
            "template_name": request.POST.get('template_name'),
            "user_custom_mt_token": request.user.uuid,
            "source_language": request.POST.get('source_language')
        },
        headers={
            "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key},
        files={
            'source_file': request.FILES["document"]
        }
    )
    file = request.FILES['document'].read()
    b_64 = base64.b64encode(file)
    send_file_translation(user_id=request.user.id, base64_attachment=b_64.decode(encoding='utf-8'),
                          file_name=request.FILES['document'].name, template_name=request.POST.get('template_name'),
                          format=os.path.splitext(str(request.FILES['document']))[1])
    return response.json()


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['templates'] = self.get_translation_templates()
        context['prompts'] = self.get_prompts()
        return context

    def get_prompts(self):
        prompts = []
        for prompt in prompts_list:
            prompts.append({"slug":prompt['slug'], "name":prompt['name']})

        return prompts

    def get_translation_templates(self):
        templates = dict()
        response = requests.post(
            CUSTOM_MT_CONSOLE_URL + "get-templates",
            data={
                "source_language": "en",
                "target_language": "fr"
            },
            headers={
                "token": preferences.MainSettings.api_key if self.request.user.is_staff else self.request.user.group.api_key})
        templates['en_fr'] = response.json()

        response = requests.post(
            CUSTOM_MT_CONSOLE_URL + "get-templates",
            data={
                "source_language": "fr",
                "target_language": "en"
            },
            headers={
                'token': preferences.MainSettings.api_key if self.request.user.is_staff else self.request.user.group.api_key
            })

        templates['fr_en'] = response.json()
        return templates

    def post(self, request):

        if request.POST.get('action') == 'text_translate':
            return JsonResponse(text_translation(request))
        elif request.POST.get('action') == 'file_translate':
            return JsonResponse(file_translate(request))
        return JsonResponse({})


@csrf_exempt
@api_view(['POST'])
def expert_revision(request):
    text = request.POST['result']
    send_expert_revision_text(user_id=request.user.id, text=text)
    return JsonResponse({})


@csrf_exempt
@api_view(['POST'])
def expert_revision_file(request):
    file_url = request.POST.get('file_url')
    send_expert_revision_file(user_id=request.user.id, file_url=file_url)
    return JsonResponse({})


class ProjectsHistoryView(TemplateView):
    template_name = 'project_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        page = self.request.GET.get('page')
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "page": page,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        headers = {"token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key}

        if page is not None:
            params["page"] = int(page)

        response = requests.get(CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
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
        project_id = request.query_params.get('project_id')
        response = requests.get(CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={
                                    "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
        return Response(response.json(), status=status.HTTP_200_OK)

    def delete(self, request):
        project_id = self.request.data.get('project_id')
        response = requests.delete(CLOUDSTORAGE_API_URL + f"{project_id}/",
                                   headers={
                                       "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})

        return Response({"message": "Sucessfully deleted"}, status=status.HTTP_204_NO_CONTENT)
