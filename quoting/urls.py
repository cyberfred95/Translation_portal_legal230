from django.urls import path
from .views import *

urlpatterns = [
    path('form/', FormQuoteView.as_view(), name='form'),
]