from rest_framework import serializers

from domains.models import Domain, DomainGroup


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['name', 'french_name']


class DomainGroupSerializer(serializers.ModelSerializer):
    domains = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj: DomainGroup):
        if self.context['request'].LANGUAGE_CODE == 'fr':
            return obj.french_name
        return obj.name

    @staticmethod
    def get_domains(obj: DomainGroup):
        return DomainSerializer(obj.domains.all(), many=True).data

    class Meta:
        model = DomainGroup
        fields = ['name', 'french_name', 'domains']
