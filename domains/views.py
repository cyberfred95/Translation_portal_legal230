from django.http import JsonResponse, HttpResponseRedirect

from .models import Domain
from .serializers import DomainSerializer
from .tasks import update_domains as update_domains
from rest_framework.generics import ListAPIView


# Create your views here.

def update_domains_view(request):
    update_domains()
    return HttpResponseRedirect(f'/{request.LANGUAGE_CODE}/admin/domains/domain/')


class DomainListView(ListAPIView):
    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
