from rest_framework.permissions import SAFE_METHODS, BasePermission
from subscriptions.services import get_user_tier


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or bool(request.user and request.user.is_staff)


class HasRequiredTier(BasePermission):
    message = 'Your subscription does not give you access to this video.'

    def has_object_permission(self, request, view, obj):
        return get_user_tier(request.user) >= obj.required_tier

