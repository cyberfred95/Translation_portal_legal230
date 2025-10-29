import base64
import re
from datetime import datetime, timedelta
from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth import login
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.templatetags.static import static
from django.urls import reverse
from django.views.generic import TemplateView
from django.conf import settings


class BaseTemplateView(TemplateView):
    """
    Base TemplateView that adds environment variables to context
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SUPPORT_EMAIL'] = settings.SUPPORT_EMAIL
        context['SENDER_EMAIL'] = settings.SENDER_EMAIL
        context['QUOTE_CC_EMAIL'] = settings.QUOTE_CC_EMAIL
        return context
from django.utils.translation import gettext_lazy as _

from preferences import preferences
from rest_framework import status, serializers
from rest_framework.generics import DestroyAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from glossaries.models import Glossary
from subscriptions.models import SubscriptionType, UserSubscription
from subscriptions.permissions import SubscribedPermission
from subscriptions.utils import get_user_api_key
from .models import UserGroup, User
from .serializers import GroupSerializer, UserSerializer, ChangePasswordSerializer, RegisterUserSerializer, \
    LoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from legal.views import PAGINATION_PAGE_SIZE
from legal.helpers import password_valid

from emails.models import EmailType
from emails.send_email import send_email


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

    @staticmethod
    def delete_all_projects(user):
        params = {
            "page_size": PAGINATION_PAGE_SIZE,
            "user_custom_mt_token": user.uuid if not user.is_staff else None
        }
        
        # Resolve API key based on user subscription
        try:
            user_api_key = get_user_api_key(user)
        except ValueError:
            print("no subscription")
            return  # Exit early if no subscription found
            
        headers = {"token": user_api_key}

        response = requests.get(settings.CLOUDSTORAGE_API_URL, params=params, headers=headers).json()
        num_pages = response.get('num_pages')
        page = 1
        while page < num_pages:
            params['page'] = page
            response = requests.get(
                settings.CLOUDSTORAGE_API_URL,
                params=params,
                headers=headers,
            ).json()
            if 'results' in response:
                for project in response['results']:
                    requests.delete(
                        settings.CLOUDSTORAGE_API_URL + f"{project['id']}/",
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

    def validate(self, attrs):
        if not attrs['username'] or not attrs['email']:
            raise serializers.ValidationError({"detail": _("Username and email are required.")})
        if (User.objects.filter(username=attrs['username']).exists()
                and self.request.user.username != attrs['username']):
            raise serializers.ValidationError({"detail": _("This username is already used.")})
        if (User.objects.filter(email=attrs['email']).exists()
                and self.request.user.email != attrs['email']):
            raise serializers.ValidationError({"detail": _("This email is already used.")})
        return attrs

    def put(self, request, *args, **kwargs):
        self.validate(request.data)
        user = request.user
        user.username = request.data['username']
        user.email = request.data['email']
        user.first_name = request.data.get('first_name', user.first_name)
        user.last_name = request.data.get('last_name', user.last_name)
        
        # Mettre à jour la langue de préférence de l'utilisateur
        if 'language' in request.data:
            user.language = request.data['language']
            # Mettre à jour aussi la langue de session pour l'interface actuelle
            from django.utils import translation
            translation.activate(request.data['language'])
            request.session[translation.LANGUAGE_SESSION_KEY] = request.data['language']
        
        user.save()
        return Response(UserSerializer(user).data, status=status.HTTP_200_OK)

    def get_object(self):
        return self.request.user

    def delete(self, request, *args, **kwargs):
        if password_valid(request):
            return super().delete(request, *args, **kwargs)
        else:
            return Response({"detail": "Invalid password"}, status=status.HTTP_403_FORBIDDEN)


class InviteUserAPIView(APIView):
    permission_classes = (SubscribedPermission,)

    @staticmethod
    def is_email_valid(email: str):
        pattern = r'^[\w\.-]+@[a-zA-Z\d\.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def post(self, request):
        if request.user.group and request.user in request.user.group.admin.all():
            emails = request.data.get('emails', [])
            if isinstance(emails, str):
                emails = emails.split(',')
                emails = list(set(emails))
            if not emails:
                return Response({"detail": "Emails list should not be empty"}, status=status.HTTP_400_BAD_REQUEST)
            if not request.data.get('subscription_type_id'):
                return Response({"detail": "Subscription type is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not SubscriptionType.objects.filter(id=int(request.data.get('subscription_type_id', 0))).exists():
                return Response({"detail": "Invalid subscription type"}, status=status.HTTP_400_BAD_REQUEST)
            for email in emails:
                if self.is_email_valid(email):
                    params = {
                        "email": base64.b64encode(email.encode('utf-8')),
                        "group": base64.b64encode(str(request.user.group.id).encode('utf-8')),
                        "subscription_type_id": base64.b64encode(request.data.get('subscription_type_id').encode('utf-8')),
                    }
                    send_email(
                        email,
                        EmailType.USER_MANAGEMENT_INVITATION,
                        request.user.language,
                        {
                            # TMP : Need to be replaced with actual values when figma integration is done
                            "lexa_username": "name",
                            "lexa_email": user.email,
                            "url_reset_password" : self.get_register_user_absolute_uri(request, params=params),
                        }
                    )
            return Response({"message": "Invitation has been successfully sent"}, status=status.HTTP_200_OK)
        return Response({"detail": "You have to be group admin to provide this action"},
                        status=status.HTTP_403_FORBIDDEN)

    @staticmethod
    def get_register_user_absolute_uri(request, params: dict = None):
        url = f"{request.build_absolute_uri(reverse('register-user'))}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url


class RegisterUserView(BaseTemplateView):
    template_name = 'registration/register.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('email'):
            context["email"] = base64.b64decode(self.request.GET.get('email')).decode('utf-8')
        if self.request.GET.get('group'):
            context["group"] = base64.b64decode(self.request.GET.get('group')).decode('utf-8')
        if self.request.GET.get('subscription_type_id'):
            context["subscription_type_id"] = base64.b64decode(self.request.GET.get('subscription_type_id')).decode(
                'utf-8')
        return context

    def post(self, request, *args, **kwargs):
        if not request.POST.get('subscription_type_id'):
            return JsonResponse({"detail":"Subscription type is required"}, status=status.HTTP_400_BAD_REQUEST)
        subscription_type = SubscriptionType.objects.get(id=int(request.POST.get('subscription_type_id', 0)))
        if not subscription_type:
            return JsonResponse({"detail": "Invalid subscription type"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = RegisterUserSerializer(data=request.POST)
        if serializer.is_valid():
            with transaction.atomic():
                user = serializer.create(serializer.validated_data)
                user_subscription = UserSubscription.objects.create(
                    user=user,
                    subscription=subscription_type,
                    status=UserSubscription.UserSubscriptionChoices.ACTIVE,
                    start_date=datetime.now(),
                    end_date = datetime.now() + timedelta(days=30)
                )
                user_subscription.save()
                login(request, user)
                return redirect(settings.LOGIN_REDIRECT_URL)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(BaseTemplateView):
    template_name = 'registration/login.html'

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=self.request.POST)
        if serializer.is_valid():
            user = User.objects.filter(email=self.request.POST.get('email')).first()
            login(request, user)
            return redirect(settings.LOGIN_REDIRECT_URL)
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ForgotPasswordView(BaseTemplateView):
    template_name = 'registration/forgot_password.html'

    def post(self, request, *args, **kwargs):
        serializer = ForgotPasswordSerializer(data=self.request.POST)
        if serializer.is_valid():
            user = User.objects.filter(email=self.request.POST.get('email')).first()

            params = {
                "email": base64.b64encode(user.email.encode('utf-8')),
            }
            send_email(
                email,
                EmailType.USER_MANAGEMENT_RESET_PASSWORD,
                request.user.language,
                {
                    # TMP : Need to be replaced with actual values when figma integration is done
                    "lexa_username": user.username,
                    "lexa_email": user.email,
                    "url_reset_password": self.get_register_user_absolute_uri(request, params=params),
                }
            )
            return JsonResponse({"message": "Code sent successfully"}, status=status.HTTP_200_OK)
        else:
            return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def get_reset_password_absolute_url(request, params: dict = None) -> str:
        url = f"{request.build_absolute_uri(reverse('reset-password'))}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url


class ResetPasswordView(BaseTemplateView):
    template_name = 'registration/reset_password.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.GET.get('email'):
            context["email"] = base64.b64decode(self.request.GET.get('email')).decode('utf-8')
        return context

    def post(self, request, *args, **kwargs):
        serializer = ResetPasswordSerializer(data=self.request.POST)
        if serializer.is_valid():
            serializer.save()
            return redirect(reverse('login'))
        return JsonResponse(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
