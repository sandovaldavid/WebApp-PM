from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permite operaciones de escritura solo a administradores,
    operaciones de lectura a cualquier usuario autenticado.
    """

    def has_permission(self, request, view):
        # Permite GET, HEAD, OPTIONS a usuarios autenticados
        if request.method in permissions.SAFE_METHODS and request.user.is_authenticated:
            return True

        # Operaciones de escritura solo a administradores
        return request.user.is_authenticated and request.user.rol == "Administrador"


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permite acceso al propietario del objeto o a un administrador.
    Útil para que un usuario solo pueda modificar sus propios datos.
    """

    def has_object_permission(self, request, view, obj):
        # Verifica si el usuario es el propietario o es administrador
        return obj.id == request.user.id or request.user.rol == "Administrador"
