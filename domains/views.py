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
    queryset = DomainGroup.objects.all()
    serializer_class = DomainGroupSerializer
