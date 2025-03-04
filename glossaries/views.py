from django.db.models.functions import Lower
from django.core.paginator import Paginator
from django.views.generic import TemplateView
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from domains.models import Domain
from languages.models import Language
from subscriptions.permissions import SubscribedPermission
from .models import Glossary
from .serializers import GlossarySerializer
from .paginators import APIViewPagination, TemplateViewPagination


# Create your views here.

class UserGlossariesView(TemplateView):
    template_name = 'glossaries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        glossaries_data, pagination_context = self.get_glossaries()
        context['glossaries'] = glossaries_data
        context['translate_languages'] = self.get_languages()
        context['paginator'] = pagination_context
        return context

    def get_languages(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return Language.objects.order_by('french_name').all()
        return Language.objects.order_by('name').all()

    def get_glossaries(self):
        tmp_glossaries = Glossary.objects.filter(user=self.request.user)

        paginator = TemplateViewPagination()
        paginated_glossaries = paginator.paginate_queryset(tmp_glossaries, self.request)

        formatted_glossaries = [
            {
                "id": glossary.id,
                "file_url": self.request.build_absolute_uri(glossary.file.url),
                "name": glossary.name,
                "source_language": glossary.source_language.abbreviation.upper(),
                "target_language": glossary.target_language.abbreviation.upper(),
                "file_size": glossary.file_size(),
                "created_at": glossary.created_at,
            }
            for glossary in paginated_glossaries
        ]
        return formatted_glossaries, paginator.get_paginated_context()


class AddGlossaryView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def validate(self, request):
        if not request.user.is_staff:
            group_subscription = request.user.group.subscriptions.first()
            if group_subscription.custom_glossaries_count >0:
                user_glossaries_count = Glossary.objects.filter(user=request.user).count()
                if user_glossaries_count + 1 > group_subscription.custom_glossaries_count:
                    raise serializers.ValidationError({"detail":"You are not allowed to add more glossaries. Please contact your group administator"})

        languages_list = Language.objects.all().values_list(Lower('abbreviation'), flat=True)
        if request.data["source_language"] == request.data["target_language"]:
            raise serializers.ValidationError({"detail":_("Source and target languages cannot be the same")})
        if request.data["source_language"] not in languages_list:
            raise serializers.ValidationError({"detail":_("Invalid source language")})
        if request.data["target_language"] not in languages_list:
            raise serializers.ValidationError({"detail":_("Invalid target language")})

    def post(self, request):
        self.validate(request)

        source_language = Language.objects.get(abbreviation__iexact=request.data.get('source_language').upper())
        target_language = Language.objects.get(abbreviation__iexact=request.data.get('target_language').upper())

        glossary = Glossary.objects.create(
            user=request.user,
            source_language=source_language,
            target_language=target_language,
            file=request.FILES.get('file'),
        )
        return Response(GlossarySerializer(glossary).data, status=status.HTTP_201_CREATED)


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    serializer_class = GlossarySerializer

    def get_object(self):
        return Glossary.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()


class GlossariesListAPIView(APIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)

    def post(self, request, *args, **kwargs):
        if 'source_language' and 'target_language' and 'domain_name' not in request.data:
            return Response(
                {"detail": "provide source_language, target_language and domain_name"},
                status=status.HTTP_400_BAD_REQUEST
            )
        glossaries = Glossary.objects.filter(
            source_language__abbreviation=request.data.get('source_language').upper(),
            target_language__abbreviation=request.data.get('target_language').upper()
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
            source_language__abbreviation=request.data.get('source_language').upper(),
            target_language__abbreviation=request.data.get('target_language').upper()
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
