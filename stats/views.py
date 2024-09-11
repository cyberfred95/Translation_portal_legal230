from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from preferences import preferences

PORTAL_STATISTIC_URL = "https://statistics.portal.custom.mt/"


# Create your views here.

class GetUserStatsView(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        additional_url_params = self.set_additional_url_params(request)

        response = requests.get(
            PORTAL_STATISTIC_URL + additional_url_params + '&group_admin=true' if self.request.user.group.admin == self.request.user else '',
            headers={
                'token': preferences.MainSettings.STATISTIC_SERVICE_URL
            },
            params={
                "uuid": request.user.uuid
            } if self.request.user.group.admin != self.request.user else None,
        )

        return Response(response.json(), status=status.HTTP_200_OK)

    def set_additional_url_params(self, request):
        date_from = request.data.get("date_from", None)
        date_to = request.data.get("date_to", None)
        additional_url_params = None

        if date_from and date_to:
            additional_url_params = f"date_from={date_from}&date_to={date_to}"
        elif date_from:
            additional_url_params = f"date_from={date_from}"
        elif date_to:
            additional_url_params = f"date_to={date_to}"

        return additional_url_params


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
