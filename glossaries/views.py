from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from django.views.generic import TemplateView
from .models import Glossary
from .serializers import GlossarySerializer


# Create your views here.

class UserGlossariesView(TemplateView):
    template_name = 'glossaries.html'


class AddGlossaryView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer
