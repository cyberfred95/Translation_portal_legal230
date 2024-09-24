from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import UsersListView


urlpatterns = [
    path('', login_required(UsersListView.as_view()), name='groups'),
]