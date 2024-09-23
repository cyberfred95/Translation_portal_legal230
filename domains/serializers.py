from rest_framework import serializers

from domains.models import Domain, DomainGroup


class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['name', 'french_name']


class DomainGroupSerializer(serializers.ModelSerializer):
    domains = serializers.SerializerMethodField()

    @staticmethod
    def get_domains(obj: DomainGroup):
        return DomainSerializer(obj.domains.all(), many=True).data

    class Meta:
        model = DomainGroup
        fields = ['name', 'french_name', 'domains']
