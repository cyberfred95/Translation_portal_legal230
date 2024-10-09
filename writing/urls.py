from django.urls import path
from .views import WritingView, writing_process

urlpatterns = [
    path('', WritingView.as_view(), name='writing'),
    path('process/', writing_process, name='process'),
]