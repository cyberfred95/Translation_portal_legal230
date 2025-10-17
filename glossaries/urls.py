from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import SingleGlossaryView, AddGlossaryView, UserGlossariesView, UserGlossariesView2, GlossariesListAPIView, GetDefaultGlossaryView

urlpatterns = [
    path('', login_required(UserGlossariesView.as_view()), name='glossaries'),
    path('2/', login_required(UserGlossariesView2.as_view()), name='glossaries_2'),
    path('add/', login_required(AddGlossaryView.as_view()), name='add_glossary'),
    path('<int:pk>/', login_required(SingleGlossaryView.as_view()), name='single_glossary'),
    path('api/list/', login_required(GlossariesListAPIView.as_view()), name='api_list_glossaries'),
    path('api/default_glossary/', login_required(GetDefaultGlossaryView.as_view()), name='get_default_glossary')
]

