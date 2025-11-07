from django.http import JsonResponse

from legal.views_all import BaseTemplateView, text_translation, file_translate
from subscriptions.models import SubscriptionType
from languages.models import Language
from legal.credentials import languages


class TranslateView(BaseTemplateView):
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

