from django.urls import path
from .views import GetUserStatsView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('list/', login_required(GetUserStatsView.as_view()), name='list'),
]