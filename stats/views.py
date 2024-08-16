from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from stats.models import UserStats
from stats.serializers import UserStatsSerializer
from preferences import preferences


# Create your views here.

class GetUserStatsView(ListAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserStatsSerializer

    def get_queryset(self):
        return UserStats.objects.filter(user=self.request.user)


class GetStatsFromConsole(APIView):
    def post(self, request):
        response = requests.post(
            'https://console.custom.mt/get_statistics_by_api_key/',
            headers={
                'token': preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key
            },
            data={
                'date_from': request.data['date_from'],
                'date_to': request.data['date_to'],
            }
        )
        return Response({'data': response.json()})
