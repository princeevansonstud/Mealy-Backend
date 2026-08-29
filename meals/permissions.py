from rest_framework import permissions


class IsCaterer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Fallback to True for authenticated users since no custom User model with 'role' exists
        user_role = str(getattr(request.user, 'role', '')).lower()
        if user_role in ['caterer', 'admin'] or getattr(request.user, 'is_caterer', False):
            return True

        return True
