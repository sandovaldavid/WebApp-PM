from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from django.db.models import Count, Avg

from dashboard.models import TareaComun, TipoTarea, TareaTareaComun
from api.permissions import IsAdminOrReadOnly
from api.serializers.tarea_comun_serializers import (
    TareaComunSerializer,
    TareaComunListSerializer,
)
from api.pagination import CustomPagination


class TareaComunViewSet(viewsets.ModelViewSet):
    """
    API endpoint para tareas comunes que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar tareas comunes.
    """

    queryset = TareaComun.objects.all().order_by("-fechacreacion")
    serializer_class = TareaComunSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["idtipotarea"]
    search_fields = ["nombre", "descripcion"]
    ordering_fields = ["nombre", "fechacreacion"]

    # Cache the list view for 15 minutes
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return TareaComunListSerializer
        return TareaComunSerializer

    def perform_create(self, serializer):
        """Custom create logic with activity logging"""
        tarea_comun = serializer.save()

        # Registrar actividad de creación si está disponible
        try:
            from dashboard.models import Actividad

            Actividad.objects.create(
                nombre=f"Creación de tarea común #{tarea_comun.idtareacomun}",
                descripcion=f"Se ha creado la tarea común: {tarea_comun.nombre}",
                idusuario=self.request.user,
                accion="crear",
                entidad_tipo="TareaComun",
                entidad_id=tarea_comun.idtareacomun,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

    @action(detail=True, methods=["get"])
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def tareas_relacionadas(self, request, pk=None):
        """Get tasks related to this common task"""
        tarea_comun = self.get_object()
        relaciones = TareaTareaComun.objects.filter(idtareacomun=tarea_comun)

        from api.serializers.tarea_serializers import TareaListSerializer

        tareas_relacionadas = []
        for rel in relaciones:
            tarea = rel.idtarea
            # Agregar la tarea y el porcentaje de similitud
            tarea_data = TareaListSerializer(tarea).data
            tarea_data["similitud"] = rel.similitud
            tareas_relacionadas.append(tarea_data)

        return Response(tareas_relacionadas)

    @action(detail=False, methods=["get"])
    def por_tipo(self, request):
        """Get common tasks filtered by type"""
        tipo_id = request.query_params.get("tipo_id")
        if not tipo_id:
            return Response(
                {"error": "Se requiere el parámetro 'tipo_id'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            TipoTarea.objects.get(idtipotarea=tipo_id)  # Verify type exists
            tareas_comunes = TareaComun.objects.filter(idtipotarea=tipo_id)

            page = self.paginate_queryset(tareas_comunes)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(tareas_comunes, many=True)
            return Response(serializer.data)

        except TipoTarea.DoesNotExist:
            return Response(
                {"error": "El tipo de tarea especificado no existe"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    @method_decorator(cache_page(60 * 30))  # Cache for 30 minutes
    def estadisticas(self, request):
        """Get statistics about common tasks"""
        # Total number of common tasks
        total = TareaComun.objects.count()

        # Common tasks by type
        por_tipo = (
            TareaComun.objects.values("idtipotarea", "idtipotarea__nombre")
            .annotate(total=Count("idtareacomun"))
            .order_by("-total")
        )

        # Most used common tasks in real tasks
        mas_usadas = (
            TareaComun.objects.annotate(total_usos=Count("tareatareacomun"))
            .values("idtareacomun", "nombre", "total_usos")
            .order_by("-total_usos")[:10]
        )

        # Average time
        tiempo_promedio = TareaComun.objects.filter(
            tiempo_promedio__isnull=False
        ).aggregate(promedio=Avg("tiempo_promedio"))

        return Response(
            {
                "total": total,
                "por_tipo": list(por_tipo),
                "mas_usadas": list(mas_usadas),
                "tiempo_promedio_general": tiempo_promedio["promedio"],
            }
        )
