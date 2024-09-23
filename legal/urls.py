from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static, serve
from .views import TranslateView, expert_revision, expert_revision_file, ProjectsHistoryView, SingleProjectView, \
    GetTemplatesView, GetDomainsView, LanguageDetectView, DetectTextLanguageView
from django.contrib.auth.decorators import login_required
from django.conf.urls.i18n import i18n_patterns
from domains.views import update_domains_view

urlpatterns = i18n_patterns(
    path("", login_required(TranslateView.as_view()), name="main_index"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path('gpt-processing/', include('gpt_processing.urls')),
    path("expert-revision", login_required(expert_revision), name='expert_revision'),
    path('expert-revision-file', login_required(expert_revision_file), name='expert_revision_file'),
    path('project-history/', login_required(ProjectsHistoryView.as_view()), name='project_history'),
    path('project/', login_required(SingleProjectView.as_view()), name='single_project'),
    path('get-templates/', login_required(GetTemplatesView.as_view()), name='get-templates'),
    path('get-domains/', login_required(GetDomainsView.as_view()), name='get_domains'),
    path('refresh_domains/', update_domains_view, name='refresh_domains'),
    path('detect_language/', login_required(LanguageDetectView.as_view()), name='detect_language'),
    path('detect_text_language/', login_required(DetectTextLanguageView.as_view()), name='detect_text_language'),
    path('statistics/', include('stats.urls')),
    path('glossaries/', include('glossaries.urls')),
    path('domains/', include('domains.urls')),

    re_path(r'^rosetta/', include('rosetta.urls'))
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) \
              + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
