from django.conf.urls import url, include
from django.contrib import admin
from django.urls import path, re_path
from django.conf import settings
from django.conf.urls.static import static
from .views import TranslateView, FileExpertRevisionView, ProjectsHistoryView, SingleProjectView, \
     GetTemplatesView, GetDomainsView, LanguageDetectView, DetectTextLanguageView, ProfileDetailsView, DashboardView, TextTranslate2View
from django.contrib.auth.decorators import login_required
from django.conf.urls.i18n import i18n_patterns
from domains.views import update_domains_view
from writing.views import refresh_prompts_view

urlpatterns = i18n_patterns(
    path("", login_required(TranslateView.as_view()), name="main_index"),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    
    path('dashboard/', login_required(DashboardView.as_view()),
         name='dashboard'),
    path('translate-2/', login_required(TextTranslate2View.as_view()),
         name='translate_2'),
    path('expert-revision-file', login_required(FileExpertRevisionView.as_view()),
         name='expert_revision_file'),
    path('project-history/', login_required(ProjectsHistoryView.as_view()),
         name='project_history'),
    path('project/', login_required(SingleProjectView.as_view()),
         name='single_project'),
    path('get-templates/', login_required(GetTemplatesView.as_view()),
         name='get-templates'),
    path('get-domains/', login_required(GetDomainsView.as_view()), name='get_domains'),
    path('profile-details/', login_required(ProfileDetailsView.as_view()),
         name='profile_details'),

    path('refresh_domains/', update_domains_view, name='refresh_domains'),
    path('refresh_prompts/', refresh_prompts_view, name='refresh_prompts'),

    path('detect_language/', login_required(LanguageDetectView.as_view()),
         name='detect_language'),
    path('detect_text_language/', login_required(DetectTextLanguageView.as_view()),
         name='detect_text_language'),

    path('statistics/', include('stats.urls')),
    path('glossaries/', include('glossaries.urls')),
    path('domains/', include('domains.urls')),
    path('usage/', include('stats.urls')),
    path('users/', include('users.urls')),
    path('writing/', include('writing.urls')),
    path('quoting/', include('quoting.urls')),

    re_path(r'^rosetta/', include('rosetta.urls'))
) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

urlpatterns += [
     path("stripe/", include('stripe_webhooks.urls')),
     path("api/", include('api.urls')),
]
