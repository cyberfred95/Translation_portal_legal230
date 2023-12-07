from django.urls import path
from .views import GPTProcessingView, gpt_process, gpt_check
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("", login_required(GPTProcessingView.as_view()), name="gpt_processing"),
    path("gpt_process/", gpt_process, name="gpt_process"),
    path("gpt_check/", gpt_check, name="gpt_process_status_check"),
]
