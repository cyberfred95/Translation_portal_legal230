from rest_framework import permissions


class SubscribedPermission(permissions.BasePermission):

    message = "You are not allowed to perform this action, please contact your group administrator"

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if not request.user.is_staff:
            if not request.user.group:
                return False
            if not request.user.group.subscriptions.first():
                return False
        return True
