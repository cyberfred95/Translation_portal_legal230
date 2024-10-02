from django.urls import path
from .views import WritingView

urlpatterns = [
    path('', WritingView.as_view(), name='writing'),
]