from rest_framework import serializers
from .models import Glossary
from languages.models import Language


class GlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Glossary
        fields = ['name', 'file', 'source_language', 'target_language', 'domain']

