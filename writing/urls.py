from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import WritingView, WritingProcessAPIView, Writing2View

urlpatterns = [
    path('', login_required(WritingView.as_view()), name='writing'),
    path('writing_2/', login_required(Writing2View.as_view()), name='writing_2'),
    path('process/', login_required(WritingProcessAPIView.as_view()), name='process'),
]