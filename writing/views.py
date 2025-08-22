import json

from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from preferences import preferences
from rest_framework.views import APIView

from subscriptions.permissions import SubscribedPermission
from .serializers import PromptSerializer
from .tasks import refresh_prompts, send_statistic_request

from .models import Prompt
import requests


# Create your views here.

def refresh_prompts_view(request):
    refresh_prompts()
    return HttpResponseRedirect(reverse('admin:writing_prompt_changelist'))


class WritingView(TemplateView):
    template_name = 'writing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prompts'] = self.get_prompts()
        return context

    def get_prompts(self):
        prompts = Prompt.objects.all()
        return PromptSerializer(prompts, many=True, context={'request': self.request}).data


class Writing2View(TemplateView):
    template_name = 'writing_2.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prompts'] = self.get_prompts_with_translations()
        return context

    def get_prompts_with_translations(self):
        """Get prompts with their translations for the current language"""
        from django.utils.translation import get_language
        language_code = get_language() or 'en'
        
        prompts = Prompt.objects.prefetch_related('translations').all()
        
        prompts_data = []
        for prompt in prompts:
            # Get translation for current language or fallback to English
            translation = prompt.translations.filter(language=language_code).first()
            if not translation:
                translation = prompt.translations.filter(language='en').first()
            
            if translation:
                prompt_data = {
                    'id': prompt.id,
                    'name': translation.name,
                    'description': translation.description,
                    'gpt_model': prompt.gpt_model,
                    'temperature': prompt.temperature,
                    'prompt': prompt.prompt,
                    'variables': prompt.variables,
                    # Infer action type from name (can be improved with a dedicated field)
                    'action_type': self.infer_action_type(translation.name.lower())
                }
                prompts_data.append(prompt_data)
        
        return prompts_data
    
    def infer_action_type(self, name):
        """Infer action type from prompt name for icon selection"""
        name = name.lower()
        if 'anonym' in name:
            return 'anonymise'
        elif 'summar' in name or 'résumé' in name:
            return 'summarise'
        elif 'detail' in name or 'détail' in name:
            return 'detail'
        elif 'explain' in name or 'expliqu' in name:
            return 'explain'
        elif 'shorten' in name or 'raccour' in name:
            return 'shorten'
        elif 'simple' in name:
            return 'simple'
        elif 'professional' in name or 'professionnel' in name:
            return 'professional'
        elif 'casual' in name or 'décontract' in name:
            return 'casual'
        else:
            return 'default'


class WritingProcessAPIView(APIView):

    requires_writing_access = True
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        data = request.data
        if not request.user.is_staff and not request.user.group:
            return Response({"detail": "You have to be staff or to be in group"}, status=status.HTTP_403_FORBIDDEN)
        prompt = Prompt.objects.filter(id=data['prompt']).first()
        if not prompt:
            return Response({"detail": "Prompt not found"}, status=status.HTTP_404_NOT_FOUND)
        prompt.variables['text'] = data.get('text')
        data = {
            "text": data['text'],
            "prompt": prompt.prompt,
            "gpt_model": prompt.gpt_model,
            "temperature": int(prompt.temperature),
            "variables": prompt.variables,
        }
        response = requests.post(
            url=preferences.MainSettings.CUSTOM_MT_CONSOLE_URL +
            'gpt-processing/foreign_gpt_process/',
            headers={
                'token': preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
            },
            json=data
        )
        result = response.json().get('result')
        if not result:
            result = []
        send_statistic_request(
            api_key=preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key,
            texts=result,
            gpt_model=prompt.gpt_model,
            user_uuid=request.user.uuid,

        )

        return Response(response.json(), status=status.HTTP_200_OK)
