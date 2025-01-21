import base64
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.http import JsonResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import TemplateView
from preferences import preferences
from rest_framework import status, serializers
from rest_framework.generics import DestroyAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from glossaries.models import Glossary
from subscriptions.permissions import SubscribedPermission
from .models import UserGroup, User, ResetPasswordCode
from .serializers import GroupSerializer, UserSerializer, ChangePasswordSerializer, RegisterUserSerializer, \
    LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from legal.views import PAGINATION_PAGE_SIZE
from .mail_helpers import send_invitation_email, send_reset_password_code, register_success_email
from legal.helpers import password_valid


# Create your views here.

class UsersListView(APIView):
    def get(self, request):
        if request.user.is_staff:
            return Response(GroupSerializer(UserGroup.objects.all(), many=True).data, status=status.HTTP_200_OK)
        if request.user.group:
            if request.user.group.admin and request.user.group.admin == request.user:
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

    @staticmethod
    def delete_all_projects(user):
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        headers = {"token": preferences.MainSettings.api_key if user.is_staff else user.group.api_key}

        response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        num_pages = response.get('num_pages')
        page = 1
        while page < num_pages:
            params['page'] = page
            response = requests.get(
                preferences.MainSettings.CLOUDSTORAGE_API_URL,
                params=params,
                headers=headers,
            ).json()
            if 'results' in response:
                for project in response['results']:
                    requests.delete(
                        preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project['id']}/",
                        headers=headers,
                    )

    def post(self, request):
        if password_valid(request):
            user = request.user
            Glossary.objects.filter(user=request.user).delete()
            self.delete_all_projects(user)
            return Response({"message": "All data deleted successfully"}, status=status.HTTP_200_OK)
        return Response({"detail": "invalid password"}, status=status.HTTP_403_FORBIDDEN)


class SingleAccountView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        if password_valid(request):
            return super().delete(request, *args, **kwargs)
        else:
            return Response({"detail": "Invalid password"}, status=status.HTTP_403_FORBIDDEN)


class InviteUserAPIView(APIView):
    permission_classes = (SubscribedPermission,)

    def post(self, request):
        if request.user.group and request.user.group.admin == request.user:
            emails = request.data.get('emails', [])
            if isinstance(emails, str):
                emails = emails.split(',')
            if not emails:
                return Response({"detail": "Emails list should not be empty"}, status=status.HTTP_400_BAD_REQUEST)
            for email in emails:
                params = {
                    "email": base64.b64encode(email.encode('utf-8')),
                    "group": base64.b64encode(str(request.user.group.id).encode('utf-8')),
                }
                send_invitation_email(email=email,
                                      register_user_absolute_uri=self.get_register_user_absolute_uri(request,
                                                                                                     params=params))
            return Response({"message": "Invitation has been successfully sent"}, status=status.HTTP_200_OK)
        return Response({"detail": "You have to be group admin to provide this action"},
                        status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def get_register_user_absolute_uri(request, params: dict = None):
        url = f"{request.build_absolute_uri(reverse('register-user'))}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url


class RegisterUserView(TemplateView):
    template_name = 'registration/register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('email'):
            context["email"] = base64.b64decode(self.request.GET.get('email')).decode('utf-8')
        if self.request.GET.get('group'):
            context["group"] = base64.b64decode(self.request.GET.get('group')).decode('utf-8')
        return context

    def post(self, request, *args, **kwargs):
        serializer = RegisterUserSerializer(data=request.POST)
        if serializer.is_valid():
            user = serializer.create(serializer.validated_data)
            login(request, user)
            register_success_email(
                username=user.username,
                email=user.email,
                password=request.POST.get('password'),
                logo_url=request.build_absolute_uri(static('images/logo.png')),
            )
            return redirect(settings.LOGIN_REDIRECT_URL)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(TemplateView):
    template_name = 'registration/login.html'

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=self.request.POST)
        if serializer.is_valid():
            user = User.objects.filter(email=self.request.POST.get('email')).first()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(TemplateView):
    template_name = 'registration/forgot_password.html'

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=self.request.POST)
        if serializer.is_valid():
            user = User.objects.filter(email=self.request.POST.get('email')).first()
            send_reset_password_email(email=user.email)
            return JsonResponse({"message": "Code sent successfully"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordView(TemplateView):
    template_name = 'registration/reset_password.html'

    def post(self, request, *args, **kwargs):