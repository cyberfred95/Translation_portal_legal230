from .tasks import refresh_prompts
from django.http import HttpResponse
# Create your views here.

def refesh_prompts_view(request):
    refresh_prompts()
    return HttpResponse("Success")

