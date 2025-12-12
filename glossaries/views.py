import csv
import io
import logging
import os.path

import django.core.exceptions
import openpyxl
import requests as http_requests
import requests
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.conf import settings

logger = logging.getLogger(__name__)


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
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from domains.models import Domain
from languages.models import Language
from subscriptions.permissions import SubscribedPermission
from users.models import User
from .models import Glossary
from .processor import GlossaryProcessor
from .serializers import GlossarySerializer
from .paginators import APIViewPagination, TemplateViewPagination


# Create your views here.

class UserGlossariesView(BaseTemplateView):
    template_name = 'glossaries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['glossaries'] = self.get_glossaries()
        context['translate_languages'] = self.get_languages()
        return context

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def get_glossaries(self):
        """
        Fetch personal glossaries from Lara-django API (read-only).
        Only fetches glossaries with UUID != '*' (personal glossaries).
        """
        from django.conf import settings
        import requests
        
        user_uuid = str(self.request.user.uuid) if hasattr(self.request.user, 'uuid') else None
        
        if not user_uuid:
            # If user has no UUID, return empty list
            return []
        
        try:
            # Fetch personal glossaries from Lara-django
            lara_url = f"{settings.LARA_API_URL}/api/lara/glossaries-list/search/"
            response = requests.get(
                lara_url,
                params={
                    'uuid': user_uuid,
                },
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Transform to format expected by frontend
                formatted_glossaries = []
                for g in data.get('glossaries', []):
                    # Use user_glossary_name if available, otherwise name
                    display_name = g.get('user_glossary_name') or g.get('name', '')
                    formatted_glossaries.append({
                        'id': g.get('glossary_id', ''),
                        'name': display_name,
                        'source_language': g.get('source_language', ''),
                        'target_language': g.get('target_languages', '').split(',')[0] if g.get('target_languages') else '',
                        'created_at': g.get('generated_at', ''),
                    })
                return formatted_glossaries
            else:
                logger.error(f"Failed to fetch glossaries from Lara-django: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching glossaries from Lara-django: {str(e)}")
            return []




class AddGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def dispatch(self, request, *args, **kwargs):
        """
        Override dispatch to clean request.POST before DRF parses it into request.data.
        DRF automatically parses request.POST into request.data for multipart/form-data,
        but we don't need source_language/target_language fields anymore.
        """
        # Remove source_language and target_language from request.POST before DRF parses it
        # This prevents MultiValueDictKeyError if something tries to access these fields
        if hasattr(request, 'POST') and request.method == 'POST':
            from django.http import QueryDict
            if isinstance(request.POST, QueryDict):
                # Make POST mutable and remove unwanted fields
                mutable_post = request.POST.copy()
                if 'source_language' in mutable_post:
                    mutable_post.pop('source_language', None)
                if 'target_language' in mutable_post:
                    mutable_post.pop('target_language', None)
                # Replace request.POST with cleaned version
                request.POST = mutable_post
        
        return super().dispatch(request, *args, **kwargs)

    def _extract_error_message(self, response):
        """
        Extract error message from LARA API response.
        
        Args:
            response: requests.Response object
            
        Returns:
            str: Error message, or default message if extraction fails
        """
        if not response.content:
            return f"Erreur HTTP {response.status_code} : réponse vide du serveur LARA"
        
        try:
            error_data = response.json()
            # Try multiple possible error field names
            error_fields = ['error', 'detail', 'message', 'errors']
            for field in error_fields:
                error_value = error_data.get(field)
                if error_value:
                    # Handle both string and dict/list errors
                    if isinstance(error_value, str):
                        error_value = error_value.strip()
                        # Check if message is empty or just "LARA error:" with nothing after
                        if error_value and not self._is_empty_error_message(error_value):
                            return error_value
                    elif isinstance(error_value, (list, dict)) and error_value:
                        return str(error_value)
        except (ValueError, KeyError, AttributeError):
            pass
        
        # If JSON parsing fails, try to get text content
        if response.text:
            text_content = response.text.strip()[:500]
            if text_content and not self._is_empty_error_message(text_content):
                return text_content
        
        # Default fallback - return None to trigger default message in _format_error_message
        return None
    
    def _is_empty_error_message(self, message):
        """
        Check if error message is effectively empty (just prefixes without content).
        
        Args:
            message: Error message string
            
        Returns:
            bool: True if message is empty or just contains error prefixes
        """
        if not message or not message.strip():
            return True
        
        # Check for common empty error patterns
        empty_patterns = [
            "LARA error:",
            "LARA error: ",
            "Error creating glossary:",
            "Error creating glossary: ",
            "Erreur lors de la création du glossaire :",
            "Erreur lors de la création du glossaire : ",
        ]
        
        message_lower = message.strip().lower()
        for pattern in empty_patterns:
            if message_lower == pattern.lower() or message_lower == pattern.lower().rstrip():
                return True
        
        return False
    
    def _format_error_message(self, status_code, error_detail):
        """
        Format error message for user display.
        
        Args:
            status_code: HTTP status code
            error_detail: Raw error message from API (can be None)
            
        Returns:
            str: Formatted, user-friendly error message
        """
        # If error detail is None, empty, or just whitespace/prefixes, provide default message
        if not error_detail or not error_detail.strip() or self._is_empty_error_message(error_detail):
            if status_code == 400:
                return "Les données envoyées sont invalides. Veuillez vérifier le format du fichier CSV et réessayer."
            elif status_code == 401:
                return "Authentification requise. Veuillez vous reconnecter."
            elif status_code == 403:
                return "Vous n'avez pas les permissions nécessaires pour créer un glossaire."
            elif status_code == 404:
                return "L'endpoint de création de glossaire est introuvable. Veuillez contacter le support technique."
            elif status_code == 502:
                return "Le serveur LARA n'a pas pu traiter votre demande. Veuillez réessayer dans quelques instants ou contacter le support si le problème persiste."
            elif status_code >= 500:
                return "Une erreur serveur s'est produite lors de la création du glossaire. Veuillez réessayer plus tard ou contacter le support technique."
            else:
                return f"Erreur lors de la création du glossaire (code HTTP {status_code}). Veuillez réessayer ou contacter le support si le problème persiste."
        
        # Clean up common error prefixes
        error_detail = error_detail.strip()
        prefixes_to_remove = [
            "Error creating glossary: ",
            "LARA error: ",
            "LARA error:",
            "Erreur lors de la création du glossaire : ",
            "Erreur lors de la création du glossaire :",
        ]
        for prefix in prefixes_to_remove:
            if error_detail.startswith(prefix):
                error_detail = error_detail[len(prefix):].strip()
        
        # If after cleaning the message is empty or just the prefix, use default
        if not error_detail or self._is_empty_error_message(error_detail):
            if status_code >= 500:
                return "Une erreur serveur s'est produite lors de la création du glossaire. Veuillez réessayer plus tard ou contacter le support technique."
            else:
                return "Une erreur s'est produite lors de la création du glossaire. Veuillez réessayer."
        
        return error_detail

    def post(self, request):
        """
        Create a personal glossary via Lara-django API.
        Languages are automatically detected from CSV file.
        """
        from django.conf import settings
        import requests
        
        user_uuid = str(request.user.uuid) if hasattr(request.user, 'uuid') else None
        
        if not user_uuid:
            return Response(
                {"detail": "UUID utilisateur introuvable. Veuillez vous reconnecter."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gloss_file = request.FILES.get('file')
        if not gloss_file:
            return Response(
                {"detail": "Un fichier est requis pour créer un glossaire. Veuillez sélectionner un fichier CSV."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (5MB max)
        max_file_size = 5 * 1024 * 1024
        if gloss_file.size > max_file_size:
            return Response(
                {"detail": f"La taille du fichier ({gloss_file.size / (1024*1024):.2f} MB) dépasse la limite autorisée de 5 MB. Veuillez utiliser un fichier plus petit."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate LARA_API_URL configuration
        if not settings.LARA_API_URL:
            logger.error("LARA_API_URL is not configured in settings")
            return Response(
                {"detail": "La configuration du serveur LARA est manquante. Veuillez contacter le support technique."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if URL uses Docker service name (common misconfiguration)
        if settings.LARA_API_URL.startswith('http://') and ('django' in settings.LARA_API_URL or 'laradjango' in settings.LARA_API_URL):
            logger.error(f"LARA_API_URL is configured with Docker service name: {settings.LARA_API_URL}")
            return Response(
                {"detail": "La configuration de l'URL LARA est incorrecte. Veuillez contacter le support technique."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        try:
            # Call Lara-django create-from-lexa endpoint
            lara_url = f"{settings.LARA_API_URL}/api/lara/glossaries-list/create-from-lexa/"
            
            files = {
                'glossary_file': (gloss_file.name, gloss_file, gloss_file.content_type)
            }
            headers = {
                'X-User-UUID': user_uuid
            }
            
            response = requests.post(
                lara_url,
                files=files,
                headers=headers,
                timeout=300  # 5 minutes for large files
            )
            
            if response.status_code == 201:
                try:
                    lara_data = response.json()
                except (ValueError, KeyError) as e:
                    logger.error(f"Failed to parse JSON response from LARA API: {str(e)} - Response content: {response.text[:200]}")
                    return Response(
                        {"detail": "Le serveur LARA a retourné une réponse dans un format invalide. Le glossaire a peut-être été créé, mais nous n'avons pas pu confirmer. Veuillez vérifier votre liste de glossaires."},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                
                # Transform to format expected by frontend
                return Response({
                    'id': lara_data.get('glossary_id', ''),
                    'name': lara_data.get('user_glossary_name', lara_data.get('name', '')),
                    'source_language': lara_data.get('source_language', ''),
                    'target_language': lara_data.get('target_languages', '').split(',')[0] if lara_data.get('target_languages') else '',
                    'created_at': lara_data.get('generated_at', ''),
                }, status=status.HTTP_201_CREATED)
            else:
                # Handle error response
                error_detail = self._extract_error_message(response)
                
                # Log detailed error information for debugging
                logger.error(
                    f"Lara-django glossary creation failed: {response.status_code} - {error_detail} - URL: {lara_url}",
                    extra={
                        'response_status': response.status_code,
                        'response_headers': dict(response.headers),
                        'response_body': response.text[:500] if response.text else None,
                    }
                )
                
                # Format user-friendly error message
                formatted_error = self._format_error_message(response.status_code, error_detail)
                
                return Response(
                    {"detail": formatted_error},
                    status=response.status_code if response.status_code < 500 else status.HTTP_502_BAD_GATEWAY
                )
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            logger.error(f"Cannot connect to LARA API at {settings.LARA_API_URL}: {error_msg}", exc_info=True)
            if 'name resolution' in error_msg.lower() or 'failed to establish' in error_msg.lower():
                return Response(
                    {"detail": f"Impossible de se connecter au serveur LARA. Veuillez vérifier la configuration (URL actuelle : {settings.LARA_API_URL}). Si le problème persiste, contactez le support."},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            return Response(
                {"detail": f"Erreur de connexion au serveur LARA : {error_msg}. Veuillez réessayer plus tard."},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout calling LARA API: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Le délai d'attente de la requête a été dépassé. Le fichier est peut-être trop volumineux ou le serveur est surchargé. Veuillez réessayer avec un fichier plus petit ou plus tard."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.RequestException as e:
            error_msg = str(e)
            logger.error(f"Error calling Lara-django API: {error_msg}", exc_info=True)
            # Format error message more clearly
            if not error_msg or error_msg.strip() == "":
                formatted_error = "Une erreur s'est produite lors de la communication avec le serveur LARA. Veuillez réessayer plus tard."
            else:
                formatted_error = f"Erreur lors de la création du glossaire : {error_msg}"
            return Response(
                {"detail": formatted_error},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Unexpected error in AddGlossaryView: {error_msg}", exc_info=True)
            formatted_error = (
                f"Une erreur inattendue s'est produite lors de la création du glossaire : {error_msg}"
                if error_msg and error_msg.strip()
                else "Une erreur inattendue s'est produite lors de la création du glossaire. Veuillez réessayer ou contacter le support."
            )
            return Response(
                {"detail": formatted_error},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = GlossarySerializer

    def get_object(self):
        """
        Fetch glossary from Lara-django API instead of local DB.
        """
        from django.conf import settings
        import requests
        
        user_uuid = str(self.request.user.uuid) if hasattr(self.request.user, 'uuid') else None
        glossary_id = self.kwargs['pk']
        
        if not user_uuid:
            from rest_framework.exceptions import NotFound
            raise NotFound("User UUID not found")
        
        try:
            # Fetch from Lara-django search endpoint
            lara_url = f"{settings.LARA_API_URL}/api/lara/glossaries-list/search/"
            response = requests.get(
                lara_url,
                params={'uuid': user_uuid},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                # Find glossary by ID
                for g in data.get('glossaries', []):
                    if g.get('glossary_id') == glossary_id:
                        # Return a mock object with the data
                        class MockGlossary:
                            def __init__(self, data):
                                self.id = data.get('glossary_id', '')
                                # Use user_glossary_name if available, otherwise name
                                self.name = data.get('user_glossary_name') or data.get('name', '')
                                self.source_language = type('obj', (object,), {'abbreviation': data.get('source_language', '')})()
                                self.target_language = type('obj', (object,), {'abbreviation': data.get('target_languages', '').split(',')[0] if data.get('target_languages') else ''})()
                                self.created_at = data.get('generated_at', '')
                        return MockGlossary(g)
            
            from rest_framework.exceptions import NotFound
            raise NotFound("Glossary not found")
        except requests.RequestException as e:
            logger.error(f"Error fetching glossary from Lara-django: {str(e)}")
            from rest_framework.exceptions import NotFound
            raise NotFound("Error fetching glossary")
    
    def delete(self, request, *args, **kwargs):
        """
        Delete glossary via Lara-django API.
        """
        from django.conf import settings
        import requests
        
        glossary_id = self.kwargs['pk']
        
        try:
            lara_url = f"{settings.LARA_API_URL}/api/lara/glossaries-list/{glossary_id}/delete/"
            response = requests.delete(lara_url, timeout=10)
            
            if response.status_code == 200:
                return Response(status=status.HTTP_204_NO_CONTENT)
            else:
                error_detail = response.json().get('error', 'Unknown error') if response.content else 'Unknown error'
                return Response(
                    {"detail": error_detail},
                    status=response.status_code
                )
        except requests.RequestException as e:
            logger.error(f"Error deleting glossary from Lara-django: {str(e)}")
            return Response(
                {"detail": f"Error deleting glossary: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GlossariesListAPIView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request, *args, **kwargs):
        if 'source_language' and 'target_language' and 'domain_name' not in request.data:
            return Response(
                {"detail": "provide source_language, target_language and domain_name"},
                status=status.HTTP_400_BAD_REQUEST
            )
        glossaries = Glossary.objects.filter(
            source_language__abbreviation=request.data.get(
                'source_language').upper(),
            target_language__abbreviation=request.data.get(
                'target_language').upper()
        )
        user_glossaries = glossaries.filter(
            user=request.user, group__isnull=True
        )
        group_glossaries = glossaries.filter(
            group=request.user.group,
            group__isnull=False
        )
        glossaries = user_glossaries | group_glossaries

        return Response(GlossarySerializer(glossaries, many=True).data, status=status.HTTP_200_OK)


class GetDefaultGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = GlossarySerializer

    def post(self, request):
        domain_name = request.data.get('domain_name')
        glossary = Glossary.objects.filter(
            source_language__abbreviation=request.data.get(
                'source_language').upper(),
            target_language__abbreviation=request.data.get(
                'target_language').upper()
        ).all()
        if request.LANGUAGE_CODE == 'fr':
            default_glossary = glossary.filter(domain__french_name=domain_name)
            if not default_glossary.exists():
                default_glossary = glossary.filter(domain__name=domain_name)
        else:
            default_glossary = glossary.filter(domain__name=domain_name)
        glossary = default_glossary.first()
        if glossary:
            return Response(GlossarySerializer(glossary).data, status=status.HTTP_200_OK)
        return Response({}, status=status.HTTP_200_OK)


class LaraGlossarySearchView(APIView):
    """
    Proxy endpoint to search glossaries in LARA backend.

    Calls /lara-django/api/lara/glossaries-list/search/ with user's UUID
    to find personal glossaries.
    """
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request):
        source_language = request.data.get('source_language', '').upper()
        target_language = request.data.get('target_language', '').upper()
        domain = request.data.get('domain', '*')

        if not source_language or not target_language:
            return Response(
                {"detail": "source_language and target_language are required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user UUID for personal glossaries
        user_uuid = str(request.user.uuid) if hasattr(request.user, 'uuid') else None

        if not user_uuid:
            return Response({
                'glossaries': [],
                'count': 0
            }, status=status.HTTP_200_OK)

        try:
            # Call LARA backend glossary search endpoint
            lara_response = http_requests.get(
                f"{settings.LARA_API_URL}/api/lara/glossaries-list/search/",
                params={
                    'uuid': user_uuid,
                    'source_language': source_language,
                    'target_languages': target_language,
                    'domain': domain
                },
                timeout=10
            )

            if lara_response.status_code == 200:
                data = lara_response.json()
                # Transform to format expected by frontend (with glossary_id)
                glossaries = [
                    {'id': g.get('glossary_id', ''), 'name': g.get('name', '')}
                    for g in data.get('glossaries', [])
                ]
                return Response(glossaries, status=status.HTTP_200_OK)
            else:
                logger.error(f"LARA glossary search failed: {lara_response.status_code} - {lara_response.text}")
                return Response([], status=status.HTTP_200_OK)

        except http_requests.RequestException as e:
            logger.error(f"LARA glossary search exception: {str(e)}")
            return Response([], status=status.HTTP_200_OK)
