from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import (
    UsersListView,
    DeleteAllDataView,
    SingleAccountView,
    ChangePasswordView,
    LoginView,
    ForgotPasswordView,
    ResetPasswordView,
    SaveInstructionsView,
    GetSavedInstructionsView,
)

urlpatterns = [
    path('', login_required(UsersListView.as_view()), name='groups'),
    path('delete-all-data/', login_required(DeleteAllDataView.as_view()), name='delete_all_data'),
    path('change-password/', login_required(ChangePasswordView.as_view()), name='change_password'),
    path('<int:id>/', login_required(SingleAccountView.as_view()), name='user'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    # Instructions de traduction
    path('save-instructions/', login_required(SaveInstructionsView.as_view()), name='save_instructions'),
    path('get-saved-instructions/', login_required(GetSavedInstructionsView.as_view()), name='get_saved_instructions'),
]
