from django.shortcuts import render
from rest_framework.generics import ListAPIView, CreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from .models import Glossary
from .serializers import GlossarySerializer


# Create your views here.

class UserGlossariesView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer

    def get_queryset(self):
        return Glossary.objects.filter(user=self.request.user)


class AddGlossaryView(CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer


class SingleGlossaryView(RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = GlossarySerializer
