from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django_filters.rest_framework import DjangoFilterBackend
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Q

from dashboard.models import (
    Recurso,
    Tiporecurso,
    Recursohumano,
    Recursomaterial,
    Tarearecurso,
    Usuario,
    Actividad,
)
from api.permissions import IsAdminOrReadOnly
from api.serializers.recurso_serializers import RecursoSerializer, RecursoListSerializer
from api.pagination import CustomPagination


class RecursoViewSet(viewsets.ModelViewSet):
    """
    API endpoint para recursos que permite CRUD completo.
    Solo admin puede crear/actualizar/eliminar recursos.
    """

    queryset = Recurso.objects.all().order_by("-fechacreacion")
    serializer_class = RecursoSerializer
    permission_classes = [IsAdminOrReadOnly]
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    pagination_class = CustomPagination
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["disponibilidad", "idtiporecurso"]
    search_fields = ["nombrerecurso"]
    ordering_fields = ["nombrerecurso", "fechacreacion", "carga_trabajo"]

    def get_serializer_class(self):
        """Use different serializers based on action"""
        if self.action == "list":
            return RecursoListSerializer
        return RecursoSerializer

    def perform_create(self, serializer):
        """Custom create logic with activity logging"""
        recurso = serializer.save()

        # Registrar actividad de creación
        try:
            Actividad.objects.create(
                nombre=f"Creación de recurso #{recurso.idrecurso}",
                descripcion=f"Se ha creado el recurso: {recurso.nombrerecurso}",
                idusuario=self.request.user,
                accion="CREACION",
                entidad_tipo="Recurso",
                entidad_id=recurso.idrecurso,
                es_automatica=True,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

    def perform_update(self, serializer):
        """Custom update logic with activity logging"""
        recurso = serializer.save()

        # Registrar actividad de actualización
        try:
            Actividad.objects.create(
                nombre=f"Actualización de recurso #{recurso.idrecurso}",
                descripcion=f"Se ha actualizado el recurso: {recurso.nombrerecurso}",
                idusuario=self.request.user,
                accion="MODIFICACION",
                entidad_tipo="Recurso",
                entidad_id=recurso.idrecurso,
                es_automatica=True,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

    def perform_destroy(self, instance):
        """Custom delete logic with activity logging"""
        id_recurso = instance.idrecurso
        nombre_recurso = instance.nombrerecurso

        # Verificar si el recurso está siendo utilizado en tareas
        if Tarearecurso.objects.filter(idrecurso=instance).exists():
            raise Exception(
                "No se puede eliminar un recurso que está asignado a tareas"
            )

        # Verificar y eliminar relaciones con Recursohumano o Recursomaterial
        try:
            if hasattr(instance, "recursohumano"):
                instance.recursohumano.delete()
            elif hasattr(instance, "recursomaterial"):
                instance.recursomaterial.delete()
        except Exception:
            pass

        # Registrar actividad de eliminación
        try:
            Actividad.objects.create(
                nombre=f"Eliminación de recurso #{id_recurso}",
                descripcion=f"Se ha eliminado el recurso: {nombre_recurso}",
                idusuario=self.request.user,
                accion="ELIMINACION",
                entidad_tipo="Recurso",
                entidad_id=id_recurso,
                es_automatica=True,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

        instance.delete()

    @action(detail=True, methods=["get"])
    def tareas(self, request, pk=None):
        """Get tasks assigned to this resource"""
        recurso = self.get_object()
        tareas_recurso = Tarearecurso.objects.filter(idrecurso=recurso)

        tareas_data = []
        for tr in tareas_recurso:
            tarea = tr.idtarea
            tareas_data.append(
                {
                    "idtarea": tarea.idtarea,
                    "nombretarea": tarea.nombretarea,
                    "estado": tarea.estado,
                    "fechainicio": tarea.fechainicio,
                    "fechafin": tarea.fechafin,
                    "cantidad": tr.cantidad,
                    "experiencia": tr.experiencia,
                    "requerimiento": (
                        {
                            "idrequerimiento": tarea.idrequerimiento.idrequerimiento,
                            "descripcion": tarea.idrequerimiento.descripcion,
                        }
                        if tarea.idrequerimiento
                        else None
                    ),
                    "proyecto": (
                        {
                            "idproyecto": tarea.idrequerimiento.idproyecto.idproyecto,
                            "nombreproyecto": tarea.idrequerimiento.idproyecto.nombreproyecto,
                        }
                        if tarea.idrequerimiento and tarea.idrequerimiento.idproyecto
                        else None
                    ),
                }
            )

        return Response(tareas_data)

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser]
    )
    def crear_recurso_humano(self, request):
        """Create a human resource with its details"""
        # Get basic resource data
        nombre = request.data.get("nombrerecurso")
        id_tipo_recurso = request.data.get("idtiporecurso")
        disponibilidad = request.data.get("disponibilidad", True)

        # Get human resource specific data
        cargo = request.data.get("cargo")
        habilidades = request.data.get("habilidades")
        tarifahora = request.data.get("tarifahora")
        id_usuario = request.data.get("idusuario")

        if not nombre or not id_tipo_recurso:
            return Response(
                {"error": "Los campos nombrerecurso y idtiporecurso son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get tiporecurso
            tipo_recurso = Tiporecurso.objects.get(idtiporecurso=id_tipo_recurso)

            # Get usuario if provided
            usuario = None
            if id_usuario:
                try:
                    usuario = Usuario.objects.get(idusuario=id_usuario)
                except Usuario.DoesNotExist:
                    return Response(
                        {"error": "El usuario especificado no existe"},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

            with transaction.atomic():
                # Create base resource
                now = timezone.now()
                recurso = Recurso.objects.create(
                    nombrerecurso=nombre,
                    idtiporecurso=tipo_recurso,
                    disponibilidad=disponibilidad,
                    fechacreacion=now,
                    fechamodificacion=now,
                )

                # Create human resource
                Recursohumano.objects.create(
                    idrecurso=recurso,
                    cargo=cargo,
                    habilidades=habilidades,
                    tarifahora=tarifahora,
                    idusuario=usuario,
                )

                # Register activity
                try:
                    Actividad.objects.create(
                        nombre=f"Creación de recurso humano #{recurso.idrecurso}",
                        descripcion=f"Se ha creado el recurso humano: {nombre}",
                        idusuario=request.user,
                        accion="CREACION",
                        entidad_tipo="Recurso",
                        entidad_id=recurso.idrecurso,
                        es_automatica=True,
                    )
                except Exception:
                    pass

                return Response(
                    {
                        "mensaje": "Recurso humano creado exitosamente",
                        "idrecurso": recurso.idrecurso,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Tiporecurso.DoesNotExist:
            return Response(
                {"error": "El tipo de recurso especificado no existe"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(
        detail=False, methods=["post"], permission_classes=[permissions.IsAdminUser]
    )
    def crear_recurso_material(self, request):
        """Create a material resource with its details"""
        # Get basic resource data
        nombre = request.data.get("nombrerecurso")
        id_tipo_recurso = request.data.get("idtiporecurso")
        disponibilidad = request.data.get("disponibilidad", True)

        # Get material resource specific data
        costounidad = request.data.get("costounidad")
        fechacompra = request.data.get("fechacompra")

        if not nombre or not id_tipo_recurso:
            return Response(
                {"error": "Los campos nombrerecurso y idtiporecurso son obligatorios"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Get tiporecurso
            tipo_recurso = Tiporecurso.objects.get(idtiporecurso=id_tipo_recurso)

            with transaction.atomic():
                # Create base resource
                now = timezone.now()
                recurso = Recurso.objects.create(
                    nombrerecurso=nombre,
                    idtiporecurso=tipo_recurso,
                    disponibilidad=disponibilidad,
                    fechacreacion=now,
                    fechamodificacion=now,
                )

                # Create material resource
                Recursomaterial.objects.create(
                    idrecurso=recurso, costounidad=costounidad, fechacompra=fechacompra
                )

                # Register activity
                try:
                    Actividad.objects.create(
                        nombre=f"Creación de recurso material #{recurso.idrecurso}",
                        descripcion=f"Se ha creado el recurso material: {nombre}",
                        idusuario=request.user,
                        accion="CREACION",
                        entidad_tipo="Recurso",
                        entidad_id=recurso.idrecurso,
                        es_automatica=True,
                    )
                except Exception:
                    pass

                return Response(
                    {
                        "mensaje": "Recurso material creado exitosamente",
                        "idrecurso": recurso.idrecurso,
                    },
                    status=status.HTTP_201_CREATED,
                )

        except Tiporecurso.DoesNotExist:
            return Response(
                {"error": "El tipo de recurso especificado no existe"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=False, methods=["get"])
    def por_tipo(self, request):
        """Get resources filtered by type (Humano, Material)"""
        tipo = request.query_params.get("tipo")

        if not tipo:
            return Response(
                {"error": "Se requiere el parámetro 'tipo'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if tipo.lower() == "humano":
            # Get all human resources
            recursos = Recurso.objects.filter(recursohumano__isnull=False)
        elif tipo.lower() == "material":
            # Get all material resources
            recursos = Recurso.objects.filter(recursomaterial__isnull=False)
        else:
            return Response(
                {"error": "Tipo inválido. Usar 'humano' o 'material'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        page = self.paginate_queryset(recursos)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(recursos, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def estadisticas(self, request):
        """Get statistics about resources"""
        # Total resources by type
        total_humanos = Recursohumano.objects.count()
        total_materiales = Recursomaterial.objects.count()

        # Resources availability
        disponibles = Recurso.objects.filter(disponibilidad=True).count()
        no_disponibles = Recurso.objects.filter(disponibilidad=False).count()

        # Most used resources in tasks
        recursos_mas_usados = (
            Tarearecurso.objects.values("idrecurso", "idrecurso__nombrerecurso")
            .annotate(total_tareas=Count("idtarea"))
            .order_by("-total_tareas")[:5]
        )

        # Resources with highest workload
        recursos_mayor_carga = (
            Recurso.objects.filter(carga_trabajo__isnull=False)
            .order_by("-carga_trabajo")[:5]
            .values("idrecurso", "nombrerecurso", "carga_trabajo")
        )

        return Response(
            {
                "total_recursos": total_humanos + total_materiales,
                "total_humanos": total_humanos,
                "total_materiales": total_materiales,
                "disponibles": disponibles,
                "no_disponibles": no_disponibles,
                "recursos_mas_usados": recursos_mas_usados,
                "recursos_mayor_carga": recursos_mayor_carga,
            }
        )
