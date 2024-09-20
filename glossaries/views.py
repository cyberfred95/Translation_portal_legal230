from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from django.views.generic import TemplateView
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
        tmp_glossaries = Glossary.objects.all()
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


class GlossariesListAPIView(ListAPIView):
    serializer_class = GlossarySerializer

    def get_queryset(self):
        return Glossary.objects.filter(user=self.request.user)
