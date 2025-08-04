# Django imports
from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

# Local imports
from languages.models import Language
from ..utils import get_user_and_data


@method_decorator(csrf_exempt, name='dispatch')
class LanguageAPIView(View):
    """
    API view for handling language-related requests.

    Provides endpoints to retrieve available languages with their codes
    and names for translation services.
    """

    def get(self, request):
        """
        Handle GET requests to retrieve all available languages.

        Args:
            request: Django HttpRequest object

        Returns:
            JsonResponse: List of languages with name and language_code
        """
        _, _, error_msg = get_user_and_data(request, with_data=False)
        if error_msg:
            return JsonResponse(error_msg, status=400)

        languages = Language.objects.all()
        data = [
            {"name": lang.name, "language_code": lang.abbreviation}
            for lang in languages
        ]
        return JsonResponse(data, status=200, safe=False)
