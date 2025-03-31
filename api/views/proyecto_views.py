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
from api.pagination import CustomPagination


class ProyectoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para proyectos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar proyectos.
    """

    queryset = Proyecto.objects.all().order_by("-fechacreacion")
    serializer_class = ProyectoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
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

        try:
            # Get requirements associated with this project
            requerimientos = Requerimiento.objects.filter(idproyecto=proyecto)

            if not requerimientos.exists():
                return Response(
                    {"detail": "Este proyecto no tiene requerimientos asociados."},
                    status=status.HTTP_200_OK,
                )

            # Get tasks associated with these requirements
            tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos).order_by(
                "-fechacreacion"
            )

            # Apply filters from query params if they exist
            estado = request.query_params.get("estado")
            if estado:
                tareas = tareas.filter(estado=estado)

            prioridad = request.query_params.get("prioridad")
            if prioridad:
                tareas = tareas.filter(prioridad=prioridad)

            # Use pagination if available
            page = self.paginate_queryset(tareas)

            from api.serializers.tarea_serializers import TareaListSerializer

            if page is not None:
                serializer = TareaListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = TareaListSerializer(tareas, many=True)
            return Response(serializer.data)

        except Exception as e:
            return Response(
                {"detail": f"Error al obtener tareas: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

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
