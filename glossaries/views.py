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
                {"detail": "User UUID not found"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        gloss_file = request.FILES.get('file')
        if not gloss_file:
            return Response(
                {"detail": "File is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file size (5MB max)
        max_file_size = 5 * 1024 * 1024
        if gloss_file.size > max_file_size:
            return Response(
                {"detail": "File size exceeds 5MB limit"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate LARA_API_URL configuration
        if not settings.LARA_API_URL:
            logger.error("LARA_API_URL is not configured in settings")
            return Response(
                {"detail": "LARA API URL is not configured. Please contact support."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Check if URL uses Docker service name (common misconfiguration)
        if settings.LARA_API_URL.startswith('http://') and ('django' in settings.LARA_API_URL or 'laradjango' in settings.LARA_API_URL):
            logger.error(f"LARA_API_URL is configured with Docker service name: {settings.LARA_API_URL}")
            return Response(
                {"detail": "LARA API URL is misconfigured. Please use the public URL (https://api.portail.lexamt.fr/lara-django) instead of Docker service name."},
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
                    logger.error(f"Failed to parse JSON response from LARA API: {str(e)}")
                    return Response(
                        {"detail": "Invalid response format from LARA API"},
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
                error_detail = 'Unknown error'
                try:
                    if response.content:
                        error_data = response.json()
                        error_detail = error_data.get('error') or error_data.get('detail') or error_data.get('message', 'Unknown error')
                except (ValueError, KeyError):
                    # If JSON parsing fails, try to get text content
                    error_detail = response.text[:200] if response.text else f"HTTP {response.status_code} error"
                
                logger.error(f"Lara-django glossary creation failed: {response.status_code} - {error_detail} - URL: {lara_url}")
                return Response(
                    {"detail": error_detail},
                    status=response.status_code if response.status_code < 500 else status.HTTP_502_BAD_GATEWAY
                )
        except requests.exceptions.ConnectionError as e:
            error_msg = str(e)
            logger.error(f"Cannot connect to LARA API at {settings.LARA_API_URL}: {error_msg}", exc_info=True)
            if 'name resolution' in error_msg.lower() or 'failed to establish' in error_msg.lower():
                return Response(
                    {"detail": f"Cannot connect to LARA API. Please check LARA_API_URL configuration. Current value: {settings.LARA_API_URL}"},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            return Response(
                {"detail": f"Connection error: {error_msg}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout calling LARA API: {str(e)}", exc_info=True)
            return Response(
                {"detail": "Request to LARA API timed out. Please try again."},
                status=status.HTTP_504_GATEWAY_TIMEOUT
            )
        except requests.RequestException as e:
            logger.error(f"Error calling Lara-django API: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"Error creating glossary: {str(e)}"},
                status=status.HTTP_502_BAD_GATEWAY
            )
        except Exception as e:
            logger.error(f"Unexpected error in AddGlossaryView: {str(e)}", exc_info=True)
            return Response(
                {"detail": f"An unexpected error occurred: {str(e)}"},
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
