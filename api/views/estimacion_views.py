from rest_framework import views, status
from rest_framework.response import Response
from rest_framework.decorators import (
    api_view,
    permission_classes,
    authentication_classes,
)
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
import logging

from api.serializers.estimacion_serializers import (
    EstimacionTareaInputSerializer,
    EstimacionResultadoSerializer,
)
from dashboard.models import Tarea, Resultadosrnn, Modeloestimacionrnn
from redes_neuronales.services import EstimacionService

logger = logging.getLogger(__name__)


class EstimacionTareaView(views.APIView):
    """
    API endpoint para estimar el tiempo de una tarea usando redes neuronales
    """

    permission_classes = [IsAuthenticated]
    authentication_classes = [TokenAuthentication, SessionAuthentication]

    def post(self, request):
        """Recibe los datos de la tarea y devuelve una estimación de tiempo"""
        serializer = EstimacionTareaInputSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Obtener servicio de estimación (singleton)
            estimacion_service = EstimacionService()

            # Obtener datos de la tarea
            tarea_data = serializer.get_task_data(serializer.validated_data)

            # Realizar estimación
            resultado = estimacion_service.estimar_tiempo_tarea(tarea_data)

            # Si se proporcionó una ID de tarea, guardar el resultado en la base de datos
            if (
                "idtarea" in serializer.validated_data
                and serializer.validated_data["idtarea"]
            ):
                try:
                    idtarea = serializer.validated_data["idtarea"]
                    tarea = Tarea.objects.get(idtarea=idtarea)

                    # Obtener o crear modelo de estimación en BD
                    modelo, _ = Modeloestimacionrnn.objects.get_or_create(
                        nombremodelo=resultado["modelo"],
                        defaults={
                            "descripcionmodelo": "Modelo de estimación de tiempo con red neuronal",
                            "precision": resultado["confianza"],
                        },
                    )

                    # Guardar resultado
                    Resultadosrnn.objects.update_or_create(
                        idtarea=tarea,
                        idmodelo=modelo.idmodelo,
                        defaults={
                            "duracionestimada": resultado["tiempo_estimado"],
                            "timestamp": timezone.now(),
                            "recursos": str(tarea_data.get("Cantidad_Recursos")),
                        },
                    )

                    # Opcionalmente, actualizar la tarea con la duración estimada
                    if not tarea.duracionestimada:
                        tarea.duracionestimada = int(resultado["tiempo_estimado"])
                        tarea.save(update_fields=["duracionestimada"])

                except Exception as e:
                    logger.error(f"Error al guardar resultado de estimación: {e}")
                    # No interrumpir el flujo si falla el guardado

            # Devolver resultado serializado
            resultado_serializer = EstimacionResultadoSerializer(resultado)
            return Response(resultado_serializer.data)

        except Exception as e:
            logger.error(f"Error en estimación de tiempo: {e}")
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(["POST"])
@authentication_classes([TokenAuthentication, SessionAuthentication])
@permission_classes([IsAuthenticated])
def estimar_tiempo_bulk(request):
    """
    Endpoint para estimar tiempo de múltiples tareas de un proyecto o requerimiento
    """
    id_proyecto = request.data.get("idproyecto")
    id_requerimiento = request.data.get("idrequerimiento")

    if not id_proyecto and not id_requerimiento:
        return Response(
            {"error": "Se requiere idproyecto o idrequerimiento"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Obtener tareas según filtro
        if id_proyecto:
            tareas = Tarea.objects.filter(
                idrequerimiento__idproyecto__idproyecto=id_proyecto
            )
        else:
            tareas = Tarea.objects.filter(idrequerimiento=id_requerimiento)

        if not tareas.exists():
            return Response(
                {"mensaje": "No hay tareas para estimar"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Obtener servicio de estimación
        estimacion_service = EstimacionService()

        resultados = []
        for tarea in tareas:
            # Obtener datos serializados de la tarea
            input_serializer = EstimacionTareaInputSerializer(
                data={"idtarea": tarea.idtarea}
            )
            if input_serializer.is_valid():
                try:
                    # Realizar estimación
                    tarea_data = input_serializer.get_task_data(
                        {"idtarea": tarea.idtarea}
                    )
                    resultado = estimacion_service.estimar_tiempo_tarea(tarea_data)

                    # Crear objeto de resultado
                    resultado_item = {
                        "idtarea": tarea.idtarea,
                        "nombretarea": tarea.nombretarea,
                        "estimacion": resultado,
                    }
                    resultados.append(resultado_item)

                    # Opcionalmente guardar resultados en BD
                    # Código similar al anterior endpoint

                except Exception as e:
                    logger.error(f"Error estimando tarea {tarea.idtarea}: {e}")
                    resultados.append(
                        {
                            "idtarea": tarea.idtarea,
                            "nombretarea": tarea.nombretarea,
                            "error": str(e),
                        }
                    )

        return Response({"tareas_estimadas": len(resultados), "resultados": resultados})

    except Exception as e:
        logger.error(f"Error en estimación masiva: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
