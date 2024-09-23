from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView
from django.views.generic import TemplateView
from rest_framework.views import APIView

from .models import Glossary
from .serializers import GlossarySerializer
from rest_framework.response import Response


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
                    "file_name": glossary.file.name,
                    "source_language": glossary.source_language.abbreviation.upper(),
                    "target_language": glossary.target_language.abbreviation.upper(),
                    "file_size": glossary.file_size(),
                    "created_at": glossary.created_at,
                }
            )
        return glossaries


class AddGlossaryView(CreateAPIView):
    serializer_class = GlossarySerializer


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

        glossaries = Glossary.objects.filter(
            domain__name=request.data.get('domain_name'),
            source_language__abbreviation=request.data.get('source_language').upper(),
            target_language__abbreviation=request.data.get('target_language').upper(),
            user=request.user
        )

        return Response(GlossarySerializer(glossaries, many=True).data, status=status.HTTP_200_OK)


class GetDefaultGlossaryView(APIView):
    serializer_class = GlossarySerializer

    def post(self, request):
        glossary = Glossary.objects.filter(
            source_language__abbreviation=request.data.get('source_language').upper(),
            target_language__abbreviation=request.data.get('target_language').upper(),
            is_default_glossary=True
        ).all()
        if request.LANGUAGE_CODE == 'fr':
            glossary = glossary.filter(domain__french_name=request.data.get('domain_name'))
        else:
            glossary = glossary.filter(domain__name=request.data.get('domain_name'))
        glossary = glossary.first()
        if glossary:
            return Response(GlossarySerializer(glossary).data, status=status.HTTP_200_OK)
        return Response({"message": "Default glossary not found"}, status=status.HTTP_404_NOT_FOUND)
