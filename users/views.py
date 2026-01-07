import base64
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView
from rest_framework import serializers, status
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from emails.models import EmailType
from emails.send_email import send_email
from glossaries.models import Glossary
from legal.helpers import password_valid

from .models import UserGroup, User
from .serializers import (
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    GroupSerializer,
    LoginSerializer,
    ResetPasswordSerializer,
    UserSerializer,
)


class BaseTemplateView(TemplateView):
    """Base TemplateView that adds environment variables to context."""
    
    def get_context_data(self, **kwargs):
        """Add environment variables to template context."""
        context = super().get_context_data(**kwargs)
        context['SUPPORT_EMAIL'] = settings.SUPPORT_EMAIL
        context['SENDER_EMAIL'] = settings.SENDER_EMAIL
        context['QUOTE_CC_EMAIL'] = settings.QUOTE_CC_EMAIL
        return context


class UsersListView(APIView):
    def get(self, request):
        if request.user.is_staff:
            return Response(GroupSerializer(UserGroup.objects.all(), many=True).data, status=status.HTTP_200_OK)
        if request.user.group:
            if request.user in request.user.group.admin.all():
                return Response(GroupSerializer(request.user.group).data)
            return Response(UserSerializer(request.user))

        return Response({"detail": "You have to be in group"}, status=status.HTTP_403_FORBIDDEN)


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=self.request.POST, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "password changed successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAllDataView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if password_valid(request):
            user = request.user
            Glossary.objects.filter(user=request.user).delete()
            # Note: Suppression des projets CloudStorage désactivée (service non disponible)
            return Response({"message": "All data deleted successfully"}, status=status.HTTP_200_OK)
        return Response({"detail": "invalid password"}, status=status.HTTP_403_FORBIDDEN)


class SingleAccountView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    @staticmethod
    def _get_update_service():
        """Retourne le service de mise à jour (import lazy pour éviter les imports circulaires)."""
        from .services.user_update import UserUpdateService
        return UserUpdateService

    def validate(self, attrs):
        """Valide les données utilisateur. Ne valide que les champs présents dans attrs."""
        update_service = self._get_update_service()
        errors = update_service.validate_fields(attrs, self.request.user)
        
        if errors:
            error_message = _("; ").join(errors.values())
            raise serializers.ValidationError({"detail": error_message})
        
        return attrs

    def put(self, request, *args, **kwargs):
        """Met à jour les champs de l'utilisateur fournis dans la requête."""
        update_service = self._get_update_service()
        user = request.user
        data = request.data
        
        # Valider les champs
        validation_errors = update_service.validate_fields(data, user)
        if validation_errors:
            return self._error_response(_("; ").join(validation_errors.values()))
        
        # Mettre à jour l'utilisateur
        error, period_reduced = update_service.update_user(user, data, request)
        if error:
            return self._error_response(_(error))
        
        user.save()
        
        # Déclencher le nettoyage si la période a été réduite
        update_service.trigger_cleanup_if_needed(user, period_reduced)
        
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)
    
    def _error_response(self, message: str) -> Response:
        """Retourne une réponse d'erreur standardisée."""
        return Response(
            {"detail": message},
            status=status.HTTP_400_BAD_REQUEST
        )

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        if password_valid(request):
            return super().delete(request, *args, **kwargs)
        else:
            return Response({"detail": "Invalid password"}, status=status.HTTP_403_FORBIDDEN)


class LoginView(BaseTemplateView):
    template_name = 'registration/login.html'

    @staticmethod
    def _format_errors(errors):
        messages = []
        for field, details in errors.items():
            if isinstance(details, (list, tuple)):
                messages.extend([str(message) for message in details])
            else:
                messages.append(str(details))
        return messages

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=self.request.POST)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.filter(email__iexact=email).first()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        error_messages = self._format_errors(serializer.errors)
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            detail = error_messages[0] if error_messages else _("An unknown error occurred.")
            return JsonResponse({"detail": detail}, status=status.HTTP_400_BAD_REQUEST)
        context = self.get_context_data(**kwargs)
        context['form_data'] = request.POST
        context['error_messages'] = error_messages
        return self.render_to_response(context, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(BaseTemplateView):
    template_name = 'registration/forgot_password.html'

    @staticmethod
    def _build_reset_password_url(request, email: str) -> str:
        """Build absolute URL for password reset with encoded email parameter."""
        params = {"email": base64.b64encode(email.encode('utf-8')).decode('utf-8')}
        url = request.build_absolute_uri(reverse('reset-password'))
        return f"{url}?{urlencode(params)}"

    def _send_reset_password_email(self, user: User, request):
        """Send password reset email to user."""
        send_email(
            user.email,
            EmailType.USER_MANAGEMENT_RESET_PASSWORD,
            user.language or 'en',
            {
                "lexa_username": user.username,
                "lexa_email": user.email,
                "url_reset_password": self._build_reset_password_url(request, user.email),
            }
        )

    def post(self, request, *args, **kwargs):
        """Handle forgot password request."""
        serializer = ForgotPasswordSerializer(data=request.POST)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = request.POST.get('email')
        user = User.objects.filter(email=email).first()

        if user:
            self._send_reset_password_email(user, request)

        # Always return success to prevent email enumeration
        return JsonResponse({"message": "Code sent successfully"}, status=status.HTTP_200_OK)


class ResetPasswordView(BaseTemplateView):
    template_name = 'registration/reset_password.html'

    def get_context_data(self, **kwargs):
        """Add decoded email to context if present in query parameters."""
        context = super().get_context_data(**kwargs)
        encoded_email = self.request.GET.get('email')
        if encoded_email:
            try:
                context["email"] = base64.b64decode(encoded_email).decode('utf-8')
            except (ValueError, UnicodeDecodeError):
                # Invalid base64 or encoding, ignore
                pass
        return context

    def post(self, request, *args, **kwargs):
        """Handle password reset request."""
        serializer = ResetPasswordSerializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            return redirect(reverse('login'))
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
