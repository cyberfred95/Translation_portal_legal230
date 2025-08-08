from rest_framework import permissions
from .models import UserSubscription
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _


def is_user_subscription_active(status: UserSubscription.UserSubscriptionChoices) -> bool:
    active_states = {
        UserSubscription.UserSubscriptionChoices.INCOMPLETE,
        UserSubscription.UserSubscriptionChoices.ACTIVE,
        UserSubscription.UserSubscriptionChoices.TRIALING,
        UserSubscription.UserSubscriptionChoices.PAST_DUE,
    }
    return status in active_states


class SubscribedPermission(permissions.BasePermission):
    message = _(
        "You are not allowed to perform this action, please contact your group administrator")

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:

            return False
        if not request.user.is_staff:
            if not request.user.group:
                return False
            user_subscription = request.user.subscriptions.first()
            if not user_subscription:
                return False
            if not is_user_subscription_active(user_subscription.status):
                return False

            current_time = now()
            if current_time > user_subscription.end_date or current_time < user_subscription.start_date:
                return False
            if hasattr(view, 'requires_writing_access') and view.requires_writing_access:
                if not user_subscription.access_to_writing:
                    return False

        return True
