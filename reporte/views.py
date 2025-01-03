from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from django.core.cache import cache
from dashboard.models import (
    Proyecto,
    Tarea,
    Recurso,
    Historialtarea,
)
import csv
import json
from django.template.loader import render_to_string
from datetime import timedelta
from weasyprint import HTML


@login_required
def index(request):
    """Vista principal de reportes"""
    try:
        # Cache los resultados para evitar múltiples consultas
        cache_key = f"reporte_data_{request.user.idusuario}"
        cached_data = cache.get(cache_key)

        if cached_data:
            return render(request, "reportes/index.html", cached_data)

        # Obtener parámetros de filtro con valores por defecto
        fecha_inicio = request.GET.get(
            "fecha_inicio", (timezone.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        )
        fecha_fin = request.GET.get("fecha_fin", timezone.now().strftime("%Y-%m-%d"))
        proyecto_id = request.GET.get("proyecto")
        tipo_reporte = request.GET.get("tipo_reporte", "general")

        # Query base optimizada con select_related
        tareas = Tarea.objects.select_related(
            "idrequerimiento", "idrequerimiento__idproyecto"
        ).prefetch_related("tarearecurso_set", "tarearecurso_set__idrecurso")

        # Aplicar filtros de manera eficiente
        if fecha_inicio:
            tareas = tareas.filter(fechacreacion__gte=fecha_inicio)
        if fecha_fin:
            tareas = tareas.filter(fechacreacion__lte=fecha_fin)
        if proyecto_id:
            tareas = tareas.filter(idrequerimiento__idproyecto_id=proyecto_id)

        # Calcular estadísticas
        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": tareas.aggregate(total=Sum("duracionactual"))["total"] or 0,
            "costo_total": tareas.aggregate(total=Sum("costoactual"))["total"] or 0,
        }

        # Obtener proyectos una sola vez
        proyectos = Proyecto.objects.all().order_by("nombreproyecto")

        # Preparar contexto base
        context = {
            "proyectos": proyectos,
            "estadisticas": estadisticas,
            "filtros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "proyecto": proyecto_id,
                "tipo_reporte": tipo_reporte,
            },
        }

        # Agregar datos específicos según tipo de reporte
        if tipo_reporte == "recursos":
            context["datos_recursos"] = calcular_estadisticas_recursos(tareas)
        elif tipo_reporte == "costos":
            context["datos_costos"] = calcular_estadisticas_costos(tareas)
        else:  # tipo_reporte == "general"
            context["datos_generales"] = calcular_estadisticas_generales(tareas)
            context["historial"] = Historialtarea.objects.select_related(
                "idtarea", "idtarea__idrequerimiento__idproyecto"
            ).order_by("-fechacambio")[:10]

        # Cachear los resultados por 5 minutos
        cache.set(cache_key, context, 300)

        return render(request, "reportes/index.html", context)

    except Exception as e:
        messages.error(request, f"Error al generar reporte: {str(e)}")
        return redirect("dashboard:index")


def calcular_estadisticas_recursos(tareas):
    return {
        "labels": list(
            tareas.values_list("idrequerimiento__idproyecto__nombreproyecto", flat=True)
        ),
        "horas_asignadas": list(tareas.values_list("duracionestimada", flat=True)),
        "horas_utilizadas": list(tareas.values_list("duracionactual", flat=True)),
    }


def calcular_estadisticas_costos(tareas):
    """Calcula las estadísticas de costos para el reporte"""
    # Calcular totales
    total_estimado = sum(t.costoestimado or 0 for t in tareas)
    total_actual = sum(t.costoactual or 0 for t in tareas)

    # Calcular variación total
    variacion_total = (
        ((total_actual - total_estimado) / total_estimado * 100)
        if total_estimado > 0
        else 0
    )

    # Calcular porcentaje utilizado
    porcentaje_utilizado = (
        (total_actual / total_estimado * 100) if total_estimado > 0 else 0
    )

    # Calcular índice de eficiencia
    indice_eficiencia = total_estimado / total_actual if total_actual > 0 else 0

    # Agrupar datos por período
    periodos = []
    for tarea in tareas:
        periodo = {
            "fecha": tarea.fechacreacion.strftime("%b %Y"),
            "estimado": tarea.costoestimado or 0,
            "actual": tarea.costoactual or 0,
            "variacion": (
                ((tarea.costoactual - tarea.costoestimado) / tarea.costoestimado * 100)
                if tarea.costoestimado and tarea.costoestimado > 0
                else 0
            ),
        }
        periodos.append(periodo)

    return {
        "total_estimado": total_estimado,
        "total_actual": total_actual,
        "variacion_total": variacion_total,
        "porcentaje_utilizado": porcentaje_utilizado,
        "indice_eficiencia": indice_eficiencia,
        "periodos": periodos,
        "periodo": (
            f"{periodos[0]['fecha']} - {periodos[-1]['fecha']}"
            if periodos
            else "No hay datos"
        ),
    }


