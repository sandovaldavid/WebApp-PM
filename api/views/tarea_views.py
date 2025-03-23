from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from dashboard.models import (
    Tarea,
    TareaComun,
    TareaTareaComun,
    Tarearecurso,
    Recurso,
    Monitoreotarea,
)
from api.permissions import IsAdminOrReadOnly
from api.serializers.tarea_serializers import TareaSerializer, TareaListSerializer
from api.pagination import CustomPagination


class TareaViewSet(viewsets.ModelViewSet):
    """
    API endpoint para tareas que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar tareas.
    """

    queryset = Tarea.objects.all().order_by("-fechacreacion")
    serializer_class = TareaSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["estado", "prioridad", "tipo_tarea", "fase", "idrequerimiento"]
    search_fields = ["nombretarea", "descripcion", "tags"]
    ordering_fields = [
        "nombretarea",
        "fechainicio",
        "fechafin",
        "prioridad",
        "estado",
        "fechacreacion",
    ]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return TareaListSerializer
        return TareaSerializer

    def perform_create(self, serializer):
        """Custom create logic if needed"""
        serializer.save()

    @action(detail=True, methods=["get"])
    def recursos(self, request, pk=None):
        """Get all resources assigned to a specific task"""
        tarea = self.get_object()
        tarea_recursos = Tarearecurso.objects.filter(idtarea=tarea)

        recursos_data = []
        for tr in tarea_recursos:
            recursos_data.append(
                {
                    "idrecurso": tr.idrecurso.idrecurso,
                    "nombrerecurso": tr.idrecurso.nombrerecurso,
                    "tipo": tr.idrecurso.idtiporecurso.nametiporecurso,
                    "cantidad": tr.cantidad,
                    "experiencia": tr.experiencia,
                }
            )

        return Response(recursos_data)

    @action(detail=True, methods=["get"])
    def monitoreo(self, request, pk=None):
        """Get monitoring information for a specific task"""
        tarea = self.get_object()
        try:
            monitoreo = Monitoreotarea.objects.get(idtarea=tarea)
            monitoreo_data = {
                "fechainicioreal": monitoreo.fechainicioreal,
                "fechafinreal": monitoreo.fechafinreal,
                "porcentajecompletado": monitoreo.porcentajecompletado,
                "alertagenerada": monitoreo.alertagenerada,
                "fechamodificacion": monitoreo.fechamodificacion,
            }
            return Response(monitoreo_data)
        except Monitoreotarea.DoesNotExist:
            return Response(
                {"detail": "No hay información de monitoreo para esta tarea."},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=True, methods=["get"])
    def tareas_comunes(self, request, pk=None):
        """Get common tasks related to this task"""
        tarea = self.get_object()
        relaciones = TareaTareaComun.objects.filter(idtarea=tarea)

        tareas_comunes = []
        for rel in relaciones:
            tareas_comunes.append(
                {
                    "idtareacomun": rel.idtareacomun.idtareacomun,
                    "nombre": rel.idtareacomun.nombre,
                    "descripcion": rel.idtareacomun.descripcion,
                    "similitud": rel.similitud,
                }
            )

        return Response(tareas_comunes)
