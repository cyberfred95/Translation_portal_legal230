from rest_framework import serializers
from .models import Glossary
from languages.models import Language


class GlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Glossary
        fields = '__all__'

    def validate(self, data):
        errors = {}
        languages_list = Language.objects.all().values_list('abbreviation')
        if data["source_language"] == data["target_language"]:
            errors["language_pair"] = "Source and target languages cannot be the same"
        if data["source_language"] not in languages_list:
            errors["source_language"] = "Source and target languages cannot be the same"
        if data["target_language"] not in languages_list:
            errors["target_language"] = "Target languages cannot be the same"

        if errors:
            raise serializers.ValidationError(errors)

        return data
