from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import WritingView, WritingProcessAPIView

urlpatterns = [
    path('', login_required(WritingView.as_view()), name='writing'),
    path('process/', login_required(WritingProcessAPIView.as_view()), name='process'),
]