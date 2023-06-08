from rest_framework import permissions


class IsAuthorOrAdminPermission(permissions.BasePermission):
    """Разрешение доступа автору, админу."""
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_authenticated
        )

    def has_object_permission(self, request, view, obj):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_superuser or obj.author == request.user
        )


class IsAdminOrReadOnly(permissions.BasePermission):
    """Разрешение доступа админу или чтение."""
    def has_permission(self, request, view):
        return (
            request.method in permissions.SAFE_METHODS
            or request.user.is_staff
        )
