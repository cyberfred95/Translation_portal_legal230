from rest_framework import serializers
from .models import Glossary
from languages.models import Language


class GlossarySerializer(serializers.ModelSerializer):
    class Meta:
        model = Glossary
        fields = ['name', 'file', 'source_language', 'target_language', 'domain']


    def validate(self, data):
        errors = {}
        print(data)
        languages_list = Language.objects.all().values_list('abbreviation')
        if data["source_language"] == data["target_language"]:
            errors["language_pair"] = "Source and target languages cannot be the same"
        if data["source_language"] not in languages_list:
            errors["source_language"] = "Invalid source language"
        if data["target_language"] not in languages_list:
            errors["target_language"] = "Invalid target language"
        if errors:
            raise serializers.ValidationError(errors)

        return data

    def create(self, validated_data):
        instance = Glossary.objects.create(**validated_data, user=self.context['request'].user)
        return instance
