from rest_framework import permissions
from .models import GroupSubscription
from django.utils.timezone import datetime


class SubscribedPermission(permissions.BasePermission):
    message = "You are not allowed to perform this action, please contact your group administrator"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.is_staff:
            if not request.user.group:
                return False
            subscription = request.user.group.subscriptions.first()
            if not subscription:
                return False
            if subscription.status != GroupSubscription.GroupSubscriptionChoices.ACTIVE:
                return False
            if datetime.now() > subscription.end_date or datetime.now() < subscription.start_date:
                return False

        return True