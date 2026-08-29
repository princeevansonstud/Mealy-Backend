from rest_framework import permissions


class IsCaterer(permissions.BasePermission):
    """
    Custom permission to only allow caterers to create or modify menus.
    Assumes your User model has a `role` field (e.g., 'caterer') or `is_caterer` flag.
    """

    def has_permission(self, request, view):

        if not request.user or not request.user.is_authenticated:
            return False

        return getattr(request.user, 'role', None) == 'caterer' or getattr(request.user, 'is_caterer', False)
