from .serializers import PromptSerializer
from .tasks import refresh_prompts
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework.views import APIView
from .models import Prompt


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
