from django.urls import path
from django.contrib.auth.decorators import login_required
from .views import UsersListView, DeleteAllDataView, SingleAccountView, ChangePasswordView, InviteUserAPIView, \
    RegisterUserView, LoginView, ForgotPasswordView

urlpatterns = [
    path('', login_required(UsersListView.as_view()), name='groups'),
    path('delete-all-data/', DeleteAllDataView.as_view(), name='delete_all_data'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('<int:id>/', SingleAccountView.as_view(), name='user'),
    path('register/', RegisterUserView.as_view(), name='register-user'),
    path('invite/', login_required(InviteUserAPIView.as_view()), name='invite-user'),
    path('login/', LoginView.as_view(), name='login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
]
