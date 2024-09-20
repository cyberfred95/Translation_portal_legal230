from django.urls import path
from django.contrib.auth.decorators import login_required

from domains.views import DomainListView

urlpatterns = [
    path('domain_groups/', login_required(DomainListView.as_view()), name='domain-list'),
]
