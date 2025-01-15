from preferences import preferences
from rest_framework import status
from rest_framework.generics import DestroyAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from glossaries.models import Glossary
from subscriptions.permissions import SubscribedPermission
from .models import UserGroup
from .serializers import GroupSerializer, UserSerializer, ChangePasswordSerializer
from legal.views import PAGINATION_PAGE_SIZE


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
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
        return Response(status=status.HTTP_200_OK)


class DeleteAllDataView(APIView):

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
        user = request.user
        Glossary.objects.filter(user=request.user).delete()
        self.delete_all_projects(user)
        return Response({"message": "All data deleted successfully"}, status=status.HTTP_200_OK)


class SingleAccountView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class InviteUserAPIView(APIView):
    permission_classes = (SubscribedPermission,)

    def post(self, request):
        if request.user.group and request.user.group.admin == request.user:
            emails = request.data.getlist('email[]')
            if not emails:
                return Response({"detail": "Emails list should not be empty"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"detail": "You have to be group admin to provide this action"},
                        status=status.HTTP_403_FORBIDDEN)
