from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Sum
from django.db.models.functions import TruncMonth
from django.core.paginator import Paginator
from dashboard.models import (
    Proyecto,
    Tarea,
    Historialreporte,
    Reporte,
    Tarearecurso,
    Recurso,
    Requerimiento,
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
        # Obtener parámetros de filtro
        fecha_inicio = request.GET.get("fecha_inicio")
        fecha_fin = request.GET.get("fecha_fin")
        proyecto_id = request.GET.get("proyecto")
        tipo_reporte = request.GET.get("tipo_reporte", "general")

        # Si no hay fechas, usar último mes
        if not fecha_fin:
            fecha_fin = timezone.now()
        if not fecha_inicio:
            fecha_inicio = fecha_fin - timedelta(days=30)

        # Query base
        tareas = Tarea.objects.select_related("idrequerimiento__idproyecto")

        # Aplicar filtros
        if proyecto_id:
            tareas = tareas.filter(idrequerimiento__idproyecto_id=proyecto_id)
        if fecha_inicio:
            tareas = tareas.filter(fechacreacion__gte=fecha_inicio)
        if fecha_fin:
            tareas = tareas.filter(fechacreacion__lte=fecha_fin)

        # Estadísticas generales
        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": sum(t.duracionactual or 0 for t in tareas),
            "costo_total": sum(t.costoactual or 0 for t in tareas),
        }

        # Datos para el gráfico de progreso
        proyectos = Proyecto.objects.all()
        datos_progreso = {
            "labels": [],
            "completadas": [],
            "en_progreso": [],
            "pendientes": [],
        }

        for proyecto in proyectos:
            tareas_proyecto = tareas.filter(idrequerimiento__idproyecto=proyecto)

            datos_progreso["labels"].append(proyecto.nombreproyecto)
            datos_progreso["completadas"].append(
                tareas_proyecto.filter(estado="Completada").count()
            )
            datos_progreso["en_progreso"].append(
                tareas_proyecto.filter(estado="En Progreso").count()
            )
            datos_progreso["pendientes"].append(
                tareas_proyecto.filter(estado="Pendiente").count()
            )

        # Datos para el gráfico de recursos
        recursos = (
            Tarearecurso.objects.filter(idtarea__in=tareas)
            .values("idrecurso__nombrerecurso")
            .annotate(
                horas_asignadas=Sum("idtarea__duracionestimada"),
                horas_utilizadas=Sum("idtarea__duracionactual"),
            )
            .order_by("-horas_asignadas")
        )

        datos_recursos = {
            "labels": [r["idrecurso__nombrerecurso"] for r in recursos],
            "horas_asignadas": [float(r["horas_asignadas"] or 0) for r in recursos],
            "horas_utilizadas": [float(r["horas_utilizadas"] or 0) for r in recursos],
        }

        # Datos para el historial
        historial = (
            Historialtarea.objects.filter(idtarea__in=tareas)
            .select_related("idtarea__idrequerimiento__idproyecto")
            .order_by("-fechacambio")[:10]
        )

        # Datos para el gráfico de costos
        costos_mensuales = (
            tareas.annotate(mes=TruncMonth("fechacreacion"))
            .values("mes")
            .annotate(
                costo_estimado=Sum("costoestimado"), costo_actual=Sum("costoactual")
            )
            .order_by("mes")
        )

        datos_costos = {"labels": [], "estimado": [], "actual": []}

        for costo in costos_mensuales:
            datos_costos["labels"].append(costo["mes"].strftime("%B %Y"))
            datos_costos["estimado"].append(float(costo["costo_estimado"] or 0))
            datos_costos["actual"].append(float(costo["costo_actual"] or 0))

        # Preparar contexto
        context = {
            "proyectos": proyectos,
            "estadisticas": estadisticas,
            "datos_progreso": datos_progreso,
            "datos_recursos": datos_recursos,
            "historial": historial,
            "datos_costos": datos_costos,
            "filtros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "proyecto": proyecto_id,
                "tipo_reporte": tipo_reporte,
            },
        }

        # Registrar generación del reporte
        Reporte.objects.create(
            tiporeporte=tipo_reporte,
            fechageneracion=timezone.now(),
            idproyecto_id=proyecto_id if proyecto_id else None,
        )

        return render(request, "reportes/index.html", context)

    except Exception as e:
        messages.error(request, f"Error al generar reporte: {str(e)}")
        return redirect("reportes:index")


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
    """Vista para filtrar el historial de tareas via HTMX"""
    try:
        tipo_filtro = request.GET.get("filtro", "todos")
        proyecto_id = request.GET.get("proyecto")

        # Query base
        historial = Historialtarea.objects.select_related(
            "idtarea__idrequerimiento__idproyecto"
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
        page = request.GET.get("page", 1)
        historial_paginado = paginator.get_page(page)

        context = {"historial": historial_paginado}

        return render(request, "reportes/components/historial_tareas.html", context)

    except Exception as e:
        return HttpResponse(
            f'<div class="text-red-500 p-4">Error al filtrar historial: {str(e)}</div>',
            status=500,
        )
