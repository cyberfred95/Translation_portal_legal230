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
    send_expert_revision_file
import base64
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
import requests
from preferences import preferences

PAGINATION_PAGE_SIZE = 30


def text_translation(request):
    text = request.POST.get('text')
    response = requests.post(CUSTOM_MT_CONSOLE_URL + "translate", data={
        "text": [text],
        "template_name": request.POST.get('template_name')
    }, headers={
            "token": preferences.MainSettings.custom_MT_api_key if request.user.is_staff else request.user.group.api_key})
    return response.json()


def file_translate(request):
    response = requests.post(
        url=CLOUDSTORAGE_API_URL,
        data={
            "template_name": request.POST.get('template_name'),
            "user_uuid": request.user.uuid
        },
        headers={
            "token": preferences.MainSettings.custom_MT_api_key if request.user.is_staff else request.user.group.api_key},
        files={
            'source_file': request.FILES["document"]
        }
    )

    return response.json()


class TranslateView(TemplateView):
    template_name = "translate.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['languages'] = languages
        context['templates'] = self.get_translation_templates()
        return context

    def get_translation_templates(self):
        templates = dict()
        response = requests.post(
            CUSTOM_MT_CONSOLE_URL + "get-templates",
            data={
                "source_language": "en",
                "target_language": "fr"
            },
            headers={
                "token": preferences.MainSettings.custom_MT_api_key if self.request.user.is_staff else self.request.user.group.api_key})
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
    file = request.FILES['file'].read()
    b_64 = base64.b64encode(file)
    send_expert_revision_file(user_id=request.user.id, base64_attachment=b_64.decode(encoding='utf-8'),
                              file_name=request.FILES['file'].name)
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
            "user_uuid": user.uuid if not user.is_staff else None
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
                        project['username'] = User.objects.get(uuid=project['user_uuid'])
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
                                    "token": preferences.MainSettings.custom_MT_api_key if request.user.is_staff else request.user.group.api_key})
        return Response(response.json(), status=status.HTTP_200_OK)

    def delete(self, request):
        project_id = self.request.data.get('project_id')
        response = requests.delete(CLOUDSTORAGE_API_URL + f"{project_id}/",
            headers={"token": preferences.MainSettings.custom_MT_api_key if request.user.is_staff else request.user.group.api_key})

        return Response({"message": "Sucessfully deleted"}, status=status.HTTP_204_NO_CONTENT)
