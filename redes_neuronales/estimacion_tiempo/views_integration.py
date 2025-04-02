from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import json
import logging

from . import get_estimacion_service
from dashboard.models import Tarea, Proyecto

logger = logging.getLogger(__name__)


@login_required
@require_http_methods(["POST"])
def estimate_task_api(request):
    """API para estimar el tiempo de una tarea"""
    try:
        data = json.loads(request.body)
        tarea_id = data.get("tarea_id")

        if not tarea_id:
            return JsonResponse(
                {"status": "error", "message": "Se requiere ID de tarea"}, status=400
            )

        # Verificar que la tarea existe
        try:
            tarea = Tarea.objects.get(idtarea=tarea_id)
        except Tarea.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": f"No existe tarea con ID {tarea_id}"},
                status=404,
            )

        # Obtener el servicio y realizar estimación
        service = get_estimacion_service()
        success, estimated_time, message = service.estimate_and_save(tarea_id)

        if not success:
            return JsonResponse({"status": "error", "message": message}, status=500)

        return JsonResponse(
            {
                "status": "success",
                "tarea_id": tarea_id,
                "tiempo_estimado": estimated_time,
                "message": message,
            }
        )

    except Exception as e:
        logger.error(f"Error en API de estimación: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"Error interno: {str(e)}"}, status=500
        )


@login_required
@require_http_methods(["POST"])
def reestimate_task_api(request):
    """API para reestimar una tarea tras cambios"""
    try:
        data = json.loads(request.body)
        tarea_id = data.get("tarea_id")

        if not tarea_id:
            return JsonResponse(
                {"status": "error", "message": "Se requiere ID de tarea"}, status=400
            )

        # Verificar que la tarea existe
        try:
            tarea = Tarea.objects.get(idtarea=tarea_id)
        except Tarea.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": f"No existe tarea con ID {tarea_id}"},
                status=404,
            )

        # Reestimar tarea
        service = get_estimacion_service()
        result = service.reestimate_after_changes(tarea_id)

        if result["status"] == "error":
            return JsonResponse(
                {"status": "error", "message": result["message"]}, status=500
            )

        return JsonResponse({"status": "success", "data": result})

    except Exception as e:
        logger.error(f"Error en API de reestimación: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"Error interno: {str(e)}"}, status=500
        )


@login_required
def project_estimation_api(request, proyecto_id):
    """API para estimar completitud de un proyecto"""
    try:
        # Verificar que el proyecto existe
        try:
            proyecto = Proyecto.objects.get(idproyecto=proyecto_id)
        except Proyecto.DoesNotExist:
            return JsonResponse(
                {
                    "status": "error",
                    "message": f"No existe proyecto con ID {proyecto_id}",
                },
                status=404,
            )

        # Estimar proyecto
        service = get_estimacion_service()
        result = service.estimate_project_completion(proyecto_id)

        if result is None:
            return JsonResponse(
                {"status": "error", "message": "No se pudo estimar el proyecto"},
                status=500,
            )

        return JsonResponse({"status": "success", "data": result})

    except Exception as e:
        logger.error(f"Error en API de estimación de proyecto: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": f"Error interno: {str(e)}"}, status=500
        )
