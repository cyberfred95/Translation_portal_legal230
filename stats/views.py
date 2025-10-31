import json
from datetime import datetime, date, timedelta
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

import requests
from preferences import preferences
from legal.views_all import PAGINATION_PAGE_SIZE
from users.models import User, UserGroup
from django.conf import settings
from subscriptions.utils import get_user_api_key


# Create your views here.


class UsageView(BaseTemplateView):
    template_name = 'usage_history.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data()
        context['stats'] = self.get_stats()
        context['stats']['filters'] = self.get_filters()
        context['date_from'] = self.request.GET.get("date_from", date.today())
        context['date_to'] = self.request.GET.get(
            "date_to", date.today() + timedelta(days=30))
        context['is_group_admin'] = self.get_is_group_admin()

        return context

    def get_is_group_admin(self):
        return self.request.user.group and self.request.user in self.request.user.group.admin.all()

    def get_filters(self):

        def get_responses():
            additional_url_params = self.set_additional_url_params(
                exclude_page_param=True)

            responses = []
            try:
                user_api_key = get_user_api_key(self.request.user)
            except ValueError:
                # En cas d'absence de subscription, retourner des réponses vides
                return []
            response = requests.get(
                settings.STATS_API_URL + "statistics_list/" + additional_url_params,
                headers={
                    'token': settings.STATS_API_KEY,
                    'X-API-Key': user_api_key
                },
                json={
                    "uuid": self.get_users(),
                }
            )
            responses.append(response)
            if response.json().get('num_pages', 0) > 1:
                for page in range(1, int(response.json().get('num_pages'))):
                    responses.append(
                        requests.get(
                            settings.STATS_API_URL + "statistics_list/" +
                            additional_url_params + f"&page={page}",
                            headers={
                                'token': settings.STATS_API_KEY,
                                'X-API-Key': user_api_key
                            },
                            json={
                                "uuid": self.get_users(),
                            }
                        )
                    )
            return list(set(responses))

        responses = get_responses()

        file_names = []
        for response in responses:
            for usage in response.json().get('results', []):
                file_names.append(usage['file_name'])

        file_names = list(set(file_names))

        if self.request.user.is_staff:
            return {
                'users': [user.username for user in User.objects.all()],
                'groups': [group.name for group in UserGroup.objects.all()],
                'file_name': file_names,
            }
        elif self.request.user.group and self.request.user in self.request.user.group.admin.all():
            return {
                'users': [user.username for user in User.objects.filter(group=self.request.user.group)],
                'file_name': file_names,
            }
        else:
            return {
                'file_name': file_names,
            }

    def get_users(self) -> list:
        group_user_uuids = []
        # get all users in groups
        if self.request.user.is_staff:
            group_names = self.request.GET.getlist('group', [])
            users = User.objects.filter(group__name__in=group_names)
            group_user_uuids = [str(user.uuid) for user in users]

        # get all users in dediсated group
        if self.request.user.is_staff or (
                self.request.user.group and self.request.user in self.request.user.group.admin.all()):
            if self.request.user.group:
                user_names = self.request.GET.getlist('user', User.objects.filter(
                    group__id=self.request.user.group.id).values_list('username', flat=True))
            else:
                user_names = self.request.GET.getlist('user', [])
            users = User.objects.filter(username__in=user_names)
            user_uuids = [str(user.uuid) for user in users]

            if self.request.user.is_staff:
                user_uuids = list(set(user_uuids + group_user_uuids))
            return user_uuids

        return [str(self.request.user.uuid)]

    def prepare_stats(self, stats: dict) -> dict:
        unique_file_names = set()
        unique_user_file_names = {}

        for stat in stats['results']:
            user = User.objects.filter(
                uuid=stat.get('user_portal_uuid')).first()
            stat['user'] = user.username if user else 'Unknown'
            try:
                stat['metadata'] = json.loads(stat['metadata'])
            except:
                pass
            stat['created_at'] = datetime.fromisoformat(
                stat['created_at'].replace('Z', '+00:00'))

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

        return stats

    def get_stats(self) -> dict:
        files = self.request.GET.getlist('file_name', [])
        additional_url_params = self.set_additional_url_params()
        try:
            user_api_key = get_user_api_key(self.request.user)
        except ValueError:
            # En cas d'absence de subscription, retourner des stats vides
            return {'results': [], 'total_count': {'chars': 0, 'tokens': 0, 'words': 0}}
        response = requests.get(
            settings.STATS_API_URL + "statistics_list/" + additional_url_params,
            headers={
                'token': settings.STATS_API_KEY,
                'X-API-Key': user_api_key
            },
            json={
                "uuid": self.get_users(),
                "file_name": files
            }
        )
        stats = dict(response.json())
        return self.prepare_stats(stats)

    @staticmethod
    def calculate_total_chars_and_tokens(stats) -> dict:
        total_chars = 0
        total_tokens = 0
        words_count = 0
        for stat in stats['results']:
            total_chars += stat['chars_count']
            total_tokens += stat['tokens_count']
            total_tokens += stat['tokens_out_count']
            if stat['metadata'] and stat['metadata']['words_count']:
                words_count += stat['metadata']['words_count']
        return {
            "chars": total_chars,
            "tokens": total_tokens,
            "words": words_count,
        }

    def set_additional_url_params(self, exclude_page_param=False) -> str:
        params = {
            'date_from': self.request.GET.get("date_from", date.today()),
            'date_to': self.request.GET.get("date_to", date.today()),
            'page': self.request.GET.get("page"),
            'page_size': PAGINATION_PAGE_SIZE,
        }
        date_from = self.request.GET.get("date_from", date.today())
        date_to = self.request.GET.get(
            "date_to", date.today() + timedelta(days=30))
        page = self.request.GET.get('page')
        additional_url_params = f"?page_size={PAGINATION_PAGE_SIZE}"

        if page is not None and not exclude_page_param:
            page = int(page)
            additional_url_params += f"&page={page}"

        if date_from and date_to:
            additional_url_params += f"&date_from={date_from}&date_to={date_to}"
        elif date_from:
            additional_url_params += f"&date_from={date_from}"
        elif date_to:
            additional_url_params += f"&date_to={date_to}"

        if self.request.user.is_staff:
            additional_url_params += f"&portal_admin=true"

        elif self.request.user.group and self.request.user in self.request.user.group.admin.all():
            additional_url_params += "&group_admin=true"

        return additional_url_params
