import csv
import io
import logging
import os.path

import django.core.exceptions
import openpyxl
import requests as http_requests
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
        tmp_glossaries = Glossary.objects.filter(user=self.request.user)

        formatted_glossaries = [
            glossary.to_json(self.request)
            for glossary in tmp_glossaries
        ]
        return formatted_glossaries




class AddGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    @staticmethod
    def validate(request):
        if not request.user.is_staff:
            user_subscription = request.user.subscriptions.first()
            if user_subscription.custom_glossaries_count > 0:
                user_glossaries_count = Glossary.objects.filter(
                    user=request.user).count()
                if user_glossaries_count + 1 > user_subscription.custom_glossaries_count:
                    raise serializers.ValidationError({
                        "detail": "You are not allowed to add more glossaries. Please contact your group administator"})

        languages_list = Language.objects.all().values_list(
            Lower('abbreviation'), flat=True)
        if request.data["source_language"] == request.data["target_language"]:
            raise serializers.ValidationError(
                {"detail": _("Source and target languages cannot be the same")})
        if request.data["source_language"] not in languages_list:
            raise serializers.ValidationError(
                {"detail": _("Invalid source language")})
        if request.data["target_language"] not in languages_list:
            raise serializers.ValidationError(
                {"detail": _("Invalid target language")})

        gloss_file = request.FILES.get('file')
        processor = GlossaryProcessor()
        if os.path.splitext(gloss_file.name)[1] == '.csv':
            request.FILES['file'] = processor.convert_file_to_utf_8(gloss_file)
        try:
            processor.validate_file(gloss_file)
        except django.core.exceptions.ValidationError as e:
            raise serializers.ValidationError({"detail": str(list(e)[0])})

    def post(self, request):
        self.validate(request)
        gloss_file = request.FILES.get('file')
        source_language = Language.objects.get(
            abbreviation__iexact=request.data.get('source_language').upper())
        target_language = Language.objects.get(
            abbreviation__iexact=request.data.get('target_language').upper())

        glossary = Glossary.objects.create(
            user=request.user,
            source_language=source_language,
            target_language=target_language,
            file=gloss_file,
        )
        return Response(GlossarySerializer(glossary).data, status=status.HTTP_201_CREATED)


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = GlossarySerializer

    def get_object(self):
        return get_object_or_404(
            Glossary,
            user=self.request.user,
            id=self.kwargs['pk']
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
                # Transform to format expected by frontend
                glossaries = [
                    {'id': name, 'name': name}
                    for name in data.get('glossaries', [])
                ]
                return Response(glossaries, status=status.HTTP_200_OK)
            else:
                logger.error(f"LARA glossary search failed: {lara_response.status_code} - {lara_response.text}")
                return Response([], status=status.HTTP_200_OK)

        except http_requests.RequestException as e:
            logger.error(f"LARA glossary search exception: {str(e)}")
            return Response([], status=status.HTTP_200_OK)
