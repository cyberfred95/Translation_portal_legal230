from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from celery.result import AsyncResult
from django.conf import settings
from .tasks import start_gpt_process
from legal.mail_helpers import send_file_translation, send_text_translation, send_gpt_processing
import requests
from preferences import preferences
from .prompts_list import prompts_list
from rest_framework.views import APIView


class GPTProcessingView(TemplateView):

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['langs'] = {'en', 'fr'}
        return context

    template_name = "gpt_processing.html"


@csrf_exempt
@api_view(['POST'])
def gpt_process(request):
    data = request.data
    if not request.user.is_staff and not request.user.group:
        return Response({"message": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
    prompt = get_prompt(request)
    response = requests.post(
        url='https://console.custom.mt/gpt-processing/foreign_gpt_process/',
        headers={
            'token': preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
        },
        data={
            "text": data['text'],
            "prompt": prompt

        }
    )
    return Response(response.json(), status=status.HTTP_200_OK)


def get_prompt(request):
    for prompts in prompts_list:
        for prompt in prompts_list[prompts]:
            if request.data['prompt'] == prompt['slug']:
                return prompt['prompt']


@csrf_exempt
@api_view(['POST'])
def gpt_check(request):
    tasks = request.data
    print(tasks)
    response = requests.post(url='https://console.custom.mt/gpt-processing/gpt_check/', data=tasks)
    return Response(response.json(), status=status.HTTP_200_OK)
