from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from dashboard.models import Requerimiento, Tarea, Proyecto, Actividad
from api.permissions import IsAdminOrReadOnly
from api.serializers.requerimiento_serializers import (
    RequerimientoSerializer,
    RequerimientoListSerializer,
)
from api.pagination import CustomPagination


class RequerimientoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para requerimientos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar requerimientos.
    """

    queryset = Requerimiento.objects.all().order_by("-fechacreacion")
    serializer_class = RequerimientoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["idproyecto"]
    search_fields = ["descripcion", "keywords"]
    ordering_fields = ["fechacreacion", "fechamodificacion"]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return RequerimientoListSerializer
        return RequerimientoSerializer

    def perform_create(self, serializer):
        """Custom create logic with activity logging"""
        requerimiento = serializer.save()

        # Registrar actividad de creación
        try:
            Actividad.objects.create(
                nombre=f"Creación de requerimiento #{requerimiento.idrequerimiento}",
                descripcion=f"Se ha creado el requerimiento: {requerimiento.descripcion[:50]}...",
                idusuario=self.request.user,
                accion="crear",
                entidad_tipo="Requerimiento",
                entidad_id=requerimiento.idrequerimiento,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

    def perform_update(self, serializer):
        """Custom update logic with activity logging"""
        requerimiento = serializer.save()

        # Registrar actividad de actualización
        try:
            Actividad.objects.create(
                nombre=f"Actualización de requerimiento #{requerimiento.idrequerimiento}",
                descripcion=f"Se ha actualizado el requerimiento: {requerimiento.descripcion[:50]}...",
                idusuario=self.request.user,
                accion="actualizar",
                entidad_tipo="Requerimiento",
                entidad_id=requerimiento.idrequerimiento,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

    def perform_destroy(self, instance):
        """Custom delete logic with activity logging"""
        req_id = instance.idrequerimiento
        req_desc = instance.descripcion[:50]

        # Verificar si tiene tareas asociadas
        if Tarea.objects.filter(idrequerimiento=instance).exists():
            raise Exception(
                "No se puede eliminar un requerimiento con tareas asociadas"
            )

        # Registrar actividad de eliminación
        try:
            Actividad.objects.create(
                nombre=f"Eliminación de requerimiento #{req_id}",
                descripcion=f"Se ha eliminado el requerimiento: {req_desc}...",
                idusuario=self.request.user,
                accion="eliminar",
                entidad_tipo="Requerimiento",
                entidad_id=req_id,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

        instance.delete()

    @action(detail=True, methods=["get"])
    def tareas(self, request, pk=None):
        """Get all tasks related to this requirement"""
        requerimiento = self.get_object()
        tareas = Tarea.objects.filter(idrequerimiento=requerimiento)

        from api.serializers.tarea_serializers import TareaListSerializer

        serializer = TareaListSerializer(tareas, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def por_proyecto(self, request):
        """Get requirements filtered by project"""
        proyecto_id = request.query_params.get("idproyecto")
        if not proyecto_id:
            return Response(
                {"error": "Se requiere el parámetro 'idproyecto'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verificar que el proyecto existe
            Proyecto.objects.get(idproyecto=proyecto_id)

            requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_id)
            page = self.paginate_queryset(requerimientos)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = self.get_serializer(requerimientos, many=True)
            return Response(serializer.data)
        except Proyecto.DoesNotExist:
            return Response(
                {"error": "El proyecto especificado no existe"},
                status=status.HTTP_404_NOT_FOUND,
            )

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """Get statistics about requirements"""
        total = Requerimiento.objects.count()

        # Requerimientos por proyecto
        por_proyecto = (
            Proyecto.objects.values("idproyecto", "nombreproyecto")
            .annotate(total_requerimientos=Count("requerimiento"))
            .order_by("-total_requerimientos")
        )

        # Requerimientos con más tareas
        con_mas_tareas = (
            Requerimiento.objects.annotate(total_tareas=Count("tarea"))
            .values("idrequerimiento", "descripcion", "total_tareas")
            .order_by("-total_tareas")[:5]
        )

        return Response(
            {
                "total_requerimientos": total,
                "por_proyecto": por_proyecto,
                "con_mas_tareas": con_mas_tareas,
            }
        )
