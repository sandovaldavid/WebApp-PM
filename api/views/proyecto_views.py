from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from dashboard.models import Proyecto
from api.permissions import IsAdminOrReadOnly
from api.serializers.proyecto_serializers import (
    ProyectoSerializer,
    ProyectoListSerializer,
)


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para proyectos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar proyectos.
    """

    queryset = Proyecto.objects.all().order_by("-fechacreacion")
    serializer_class = ProyectoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["estado", "idequipo"]
    search_fields = ["nombreproyecto", "descripcion"]
    ordering_fields = ["nombreproyecto", "fechainicio", "fechafin", "fechacreacion"]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return ProyectoListSerializer
        return ProyectoSerializer

    def perform_create(self, serializer):
        """Custom create logic if needed"""
        serializer.save()

    @action(detail=True, methods=["get"])
    def tareas(self, request, pk=None):
        """Get all tasks for a specific project"""
        proyecto = self.get_object()
        from dashboard.models import Tarea, Requerimiento

        requerimientos = Requerimiento.objects.filter(idproyecto=proyecto)
        tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)

        from api.serializers.tarea_serializers import TareaListSerializer

        serializer = TareaListSerializer(tareas, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def equipo(self, request, pk=None):
        """Get team information for a specific project"""
        proyecto = self.get_object()
        equipo = proyecto.idequipo

        if not equipo:
            return Response(
                {"detail": "Este proyecto no tiene un equipo asignado."},
                status=status.HTTP_404_NOT_FOUND,
            )

        from api.serializers.equipo_serializers import EquipoSerializer

        serializer = EquipoSerializer(equipo)
        return Response(serializer.data)
