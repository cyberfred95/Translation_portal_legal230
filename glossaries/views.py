from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from django.views.generic import TemplateView
from .models import Glossary
from .serializers import GlossarySerializer


# Create your views here.

class UserGlossariesView(TemplateView):
    template_name = 'glossaries.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['glossaries'] = Glossary.objects.all()
        print(context['glossaries'])
        return context


class AddGlossaryView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer
