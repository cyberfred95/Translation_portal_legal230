from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from preferences import preferences


# Create your views here.

class GetUserStatsView(APIView):
    def get(self, request):
        print(self.request.user)
        print(request.user.uuid)
        additional_url_params = self.set_additional_url_params(request)

        response = requests.get(
            preferences.StatisticSettings.URL + "statistics_list/" + additional_url_params,
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-Key': preferences.MainSettings.api_key
            },
            json={
                "uuid": str(request.user.uuid)
            }
        )
        return Response(response.json(), status=status.HTTP_200_OK)

    def set_additional_url_params(self, request):
        date_from = request.data.get("date_from", None)
        date_to = request.data.get("date_to", None)
        additional_url_params = ""

        if date_from and date_to:
            additional_url_params += f"?date_from={date_from}&date_to={date_to}"
        elif date_from:
            additional_url_params += f"?date_from={date_from}"
        elif date_to:
            additional_url_params += f"?date_to={date_to}"
        if request.user.group.admin != request.user:
            additional_url_params += "&group_admin=true"

        return additional_url_params
