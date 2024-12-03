from rest_framework import serializers
from preferences import preferences
from domains.models import Domain, DomainGroup, DefaultTranslation


class DefaultDomainSerializer(serializers.ModelSerializer):

    class Meta:
        model = DefaultTranslation
        fields = ['name', 'french_name']


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['name', 'french_name']


class DomainGroupSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    def get_name(self, obj: DomainGroup):
        if self.context['request'].LANGUAGE_CODE == 'fr':
            return obj.french_name
        return obj.name


    class Meta:
        model = DomainGroup
        fields = ['name', 'french_name', 'domains']
