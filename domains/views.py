from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from rest_framework.permissions import IsAuthenticated

from .models import Domain, DomainGroup
from .serializers import DomainSerializer, DomainGroupSerializer
from .tasks import update_domains as update_domains
from rest_framework.generics import ListAPIView
from subscriptions.permissions import SubscribedPermission

def update_domains_view(request):
    update_domains()
    return HttpResponseRedirect(reverse('admin:domains_domain_changelist'))


class DomainListView(ListAPIView):
    permission_classes = (SubscribedPermission, IsAuthenticated)
    serializer_class = DomainGroupSerializer

    def get_queryset(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return DomainGroup.objects.all().order_by('french_name')
        return DomainGroup.objects.all().order_by('name')
