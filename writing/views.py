from django.views.generic import TemplateView
from django.conf import settings
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from subscriptions.permissions import SubscribedPermission


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


class WritingView(BaseTemplateView):
    """
    Vue pour la page Writing.
    Affiche l'interface de modification de texte avec GPT.
    """
    template_name = 'writing.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['prompts'] = self.get_prompts()
        return context

    def get_prompts(self):
        from .serializers import PromptSerializer
        from .models import Prompt
        prompts = Prompt.objects.all()
        return PromptSerializer(prompts, many=True, context={'request': self.request}).data


class WritingProcessAPIView(APIView):
    """
    API endpoint for processing text with GPT.

    Requires:
    - User authentication
    - Active subscription with access_to_writing=True
    - User must be staff OR belong to a group
    """
    requires_writing_access = True
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        from .services import OpenAIClient, OpenAIClientError
        from .models import Prompt
        from subscriptions.helpers import translation_allowed, add_translations
        from legal.helpers import get_word_count

        data = getattr(request, 'data', request.POST)

        # Validate user permissions
        if not request.user.is_staff and not request.user.group:
            return Response(
                {"detail": "You have to be staff or to be in group"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Get input text
        text = data.get('text', '')
        if not text:
            return Response(
                {"detail": "Text is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Count words and symbols for quota check
        words_count = get_word_count(text)
        symbols_count = len(text)

        # Check quota BEFORE processing
        is_allowed, error_code, error_message = translation_allowed(
            request,
            words_count=words_count,
            symbols_count=symbols_count
        )
        if not is_allowed:
            return Response(
                {"detail": str(error_message) if error_message else "Translation not allowed"},
                status=status.HTTP_403_FORBIDDEN
            )

        # Load prompt configuration
        prompt_obj = Prompt.objects.filter(id=data.get('prompt')).first()
        if not prompt_obj:
            return Response(
                {"detail": "Prompt not found"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build variables dict with user text
        variables = dict(prompt_obj.variables) if prompt_obj.variables else {}
        variables['text'] = text

        # Call OpenAI API
        try:
            client = OpenAIClient()
            response = client.process_text(
                text=text,
                prompt=prompt_obj.prompt,
                model=prompt_obj.gpt_model,
                temperature=float(prompt_obj.temperature),
                variables=variables
            )

            if not response.success:
                return Response(
                    {"detail": response.error},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )

            # Update quota AFTER successful processing
            add_translations(request, words_count=words_count, symbols_count=symbols_count)

            # Format response (split by newlines to match expected format for frontend)
            result = [line for line in response.content.split('\n') if line.strip()]
            if not result:
                result = [response.content]

            return Response({"result": result}, status=status.HTTP_200_OK)

        except OpenAIClientError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
