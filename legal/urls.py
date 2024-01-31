from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static, serve
from .views import TranslateView, expert_revision, expert_revision_file, ProjectsHistoryView, SingleProjectView
from django.contrib.auth.decorators import login_required
from django.conf.urls.i18n import i18n_patterns

urlpatterns = i18n_patterns(
    path("", login_required(TranslateView.as_view()), name="main_index"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('gpt-processing/', include('gpt_processing.urls')),
    path("expert-revision", login_required(expert_revision), name='expert_revision'),
    path('expert-revision-file', login_required(expert_revision_file), name='expert_revision_file'),
    path('project-history/', login_required(ProjectsHistoryView.as_view()), name='project_history'),
    path('project/', login_required(SingleProjectView.as_view()), name='single_project'),
    re_path(r'^rosetta/', include('rosetta.urls'))
)+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)\
+ static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
