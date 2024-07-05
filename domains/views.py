from django.http import JsonResponse, HttpResponseRedirect

from .tasks import update_domains as update_domains


# Create your views here.

def update_domains_view(request):
    update_domains()
    return HttpResponseRedirect('/en/admin/domains/domain/')
