import os
import time
from urllib.parse import urlparse, unquote

from django.core.files.uploadedfile import InMemoryUploadedFile
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

    project_id = response.json().get('id')
    time.sleep(0.1)
    res = requests.get(CLOUDSTORAGE_API_URL + f"{project_id}/",
                       headers={
                           "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
    send_file_translation(user_id=request.user.id, source_file_url=res.json().get('source_file'),
                          template_name=request.POST.get('template_name'), file_name=request.FILES["document"].name,
                          file_ext=os.path.splitext(request.FILES["document"].name)[1])
    return response.json()


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['translate_languages'] = Language.objects.all()
        context['templates'] = self.get_translation_templates()
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

    def get_translation_templates(self):
        if not self.request.user.is_staff and not self.request.user.group:
            return HttpResponseBadRequest({"message": "You have to be staff or to be in group"})
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
        response = requests.post(
            CUSTOM_MT_CONSOLE_URL + "get-templates",
            data={
                "source_language": self.request.query_params['source_language'].lower(),
                "target_language": self.request.query_params['target_language'].lower()
            },
            headers={
                'token': preferences.MainSettings.api_key if self.request.user.is_staff else self.request.user.group.api_key
            }
        )
        return Response(response.json(), status=status.HTTP_200_OK)


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
        CLOUDSTORAGE_API_URL + f"{project_id}/",
        headers={
            "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
        }

    ).json()
    response = requests.post(
        CLOUDSTORAGE_API_URL + f"post_editing/{request.POST.get('project_id')}/",
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
