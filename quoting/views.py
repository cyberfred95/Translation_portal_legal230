import os

import requests
from django.urls import reverse
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from subscriptions.permissions import SubscribedPermission
from .helpers import get_price_by_language_pair
from preferences import preferences
from legal.helpers import get_project_file, get_text_from_file
from .mail_helpers import send_quote_email
from urllib.parse import urlencode


# Create your views here.

class FormQuoteView(APIView):
    permission_classes = (IsAuthenticated, SubscribedPermission)

    @staticmethod
    def get_expert_revision_url(project_id, request):
        params = {
            'project_id': project_id,
        }
        return f"{request.build_absolute_uri(reverse('expert_revision_file'))}?{urlencode(params)}"

    def post(self, request):
        project_id = request.data.get('project_id')
        if not project_id:
            return Response({"message": "project id must be set"}, status=status.HTTP_400_BAD_REQUEST)
        response = requests.get(preferences.MainSettings.CLOUDSTORAGE_API_URL + f"{project_id}/",
                                headers={
                                    "token": preferences.MainSettings.api_key if request.user.is_staff else request.user.group.api_key})
        if response.status_code != status.HTTP_200_OK:
            return Response({"message": "Error in request"}, status=status.HTTP_400_BAD_REQUEST)
        project = response.json()
        quote_price = get_price_by_language_pair(source_language=project['source_language'],
                                                 target_language=project['target_language'])
        file = get_project_file(file_url=project['source_file'])
        words_count = len(get_text_from_file(file, api_key=None))
        if quote_price:
            context_variables = {

                "email": preferences.MainSettings.sender_email,
                "username": request.user.username,
                "user_email": request.user.email,
                "company": request.user.group.name if request.user.group else "Administrator",
                'contract_name': self.request.data.get('company',
                                                       request.user.group.name if request.user.group else "Administrator"),
                'file_name': file.name,
                'word_price': quote_price.price,
                'words_count': words_count,
                'total_price': words_count * quote_price.price,
                'created_at': now(),
                'expert_revision_file_absolute_url': self.get_expert_revision_url(project_id, request),
                'quote_number': request.user.group.generate_quoting_number() if request.user.group else f"{now().strftime('%Y/%m')}/0"

            }
            send_quote_email(request.user.id, context_variables)

        return Response({"message": "Quote sent successfully"}, status=status.HTTP_200_OK)
