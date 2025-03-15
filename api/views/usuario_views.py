from rest_framework import viewsets, permissions
from dashboard.models import Usuario
from api.serializers.usuario_serializers import UsuarioSerializer
from api.permissions import IsAdminOrReadOnly


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all()
    serializer_class = UsuarioSerializer
    permission_classes = [IsAdminOrReadOnly]
