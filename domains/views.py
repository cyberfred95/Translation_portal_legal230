from django.http import JsonResponse, HttpResponseRedirect
from django.urls import reverse
from .models import Domain, DomainGroup
from .serializers import DomainSerializer, DomainGroupSerializer
from .tasks import update_domains as update_domains
from rest_framework.generics import ListAPIView


# Create your views here.

def update_domains_view(request):
    update_domains()
    return HttpResponseRedirect(reverse('admin:domains_domain_changelist'))


class DomainListView(ListAPIView):

    def get_queryset(self):
        if self.request.LANGUAGE_CODE == 'fr':
            return DomainGroup.objects.all().order_by('french_name')
        return Domain.objects.all().order_by('name')
    serializer_class = DomainGroupSerializer
