from rest_framework import status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from django.views.generic import TemplateView
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import serializers

from domains.models import Domain
from languages.models import Language
from .models import Glossary
from .serializers import GlossarySerializer


# Create your views here.

class UserGlossariesView(TemplateView):
    template_name = 'glossaries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['glossaries'] = self.get_glossaries()
        return context

    def get_glossaries(self):
        tmp_glossaries = Glossary.objects.filter(user=self.request.user)
        glossaries = []
        for glossary in tmp_glossaries:
            glossaries.append(
                {
                    "file_url": self.request.build_absolute_uri(glossary.file.url),
                    "name": glossary.name,
                    "source_language": glossary.source_language.abbreviation.upper(),
                    "target_language": glossary.target_language.abbreviation.upper(),
                    "file_size": glossary.file_size(),
                    "created_at": glossary.created_at,
                }
            )
        return glossaries


class AddGlossaryView(APIView):

    def validate(self, request):
        errors = {}

        languages_list = Language.objects.all().values_list('abbreviation')
        if request.data["source_language"] == request.data["target_language"]:
            errors["language_pair"] = "Source and target languages cannot be the same"
        if request.data["source_language"] not in languages_list:
            errors["source_language"] = "Invalid source language"
        if request.data["target_language"] not in languages_list:
            errors["target_language"] = "Invalid target language"
        if request.LANGUAGE_CODE == 'fr':
            domains = Domain.objects.all().values_list('french_name', flat=True)
        else:
            domains = Domain.objects.all().values_list('name', flat=True)
        if request.data('domain_name') not in domains:
            errors["domain_name"] = "Invalid domain name"

        if errors:
            raise serializers.ValidationError(errors)

    def post(self, request):
        # self.validate(request)
        if request.LANGUAGE_CODE == 'fr':
            domain = Domain.objects.filter(french_name=request.data.get('domain_name'))
        else:
            domain = Domain.objects.filter(name=request.data.get('domain_name'))

        source_language = Language.objects.get(abbreviation=request.data.get('source_language').upper())
        target_language = Language.objects.get(abbreviation=request.data.get('target_language').upper())

        glossary = Glossary.objects.create(
            user=request.user,
            source_language=source_language,
            target_language=target_language,
            file=request.FILES.get('file'),
        )
        return Response(GlossarySerializer(glossary).data, status=status.HTTP_201_CREATED)


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    serializer_class = GlossarySerializer

    def get_queryset(self):
        return Glossary.objects.filter(user=self.request.user, id=self.kwargs['pk']).first()


class GlossariesListAPIView(APIView):

    def post(self, request, *args, **kwargs):
        if 'source_language' and 'target_language' and 'domain_name' not in request.data:
            return Response(
                {"message": "provide source_language, target_language and domain_name"},
                status=status.HTTP_400_BAD_REQUEST
            )
        domain = Domain.objects.get(
            name=request.data.get('domain_name')) if request.LANGUAGE_CODE != 'fr' else Domain.objects.get(
            french_name=request.data.get('domain_name'))
        glossaries = Glossary.objects.filter(
            domain=domain,
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
    serializer_class = GlossarySerializer

    def post(self, request):
        glossary = Glossary.objects.filter(
            source_language__abbreviation=request.data.get('source_language').upper(),
            target_language__abbreviation=request.data.get('target_language').upper(),
            user__isnull=True,
            group__isnull=True,
        ).all()
        if request.LANGUAGE_CODE == 'fr':
            glossary = glossary.filter(domain__french_name=request.data.get('domain_name'))
        else:
            glossary = glossary.filter(domain__name=request.data.get('domain_name'))
        glossary = glossary.first()
        if glossary:
            return Response(GlossarySerializer(glossary).data, status=status.HTTP_200_OK)
        return Response({"message": "Default glossary not found"}, status=status.HTTP_404_NOT_FOUND)
