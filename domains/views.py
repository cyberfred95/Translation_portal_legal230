from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated

from .models import Domain, DomainGroup
from .serializers import DomainSerializer, DomainGroupSerializer
from rest_framework.generics import ListAPIView
from subscriptions.permissions import SubscribedPermission

class DomainListView(ListAPIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = DomainGroupSerializer

    def get_queryset(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return DomainGroup.objects.all().order_by('french_name')
        return DomainGroup.objects.all().order_by('name')
