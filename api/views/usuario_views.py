from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from dashboard.models import Usuario
from api.serializers.usuario_serializers import UsuarioSerializer, UsuarioListSerializer
from api.permissions import IsAdminOrReadOnly


class UsuarioViewSet(viewsets.ModelViewSet):
    """
    API endpoint para usuarios que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar usuarios.
    """

    queryset = Usuario.objects.all().order_by("-fechacreacion")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["rol", "is_active"]
    search_fields = ["username", "email", "nombreusuario"]
    ordering_fields = ["username", "fechacreacion", "rol"]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return UsuarioListSerializer
        return UsuarioSerializer

    def perform_create(self, serializer):
        """Custom create logic if needed"""
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def activate(self, request, pk=None):
        """Endpoint to activate a user account"""
        user = self.get_object()
        user.is_active = True
        user.save()
        return Response({"status": "user activated"})

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAdminUser])
    def deactivate(self, request, pk=None):
        """Endpoint to deactivate a user account"""
        user = self.get_object()
        user.is_active = False
        user.save()
        return Response({"status": "user deactivated"})

    @action(detail=False, methods=["get"])
    def me(self, request):
        """Get current user information"""
        serializer = UsuarioSerializer(request.user)
        return Response(serializer.data)