def calcular_estadisticas_generales(tareas):
    """Calcula las estadísticas generales para el reporte"""
    # Obtener totales generales
    total_completadas = tareas.filter(estado="Completada").count()
    total_en_progreso = tareas.filter(estado="En Progreso").count()
    total_pendientes = tareas.filter(estado="Pendiente").count()

    # Agrupar por proyecto
    proyectos = []
    for proyecto in Proyecto.objects.filter(requerimiento__tarea__in=tareas).distinct():
        tareas_proyecto = tareas.filter(idrequerimiento__idproyecto=proyecto)
        completadas = tareas_proyecto.filter(estado="Completada").count()
        en_progreso = tareas_proyecto.filter(estado="En Progreso").count()
        pendientes = tareas_proyecto.filter(estado="Pendiente").count()
        total = completadas + en_progreso + pendientes

        proyectos.append(
            {
                "nombre": proyecto.nombreproyecto,
                "completadas": completadas,
                "en_progreso": en_progreso,
                "pendientes": pendientes,
                "porcentaje_completado": round(
                    (completadas / total * 100) if total > 0 else 0, 1
                ),
            }
        )

    return {
        "total_completadas": total_completadas,
        "total_en_progreso": total_en_progreso,
        "total_pendientes": total_pendientes,
        "proyectos": sorted(
            proyectos, key=lambda x: x["porcentaje_completado"], reverse=True
        ),
    }


def calcular_estadisticas_recursos(tareas):
    """Calcula las estadísticas de recursos para el reporte"""
    recursos_data = []
    total_asignadas = 0
    total_utilizadas = 0

    # Obtener todos los recursos utilizados en las tareas
    recursos = Recurso.objects.filter(tarearecurso__idtarea__in=tareas).distinct()

    for recurso in recursos:
        # Calcular horas asignadas y utilizadas para cada recurso
        asignaciones = recurso.tarearecurso_set.filter(idtarea__in=tareas)
        horas_asignadas = sum(a.horasasignadas or 0 for a in asignaciones)
        horas_utilizadas = sum(a.horasutilizadas or 0 for a in asignaciones)

        # Calcular eficiencia
        eficiencia = (
            (horas_utilizadas / horas_asignadas * 100) if horas_asignadas > 0 else 0
        )

        recursos_data.append(
            {
                "nombre": recurso.nombrerecurso,
                "tipo": "Humano" if hasattr(recurso, "recursohumano") else "Material",
                "horas_asignadas": horas_asignadas,
                "horas_utilizadas": horas_utilizadas,
                "eficiencia": round(eficiencia, 1),
            }
        )

        total_asignadas += horas_asignadas
        total_utilizadas += horas_utilizadas

    return {
        "recursos": sorted(
            recursos_data, key=lambda x: x["horas_asignadas"], reverse=True
        ),
        "total_horas_asignadas": total_asignadas,
        "total_horas_utilizadas": total_utilizadas,
    }


