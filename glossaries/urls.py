from django.urls import path
from .views import SingleGlossaryView, AddGlossaryView, UserGlossariesView

urlpatterns = [
    path('', UserGlossariesView.as_view(), name='glossaries'),
    path('add/', AddGlossaryView.as_view(), name='add_glossary'),
    path('<int:pk>/', SingleGlossaryView.as_view(), name='single_glossary'),
]