from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static, serve
from .views import TranslateView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path("", login_required(TranslateView.as_view()), name="main_index"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('gpt-processing/', include('gpt_processing.urls')),
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
