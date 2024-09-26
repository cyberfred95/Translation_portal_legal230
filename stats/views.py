from datetime import datetime

import requests
from preferences import preferences
from django.views.generic import TemplateView
from legal.views import PAGINATION_PAGE_SIZE
from users.models import User, UserGroup


# Create your views here.


class UsageView(TemplateView):
    template_name = 'usage_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['stats'] = self.get_stats()
        context['date_from'] = self.request.GET.get("date_from", "")
        context['date_to'] = self.request.GET.get("date_to", "")
        
        return context

    def get_stats(self):
        additional_url_params = self.set_additional_url_params()

        response = requests.get(
            preferences.StatisticSettings.URL + "statistics_list/" + additional_url_params,
            headers={
                'token': preferences.StatisticSettings.API_KEY,
                'X-API-Key': preferences.MainSettings.api_key
            },
            json={
                "uuid": str(self.request.user.uuid)
            }
        )

        stats = dict(response.json())
        
        unique_file_names = set()
        unique_user_file_names = {}

        for stat in stats['results']:
            user = User.objects.filter(uuid=stat.get('user_portal_uuid')).first()
            stat['user'] = user.username if user else 'Unknown'

            stat['created_at'] = datetime.fromisoformat(stat['created_at'].replace('Z', '+00:00'))

            try:
                stat['group'] = user.group.name
            except:
                stat['group'] = 'Unknown'

            stat.pop('portal_name')
            stat.pop('user_portal_uuid')

            if user:
                if user.username not in unique_user_file_names:
                    unique_user_file_names[user.username] = set()
                unique_user_file_names[user.username].add(stat['file_name'])

            unique_file_names.add(stat['file_name'])

        stats['total_count'] = self.calculate_total_chars_and_tokens(stats)

        if self.request.user.is_superuser or (self.request.user.group and self.request.user.group.admin == self.request.user):
            stats['filters'] = {
                'users': [user.username for user in User.objects.all()],  
                'groups': [group.name for group in UserGroup.objects.all()],  
                'file_name': list(unique_file_names),  
            }
        else:
            stats['filters'] = {
                'file_name': list(unique_user_file_names.get(self.request.user.username, set())),
            }

        print(f"Filters for user {self.request.user.username}: {stats['filters']}")
  
        return stats

    def calculate_total_chars_and_tokens(self, stats):
        total_chars = 0
        total_tokens = 0
        for stat in stats['results']:
            total_chars += stat['chars_count']
            total_tokens += stat['tokens_count']
        return {
            "chars": total_chars,
            "tokens": total_tokens,
        }

    def set_additional_url_params(self):
        date_from = self.request.GET.get("date_from", None)
        date_to = self.request.GET.get("date_to", None)
        additional_url_params = f"?page_size={PAGINATION_PAGE_SIZE}"

        if date_from and date_to:
            additional_url_params += f"&date_from={date_from}&date_to={date_to}"
        elif date_from:
            additional_url_params += f"&date_from={date_from}"
        elif date_to:
            additional_url_params += f"&date_to={date_to}"

        if self.request.user.is_superuser or (self.request.user.group and self.request.user.group.admin == self.request.user):
            additional_url_params += "&group_admin=true"

        return additional_url_params
