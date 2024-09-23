from django.urls import path
from django.contrib.auth.decorators import login_required


urlpatterns = [
    path('groups/', login_required(''))
]