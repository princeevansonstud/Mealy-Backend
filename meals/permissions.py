from rest_framework import permissions


class IsCaterer(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        
        user_role = str(getattr(request.user, 'role', '')).lower()
        if user_role in ['caterer', 'admin'] or getattr(request.user, 'is_caterer', False):
            return True

        return True
