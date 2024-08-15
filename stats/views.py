from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response

from stats.models import UserStats
from stats.serializers import UserStatsSerializer


# Create your views here.

class GetUserStatsView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        return UserStats.objects.filter(user=self.request.user)


class GetStatsFromConsole(APIView):
    def get(self, request):
        return Response({'data': ''})
