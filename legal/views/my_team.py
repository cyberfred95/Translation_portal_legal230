import base64
from urllib.parse import urlencode

from django.urls import reverse
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect

from django.utils.timezone import now
from users.models import User
from subscriptions.models import SubscriptionType, UserSubscription
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
            if not self._can_edit_user(user, request.user):
                return JsonResponse({'error': 'Permission denied'}, status=403)

            old_email = user.email
            new_email = email if email else ''

            self._update_user(user, username, new_email, is_admin)

            if new_email and old_email != new_email:
                self._handle_email_change(user, new_email, request)

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
        user_group = self._get_current_user_group()

        group_name = "All Users" if self.request.user.is_staff else (user_group.name if user_group else "No Group")
        stripe_portal_url = self._get_stripe_portal_url()
        has_buyer_in_group = self._has_buyer_in_group(user_group)

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
        queryset = self._get_user_queryset().select_related('group').order_by('-date_joined')

        members_with_data = []
        for user in queryset:
            license_info = self.get_user_license(user)
            if license_info['status'] == 'no_subscription':
                continue
            is_admin = self.check_admin_status(user)
            is_buyer = (not is_admin) and self.check_buyer_status(user)
            usage = self._get_user_usage(user)
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
                'usage': usage,
                'is_editable': self.is_user_editable(user, is_buyer, license_info),
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
        queryset = self._get_user_queryset()

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
        """Retourne les informations de licence de l'utilisateur."""
        active_subscriptions = self._get_active_subscriptions(user)
        
        if not active_subscriptions:
            return {
                'status': 'no_subscription',
                'name': 'No subscription',
                'product_type': None
            }
        elif len(active_subscriptions) == 1:
            subscription = active_subscriptions[0]
            return {
                'status': 'active',
                'name': subscription.subscription.name,
                'product_type': subscription.subscription.product_type
            }
        else:
            return {
                'status': 'error',
                'name': 'Error: Multiple subscriptions',
                'product_type': None
            }

    def is_user_editable(self, user, is_buyer, license_info):
        """Détermine si un utilisateur peut être édité."""
        if is_buyer:
            return False
        product_type = license_info.get('product_type')
        if product_type in (SubscriptionType.ProductChoices.API, SubscriptionType.ProductChoices.WORD_ADD_IN):
            return False
        return True

    # Méthodes helper privées

    def _get_user_queryset(self):
        """Retourne le queryset des utilisateurs selon les permissions."""
        if self.request.user.is_staff:
            return User.objects.all()
        user_group = getattr(self.request.user, 'group', None)
        if user_group:
            return User.objects.filter(group=user_group)
        return User.objects.none()

    def _get_active_subscriptions(self, user):
        """Retourne la liste des abonnements actifs d'un utilisateur."""
        current_time = now()
        all_subscriptions = UserSubscription.objects.filter(
            user=user
        ).select_related('subscription')
        
        active_subscriptions = [
            sub for sub in all_subscriptions
            if is_user_subscription_active(sub.status)
            and current_time >= sub.start_date
            and current_time <= sub.end_date
        ]
        return active_subscriptions

    def _get_active_subscription(self, user):
        """Retourne le premier abonnement actif d'un utilisateur ou None."""
        active_subscriptions = self._get_active_subscriptions(user)
        return active_subscriptions[0] if active_subscriptions else None

    def _get_user_usage(self, user):
        """Retourne les statistiques d'utilisation de l'utilisateur."""
        user_subscription = user.subscriptions.first()
        if not user_subscription:
            return {
                'symbols': {'current': 0, 'max': 0},
                'words': {'current': 0, 'max': 0},
                'files': {'current': 0, 'max': 0},
            }
        return {
            'symbols': {
                'current': getattr(user_subscription, 'translated_symbols_count', 0),
                'max': getattr(user_subscription, 'max_symbols_count', 0)
            },
            'words': {
                'current': getattr(user_subscription, 'translated_words_count', 0),
                'max': getattr(user_subscription, 'max_words_count', 0)
            },
            'files': {
                'current': getattr(user_subscription, 'translated_files_count', 0),
                'max': getattr(user_subscription, 'max_files_count', 0)
            },
        }

    def _can_edit_user(self, user, current_user):
        """Vérifie si l'utilisateur actuel peut éditer l'utilisateur donné."""
        if current_user.is_staff:
            return True
        if user.group != current_user.group:
            return False
        if user.stripe_customer_id:
            return False
        return True

    def _update_user(self, user, username, email, is_admin):
        """Met à jour les informations de l'utilisateur."""
        user.username = username
        user.email = email
        user.save()

        user_group = user.group
        if user_group:
            if is_admin:
                if not user_group.admin.filter(id=user.id).exists():
                    user_group.admin.add(user)
            else:
                if user_group.admin.filter(id=user.id).exists():
                    user_group.admin.remove(user)

    def _get_or_create_api_key(self, subscription):
        """Récupère ou crée la clé API d'un abonnement."""
        if not subscription.api_key:
            subscription.save()
        return subscription.api_key

    def _send_subscription_email(self, subscription, new_email, user, request):
        """Envoie l'email approprié selon le type d'abonnement."""
        product_type = subscription.subscription.product_type
        
        if product_type == SubscriptionType.ProductChoices.LEXA:
            params = {
                "email": base64.b64encode(new_email.encode('utf-8')),
                "group": base64.b64encode(str(user.group.id).encode('utf-8')) if user.group else None,
                "subscription_type_id": base64.b64encode(str(subscription.subscription.id).encode('utf-8')),
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
        elif product_type in (SubscriptionType.ProductChoices.API, SubscriptionType.ProductChoices.WORD_ADD_IN):
            api_key = self._get_or_create_api_key(subscription)
            email_type = EmailType.API_CREATED if product_type == SubscriptionType.ProductChoices.API else EmailType.ADDIN_CREATED
            send_email(
                new_email,
                email_type,
                request.user.language,
                {
                    "lexa_username": user.username,
                    "lexa_email": new_email,
                    "lexa_apikey": api_key
                }
            )

    def _handle_email_change(self, user, new_email, request):
        """Gère le changement d'email et envoie les notifications appropriées."""
        active_subscription = self._get_active_subscription(user)
        if active_subscription:
            self._send_subscription_email(active_subscription, new_email, user, request)

    def _get_current_user_group(self):
        """Retourne le groupe de l'utilisateur actuel."""
        return getattr(self.request.user, 'group', None)

    def _get_stripe_portal_url(self):
        """Retourne l'URL du portail Stripe si disponible."""
        if not self.request.user.stripe_customer_id:
            return None
        error_response, portal_url = get_stripe_customer_session_url(self.request.user.stripe_customer_id)
        return portal_url if not error_response and portal_url else None

    def _has_buyer_in_group(self, user_group):
        """Vérifie s'il y a un buyer dans le groupe."""
        if self.request.user.is_staff:
            return User.objects.filter(stripe_customer_id__isnull=False).exists()
        if user_group:
            return User.objects.filter(group=user_group, stripe_customer_id__isnull=False).exists()
        return False