@login_required
def exportar_csv(request):
    """Exportar datos a CSV"""
    try:
        # Obtener filtros del formulario
        filtros = json.loads(request.POST.get("filtros", "{}"))

        # Aplicar filtros a la consulta
        tareas = Tarea.objects.select_related("idrequerimiento__idproyecto")

        if filtros.get("proyecto"):
            tareas = tareas.filter(idrequerimiento__idproyecto_id=filtros["proyecto"])
        if filtros.get("fecha_inicio"):
            tareas = tareas.filter(fechacreacion__gte=filtros["fecha_inicio"])
        if filtros.get("fecha_fin"):
            tareas = tareas.filter(fechacreacion__lte=filtros["fecha_fin"])

        # Crear response HTTP con tipo CSV
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="reporte.csv"'

        # Crear writer CSV
        writer = csv.writer(response)
        writer.writerow(
            [
                "Tarea",
                "Proyecto",
                "Estado",
                "Duración Estimada",
                "Duración Actual",
                "Costo Estimado",
                "Costo Actual",
                "Fecha Inicio",
                "Fecha Fin",
            ]
        )

        # Escribir datos
        for tarea in tareas:
            writer.writerow(
                [
                    tarea.nombretarea,
                    tarea.idrequerimiento.idproyecto.nombreproyecto,
                    tarea.estado,
                    tarea.duracionestimada or 0,
                    tarea.duracionactual or 0,
                    tarea.costoestimado or 0,
                    tarea.costoactual or 0,
                    tarea.fechainicio,
                    tarea.fechafin,
                ]
            )

        return response

    except Exception as e:
        return JsonResponse({"error": f"Error al exportar CSV: {str(e)}"}, status=500)


@login_required
def exportar_pdf(request):
    """Exportar datos a PDF"""
    try:
        # Obtener filtros del formulario
        filtros = json.loads(request.POST.get("filtros", "{}"))

        # Aplicar filtros a la consulta
        tareas = Tarea.objects.select_related("idrequerimiento__idproyecto")

        if filtros.get("proyecto"):
            tareas = tareas.filter(idrequerimiento__idproyecto_id=filtros["proyecto"])
        if filtros.get("fecha_inicio"):
            tareas = tareas.filter(fechacreacion__gte=filtros["fecha_inicio"])
        if filtros.get("fecha_fin"):
            tareas = tareas.filter(fechacreacion__lte=filtros["fecha_fin"])

        # Calcular estadísticas
        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": sum(t.duracionactual or 0 for t in tareas),
            "costo_total": sum(t.costoactual or 0 for t in tareas),
        }

        # Renderizar template HTML
        html = render_to_string(
            "reportes/pdf_template.html",
            {
                "tareas": tareas,
                "estadisticas": estadisticas,
                "fecha_generacion": timezone.now(),
                "filtros": filtros,
            },
        )

        # Crear PDF
        pdf = HTML(string=html).write_pdf()

        # Crear response
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte.pdf"'

        return response

    except Exception as e:
        return JsonResponse({"error": f"Error al exportar PDF: {str(e)}"}, status=500)


@login_required
def filtrar_historial(request):
    """Vista para filtrar el historial de tareas"""
    try:
        # Obtener parámetros de filtro
        tipo_filtro = request.GET.get("tipo_filtro", "todos")
        proyecto_id = request.GET.get("proyecto")
        page = request.GET.get("page", 1)

        # Query base optimizada
        historial = Historialtarea.objects.select_related(
            "idtarea", "idtarea__idrequerimiento__idproyecto"
        ).order_by("-fechacambio")

        # Aplicar filtros
        if tipo_filtro == "estado":
            historial = historial.filter(descripcioncambio__icontains="estado")
        elif tipo_filtro == "asignacion":
            historial = historial.filter(descripcioncambio__icontains="asign")
        elif tipo_filtro == "recursos":
            historial = historial.filter(descripcioncambio__icontains="recurs")

        if proyecto_id:
            historial = historial.filter(
                idtarea__idrequerimiento__idproyecto_id=proyecto_id
            )

        # Paginación
        paginator = Paginator(historial, 10)
        historial_paginado = paginator.get_page(page)

        # Obtener proyectos para el filtro
        proyectos = Proyecto.objects.all()

        context = {
            "historial": historial_paginado,
            "proyectos": proyectos,
            "filtro_actual": tipo_filtro,
            "proyecto_actual": proyecto_id,
        }

        return render(request, "components/historial_tareas.html", context)

    except Exception as e:
        messages.error(request, f"Error al filtrar historial: {str(e)}")
        return redirect("reportes:index")
