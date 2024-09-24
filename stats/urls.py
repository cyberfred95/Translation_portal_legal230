from django.urls import path

from .views import UsageView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(UsageView.as_view()), name='usage'),
]