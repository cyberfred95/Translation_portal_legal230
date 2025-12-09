# ============================================================================
# WRITING FUNCTIONALITY - TEMPORARILY DISABLED
# ============================================================================
# Cette fonctionnalité est temporairement désactivée en prévision d'une refonte.
# Tout le code est conservé en commentaire pour référence future.
# ============================================================================

from django.contrib.auth.decorators import login_required
from django.urls import path
from .views import WritingView
# from .views import WritingProcessAPIView  # COMMENTED - Feature disabled

urlpatterns = [
    path('', login_required(WritingView.as_view()), name='writing'),
    # path('process/', login_required(WritingProcessAPIView.as_view()), name='process'),  # COMMENTED - Feature disabled
]