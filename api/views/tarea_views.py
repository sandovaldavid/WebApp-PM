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
    Requerimiento,
    Proyecto,
    Usuario,
    TipoTarea,
)
from api.permissions import IsAdminOrReadOnly
from api.serializers.tarea_serializers import TareaSerializer, TareaListSerializer
from api.pagination import CustomPagination
import requests
import logging
from datetime import datetime
import os  # Add this import

# Set up logger
logger = logging.getLogger(__name__)


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

    @action(detail=False, methods=["get"])
    def por_proyecto(self, request):
        """Get tasks filtered by project ID"""
        proyecto_id = request.query_params.get("idproyecto")
        if not proyecto_id:
            return Response(
                {"error": "Se requiere el parámetro 'idproyecto'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Verify the project exists
            proyecto = Proyecto.objects.get(idproyecto=proyecto_id)

            # Get requirements for this project
            requerimientos = Requerimiento.objects.filter(idproyecto=proyecto)

            if not requerimientos.exists():
                return Response(
                    {"detail": "Este proyecto no tiene requerimientos asociados."},
                    status=status.HTTP_200_OK,
                    data=[],
                )

            # Get tasks for these requirements
            tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)

            # Apply additional filters if provided
            estado = request.query_params.get("estado")
            if estado:
                tareas = tareas.filter(estado=estado)

            prioridad = request.query_params.get("prioridad")
            if prioridad:
                tareas = tareas.filter(prioridad=prioridad)

            fase = request.query_params.get("fase")
            if fase:
                tareas = tareas.filter(fase=fase)

            # Order by provided parameter or default to creation date
            ordering = request.query_params.get("ordering", "-fechacreacion")
            tareas = tareas.order_by(ordering)

            # Use pagination
            page = self.paginate_queryset(tareas)
            if page is not None:
                serializer = TareaListSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = TareaListSerializer(tareas, many=True)
            return Response(serializer.data)

        except Proyecto.DoesNotExist:
            return Response(
                {"detail": "El proyecto especificado no existe."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"detail": f"Error al obtener tareas: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def cambiar_estado(self, request, pk=None):
        """Update the status of a task"""
        tarea = self.get_object()
        nuevo_estado = request.data.get("estado")

        if not nuevo_estado:
            return Response(
                {"error": "Se requiere el campo 'estado'"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        estados_validos = [
            "pendiente",
            "en_progreso",
            "completada",
            "pausada",
            "cancelada",
        ]
        if nuevo_estado not in estados_validos:
            return Response(
                {
                    "error": f"Estado inválido. Valores permitidos: {', '.join(estados_validos)}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Guardar estado anterior para actividad
        estado_anterior = tarea.estado

        # Actualizar estado
        tarea.estado = nuevo_estado
        tarea.save(update_fields=["estado", "fechamodificacion"])

        # Registrar actividad si es posible
        try:
            from dashboard.models import Actividad

            Actividad.objects.create(
                nombre=f"Cambio de estado de tarea #{tarea.idtarea}",
                descripcion=f"Estado actualizado de '{estado_anterior}' a '{nuevo_estado}'",
                idusuario=request.user,
                accion="cambio_estado",
                entidad_tipo="Tarea",
                entidad_id=tarea.idtarea,
            )
        except Exception:
            pass  # No interrumpir el flujo si falla el registro de actividad

        return Response({"detail": "Estado actualizado con éxito"})

    @action(
        detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated]
    )
    def parameterize(self, request, pk=None):
        """
        Connect to external API to parameterize a task with AI assistance.
        Updates the task with parameters like estimated duration, tags, complexity, etc.
        """
        tarea = self.get_object()

        # Configure the API endpoint
        api_base_url = request.data.get("api_url", "http://localhost:3000/api")
        api_endpoint = f"{api_base_url}/tasks/{tarea.idtarea}/parameterize"

        try:
            # Get token from environment variable
            token = os.environ.get("API_INTERMEDIARIA_TOKEN")

            # Set up headers with authorization token
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info(f"Using API token from environment variable")
            else:
                logger.warning(
                    "API_INTERMEDIARIA_TOKEN not found in environment variables"
                )

            # Make the request to the external API with auth headers
            response = requests.get(api_endpoint, headers=headers, timeout=10)
            response.raise_for_status()  # Raise exception for non-200 responses

            data = response.json()

            if not data.get("success"):
                return Response(
                    {
                        "error": "API call was unsuccessful",
                        "details": data.get("message", "Unknown error"),
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            # Extract data from the response
            task_data = data.get("data", {})

            # Process and update task fields based on the response
            updates = {}

            # Update task name if provided
            if "tarea" in task_data:
                updates["nombretarea"] = task_data["tarea"]

            # Update task type if provided
            if "tipo" in task_data:
                tipo_nombre = task_data["tipo"]
                # Try to find an existing task type or create a new one
                tipo_tarea, created = TipoTarea.objects.get_or_create(
                    nombre__iexact=tipo_nombre, defaults={"nombre": tipo_nombre}
                )
                updates["tipo_tarea"] = tipo_tarea

            # Update tags if provided
            if "palabras_clave" in task_data and isinstance(
                task_data["palabras_clave"], list
            ):
                # Convert list to comma-separated string
                updates["tags"] = ",".join(task_data["palabras_clave"])

            # Update complexity/difficulty if provided
            if "complejidad" in task_data:
                # Map text values to numeric values
                complexity_map = {
                    "Baja": 1,
                    "Media": 2,
                    "Alta": 3,
                    "Muy Alta": 4,
                    "Extrema": 5,
                }
                difficulty = complexity_map.get(task_data["complejidad"], None)
                if difficulty:
                    updates["dificultad"] = difficulty

            # Update estimated duration if provided
            if "tiempo_estimado" in task_data:
                try:
                    # Extract numeric value from strings like "8 días"
                    tiempo_str = task_data["tiempo_estimado"]
                    # Basic parsing - extract the first number found
                    import re

                    time_value = re.search(r"\d+", tiempo_str)
                    if time_value:
                        updates["duracionestimada"] = int(time_value.group())
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse tiempo_estimado: {e}")

            # Update clarity of requirements if provided
            if "claridad_requisitos" in task_data:
                try:
                    # Convert percentage string like "85%" to float 0.85
                    claridad_str = task_data["claridad_requisitos"]
                    claridad_value = float(claridad_str.strip("%")) / 100
                    updates["claridad_requisitos"] = claridad_value
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse claridad_requisitos: {e}")

            # Update story points / estimated size if provided
            if "puntos_historia" in task_data:
                try:
                    puntos = int(task_data["puntos_historia"])
                    updates["tamaño_estimado"] = puntos
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse puntos_historia: {e}")

            # Update last modification date
            updates["fechamodificacion"] = datetime.now()

            # Apply all updates to the task
            for field, value in updates.items():
                setattr(tarea, field, value)

            tarea.save()

            # Optional: Record this activity
            try:
                from dashboard.models import Actividad

                Actividad.objects.create(
                    nombre=f"Parametrización automática de tarea #{tarea.idtarea}",
                    descripcion=f"Se parametrizó la tarea {tarea.nombretarea} usando IA",
                    idusuario=request.user,
                    accion="parametrizar",
                    entidad_tipo="Tarea",
                    entidad_id=tarea.idtarea,
                )
            except Exception as e:
                logger.warning(f"Failed to record activity: {e}")

            # Return updated task data
            serializer = TareaSerializer(tarea)
            return Response(
                {
                    "message": "Task successfully parameterized",
                    "updated_fields": list(updates.keys()),
                    "task": serializer.data,
                }
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return Response(
                {"error": f"Failed to connect to parameterization API: {str(e)}"},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"Task parameterization error: {e}", exc_info=True)
            return Response(
                {"error": f"Error during task parameterization: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
