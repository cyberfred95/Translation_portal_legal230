from rest_framework import serializers

from writing.models import Prompt


class PromptSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()

    def get_translation(self, instance: Prompt):
        return instance.translations.filter(language=self.context['request'].LANGUAGE_CODE).first()

    def get_name(self, instance: Prompt):
        translation = self.get_translation(instance)
        if translation:
            return translation.name

    def get_description(self, instance: Prompt):
        translation = self.get_translation(instance)
        if translation:
            return translation.description

    class Meta:
        model = Prompt
        fields = '__all__'
