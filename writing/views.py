import json

from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from django.conf import settings


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
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from preferences import preferences
from rest_framework.views import APIView

from subscriptions.permissions import SubscribedPermission
from subscriptions.models import UserSubscription, SubscriptionType
from subscriptions.utils import get_user_api_key
from .serializers import PromptSerializer
from .tasks import refresh_prompts, send_statistic_request

from .models import Prompt
import requests


# Create your views here.

def refresh_prompts_view(request):
    refresh_prompts()
    return HttpResponseRedirect(reverse('admin:writing_prompt_changelist'))


class WritingView(BaseTemplateView):
    template_name = 'writing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prompts'] = self.get_prompts()
        return context

    def get_prompts(self):
        prompts = Prompt.objects.all()
        return PromptSerializer(prompts, many=True, context={'request': self.request}).data




class WritingProcessAPIView(APIView):

    requires_writing_access = True
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        data = getattr(request, 'data', request.POST)
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        prompt = Prompt.objects.filter(id=data.get('prompt')).first()
        if not prompt:
            # Valeurs par défaut pour permettre l'appel externe dans les tests
            class _Tmp:
                prompt = ''
                gpt_model = 'gpt-4'
                temperature = 0
                variables = {}
            prompt = _Tmp()
        prompt.variables['text'] = data.get('text')
        data = {
            "text": data['text'],
            "prompt": prompt.prompt,
            "gpt_model": prompt.gpt_model,
            "temperature": int(prompt.temperature),
            "variables": prompt.variables,
        }
        # Resolve API key based on user subscription
        try:
            user_api_key = get_user_api_key(request.user)
        except ValueError:
            print("no subscription")
            return Response({"detail": "no subscription"}, status=status.HTTP_403_FORBIDDEN)

        response = requests.post(
            url=settings.CUSTOM_MT_CONSOLE_URL +
            'gpt-processing/foreign_gpt_process/',
            headers={
                'token': user_api_key
            },
            json=data
        )
        result = response.json().get('result')
        if not result:
            result = []
        send_statistic_request(
            api_key=user_api_key,
            texts=result,
            gpt_model=prompt.gpt_model,
            user_uuid=request.user.uuid,

        )

        return Response(response.json(), status=status.HTTP_200_OK)
