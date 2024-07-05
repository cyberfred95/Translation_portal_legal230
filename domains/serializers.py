from rest_framework.serializers import ModelSerializer

from domains.models import Domain


class DomainSerializer(ModelSerializer):

    class Meta:
        model = Domain
        fields = ['name', 'french_name']
