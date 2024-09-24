from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import UserGroup
from .serializers import GroupSerializer, UserSerializer


# Create your views here.

class UsersListView(APIView):
    def get(self, request):
        if request.user.is_staff:
            return Response(GroupSerializer(UserGroup.objects.all(), many=True).data, status=status.HTTP_200_OK)
        if request.user.group:
            if request.user.group.admin and request.user.group.admin == request.user:
                return Response(GroupSerializer(request.user.group).data)
            return Response(UserSerializer(request.user))

        return Response({"message": "You have to be in group"}, status=status.HTTP_403_FORBIDDEN)
