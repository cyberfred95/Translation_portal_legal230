from django.urls import path
from .views import refesh_prompts_view

urlpatterns = [
    path('refresh/',refesh_prompts_view,name='refresh'),
]