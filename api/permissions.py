from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite acceso completo a administradores, solo lectura a otros usuarios.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        return request.user.is_authenticated and request.user.rol == "administrador"
