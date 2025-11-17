import re
import langdetect
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from languages.models import Language
from subscriptions.permissions import SubscribedPermission
from subscriptions.helpers import translation_allowed


class DetectTextLanguageView(APIView):
    WORDS_COUNT_FOR_DETECTION = 500
    permission_classes = (SubscribedPermission, IsAuthenticated)

    @staticmethod
    def text_string_to_array(text):
        text = re.sub(r'<[^>]*>', '', text)
        text = text.split()
        return text

    def post(self, request):

        text = request.data.get('text')
        text_for_detection = self.get_text_for_detection(text)
        symbols_count = len(text_for_detection)
        texts = self.text_string_to_array(text)
        if translation_allowed(request, words_count=len(texts), symbols_count=symbols_count):
            try:
                tmp_language = langdetect.detect(text_for_detection)
                language = Language.objects.filter(abbreviation__iexact=tmp_language.upper()).values_list(
                    'abbreviation', flat=True).first()
                if not language:
                    language = Language.objects.all().values_list(
                        'abbreviation', flat=True).first()
            except langdetect.LangDetectException:
                return Response({"detail": "Source text should not be blank"}, status=status.HTTP_400_BAD_REQUEST)
            return Response({"language": language.upper()})
        return Response({"detail": "You are not allowed to translate such amount of data"},
                        status=status.HTTP_400_BAD_REQUEST)

    def get_text_for_detection(self, text):
        text = self.text_string_to_array(text)

        text_for_detection = ' '.join(text[:self.WORDS_COUNT_FOR_DETECTION])
        return text_for_detection


