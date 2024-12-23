from django.urls import path
from .views import WritingView, WritingProcessAPIView

urlpatterns = [
    path('', WritingView.as_view(), name='writing'),
    path('process/', WritingProcessAPIView.as_view(), name='process'),
]