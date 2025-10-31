import base64
from urllib.parse import urlencode

from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from django.utils.timezone import now
from users.models import User
from subscriptions.models import UserSubscription
from subscriptions.permissions import is_user_subscription_active

from emails.models import EmailType
from emails.send_email import send_email

from stripe_webhooks.tasks_handlers.helper.stripe_session import get_stripe_customer_session_url

from legal.views_all import BaseTemplateView


class MyTeamView(LoginRequiredMixin, UserPassesTestMixin, BaseTemplateView):
    template_name = 'my_team/my_team.html'

    def test_func(self):
        if self.request.user.is_staff:
            return True
        user_group = getattr(self.request.user, 'group', None)
        if user_group:
            return user_group.admin.filter(id=self.request.user.id).exists()
        return False

    def post(self, request, *args, **kwargs):

        user_id = request.POST.get('user_id')
        username = request.POST.get('username')
        email = request.POST.get('email', '')
        is_admin = request.POST.get('is_admin') == 'on'

        try:
            user = User.objects.get(id=user_id)
            if not request.user.is_staff:
                if user.group != request.user.group:
                    return JsonResponse({'error': 'Permission denied'}, status=403)
                if user.stripe_customer_id:
                    return JsonResponse({'error': 'Cannot edit buyer users'}, status=403)

            old_email = user.email
            new_email = email if email else ''

            user.username = username
            user.email = new_email
            user.save()

            user_group = user.group
            if user_group:
                if is_admin:
                    if not user_group.admin.filter(id=user.id).exists():
                        user_group.admin.add(user)
                else:
                    if user_group.admin.filter(id=user.id).exists():
                        user_group.admin.remove(user)

            if new_email and old_email != new_email:
                active_subscription = None
                current_time = now()
                all_subscriptions = UserSubscription.objects.filter(user=user)
                for sub in all_subscriptions:
                    if is_user_subscription_active(sub.status):
                        if current_time >= sub.start_date and current_time <= sub.end_date:
                            active_subscription = sub
                            break
                if active_subscription:
                    params = {
                        "email": base64.b64encode(new_email.encode('utf-8')),
                        "group": base64.b64encode(str(user.group.id).encode('utf-8')) if user.group else None,
                        "subscription_type_id": base64.b64encode(str(active_subscription.subscription.id).encode('utf-8')),
                    }
                    send_email(
                        new_email,
                        EmailType.USER_MANAGEMENT_INVITATION,
                        request.user.language,
                        {
                            "lexa_username": user.username,
                            "lexa_email": new_email,
                            "url_reset_password": self.get_register_user_absolute_uri(request, params=params),
                        }
                    )

            return redirect('my_team')

        except User.DoesNotExist:
            return JsonResponse({'error': 'User not found'}, status=404)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    @staticmethod
    def get_register_user_absolute_uri(request, params: dict = None):
        url = f"{request.build_absolute_uri(reverse('reset-password'))}"
        if params:
            url = f"{url}?{urlencode(params)}"
        return url

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        team_members, paginator_info = self.get_team_members()
        stats = self.get_team_stats()

        if self.request.user.is_staff:
            group_name = "All Users"
        else:
            user_group = getattr(self.request.user, 'group', None)
            group_name = user_group.name if user_group else "No Group"

        stripe_portal_url = None
        if self.request.user.stripe_customer_id:
            error_response, portal_url = get_stripe_customer_session_url(self.request.user.stripe_customer_id)
            if not error_response and portal_url:
                stripe_portal_url = portal_url

        has_buyer_in_group = False
        if self.request.user.is_staff:
            has_buyer_in_group = User.objects.filter(stripe_customer_id__isnull=False).exists()
        else:
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                has_buyer_in_group = User.objects.filter(group=user_group, stripe_customer_id__isnull=False).exists()

        context.update({
            'team_members': team_members,
            'stats': stats,
            'paginator': paginator_info,
            'group_name': group_name,
            'stripe_portal_url': stripe_portal_url,
            'has_buyer_in_group': has_buyer_in_group,
        })

        return context

    def get_team_members(self):
        if self.request.user.is_staff:
            queryset = User.objects.all()
        else:
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                queryset = User.objects.filter(group=user_group)
            else:
                queryset = User.objects.none()

        queryset = queryset.select_related('group').order_by('-date_joined')

        members_with_data = []
        for user in queryset:
            license_info = self.get_user_license(user)
            if license_info['status'] == 'no_subscription':
                continue
            is_admin = self.check_admin_status(user)
            is_buyer = (not is_admin) and self.check_buyer_status(user)
            member_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name or 'Unknown',
                'last_name': user.last_name or 'User',
                'email': user.email,
                'initials': self.get_user_initials(user),
                'is_admin': is_admin,
                'is_buyer': is_buyer,
                'is_premium': self.check_premium_status(user),
                'date_joined': user.date_joined,
                'license': license_info,
            }
            members_with_data.append(member_data)

        # Custom ordering per business rules:
        # 1) Users (non admin, non buyer) having an email
        # 2) Users (non admin, non buyer) without email
        # 3) Admins
        # 4) Buyers
        def _bucket(member):
            if member['is_admin']:
                return 2
            if member['is_buyer']:
                return 3
            return 0 if member['email'] else 1

        members_with_data.sort(key=lambda m: (_bucket(m), (m['username'] or '').lower()))

        paginator_info = {
            'current_page': 1,
            'total_pages': 1,
            'has_previous': False,
            'has_next': False,
            'previous_page_number': None,
            'next_page_number': None,
            'page_range': [1],
            'has_multiple_pages': False,
        }

        return members_with_data, paginator_info

    def get_team_stats(self):
        if self.request.user.is_staff:
            queryset = User.objects.all()
        else:
            user_group = getattr(self.request.user, 'group', None)
            if user_group:
                queryset = User.objects.filter(group=user_group)
            else:
                queryset = User.objects.none()

        admin_users = 0
        active_plans = 0
        total_users_with_license = 0

        for user in queryset:
            license_info = self.get_user_license(user)
            if license_info['status'] == 'no_subscription':
                continue
            total_users_with_license += 1
            if self.check_admin_status(user):
                admin_users += 1
            if user.email:
                active_plans += 1

        return {
            'total_users': total_users_with_license,
            'admin_users': admin_users,
            'active_plans': active_plans,
        }

    def get_user_initials(self, user):
        first_initial = user.first_name[0].upper() if user.first_name else 'U'
        last_initial = user.last_name[0].upper() if user.last_name else 'U'
        return f"{first_initial}{last_initial}"

    def check_admin_status(self, user):
        if user.is_staff or user.is_superuser:
            return True
        user_group = getattr(user, 'group', None)
        if user_group:
            return user_group.admin.filter(id=user.id).exists()
        return False

    def check_premium_status(self, user):
        return user.is_staff or hasattr(user, 'subscription') and getattr(user.subscription, 'is_premium', False)

    def check_buyer_status(self, user):
        return bool(user.stripe_customer_id)

    def get_user_license(self, user):
        all_subscriptions = UserSubscription.objects.filter(user=user)
        active_subscriptions = []
        current_time = now()
        for sub in all_subscriptions:
            if is_user_subscription_active(sub.status):
                if current_time >= sub.start_date and current_time <= sub.end_date:
                    active_subscriptions.append(sub)
        if len(active_subscriptions) == 0:
            return {
                'status': 'no_subscription',
                'name': 'No subscription'
            }
        elif len(active_subscriptions) == 1:
            return {
                'status': 'active',
                'name': active_subscriptions[0].subscription.name
            }
        else:
            return {
                'status': 'error',
                'name': 'Error: Multiple subscriptions'
            }


