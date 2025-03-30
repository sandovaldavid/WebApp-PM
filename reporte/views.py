import csv
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Q, Count
from django.db.models.functions import TruncMonth, Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from weasyprint import HTML

from dashboard.models import (
    Proyecto,
    Tarea,
    Historialtarea,
)


@login_required
def index(request):
    """Vista principal de reportes que muestra estadísticas en un rango de fechas"""
    try:
        # Obtener fechas del request o usar valores por defecto
        fecha_fin = parse_date(request.GET.get("fecha_fin"), default=timezone.now())
        fecha_inicio = parse_date(
            request.GET.get("fecha_inicio"), default=fecha_fin - timedelta(days=30)
        )

        # Obtener otros filtros
        proyecto_id = request.GET.get("proyecto")
        tipo_reporte = request.GET.get("tipo_reporte", "general")

        # Query base optimizada
        tareas = Tarea.objects.all()
        # Aplicar filtros de fecha
        tareas = tareas.filter(fechacreacion__range=(fecha_inicio, fecha_fin))

        # Aplicar filtro de proyecto si existe
        if proyecto_id:
            tareas = tareas.filter(idrequerimiento__idproyecto_id=proyecto_id)

        # Calcular estadísticas básicas con tipos de datos consistentes
        decimal_field = models.DecimalField(max_digits=10, decimal_places=2)

        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": tareas.aggregate(
                total=Coalesce(
                    Sum("duracionactual", output_field=decimal_field),
                    0.0,
                    output_field=decimal_field,
                )
            )["total"],
            "costo_total": tareas.aggregate(
                total=Coalesce(
                    Sum("costoactual", output_field=decimal_field),
                    0.0,
                    output_field=decimal_field,
                )
            )["total"],
        }

        # Preparar contexto según tipo de reporte
        context = prepare_context(
            tareas=tareas,
            tipo_reporte=tipo_reporte,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            proyecto_id=proyecto_id,
            estadisticas=estadisticas,
        )

        return render(request, "reportes/index.html", context)

    except Exception as e:
        messages.error(request, f"Error al generar reporte: {str(e)}")
        return redirect("dashboard:panel_control")


def parse_date(date_str, default=None):
    """Convierte string a fecha aware o retorna valor por defecto"""
    if not date_str:
        return default

    try:
        fecha = datetime.strptime(date_str, "%Y-%m-%d")
        return timezone.make_aware(
            datetime.combine(
                fecha, datetime.min.time() if fecha == fecha else datetime.max.time()
            )
        )
    except ValueError:
        return default


def calcular_estadisticas_base(tareas):
    """Calcula las estadísticas básicas de las tareas"""
    return {
        "total_tareas": tareas.count(),
        "tareas_completadas": tareas.filter(estado="Completada").count(),
        "total_horas": tareas.aggregate(
            total=Coalesce(
                Sum("duracionactual", output_field=models.DecimalField()),
                0,
                output_field=models.DecimalField(),
            )
        )["total"],
        "costo_total": tareas.aggregate(
            total=Coalesce(
                Sum("costoactual", output_field=models.DecimalField()),
                0,
                output_field=models.DecimalField(),
            )
        )["total"],
    }


def prepare_context(
    tareas, tipo_reporte, fecha_inicio, fecha_fin, proyecto_id, estadisticas
):
    """Prepara el contexto según el tipo de reporte"""
    context = {
        "proyectos": Proyecto.objects.all().order_by("nombreproyecto"),
        "estadisticas": {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": tareas.aggregate(
                total=Coalesce(
                    Sum(
                        "duracionactual",
                        output_field=models.DecimalField(
                            max_digits=10, decimal_places=2
                        ),
                    ),
                    0.0,
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            )["total"],
            "costo_total": tareas.aggregate(
                total=Coalesce(
                    Sum(
                        "costoactual",
                        output_field=models.DecimalField(
                            max_digits=10, decimal_places=2
                        ),
                    ),
                    0.0,
                    output_field=models.DecimalField(max_digits=10, decimal_places=2),
                )
            )["total"],
        },
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

    return context


def calcular_estadisticas_recursos(tareas):
    """Calcula estadísticas relacionadas con los recursos y su utilización"""
    recursos = (
        tareas.values(
            "tarearecurso__idrecurso__nombrerecurso",
            "tarearecurso__idrecurso__idtiporecurso__nametiporecurso",
        )
        .annotate(
            horas_asignadas=Coalesce(
                Sum("duracionestimada"), 0, output_field=models.DecimalField()
            ),
            horas_utilizadas=Coalesce(
                Sum("duracionactual"), 0, output_field=models.DecimalField()
            ),
        )
        .filter(tarearecurso__isnull=False)
    )

    return {
        "total_horas_asignadas": sum(r["horas_asignadas"] for r in recursos),
        "total_horas_utilizadas": sum(r["horas_utilizadas"] for r in recursos),
        "recursos": [
            {
                "nombre": r["tarearecurso__idrecurso__nombrerecurso"],
                "tipo": r["tarearecurso__idrecurso__idtiporecurso__nametiporecurso"],
                "horas_asignadas": r["horas_asignadas"],
                "horas_utilizadas": r["horas_utilizadas"],
                "eficiencia": round(
                    (
                        (r["horas_utilizadas"] / r["horas_asignadas"] * 100)
                        if r["horas_asignadas"] > 0
                        else 0
                    ),
                    2,
                ),
            }
            for r in recursos
        ],
    }


def calcular_estadisticas_costos(tareas):
    """Calcula estadísticas relacionadas con los costos y presupuestos"""
    # Calcular totales con valores por defecto
    totales = tareas.aggregate(
        total_estimado=Coalesce(
            Sum("costoestimado"), 0, output_field=models.DecimalField()
        ),
        total_actual=Coalesce(
            Sum("costoactual"), 0, output_field=models.DecimalField()
        ),
    )

    total_estimado = totales["total_estimado"]
    total_actual = totales["total_actual"]

    # Calcular métricas
    variacion_total = (
        ((total_actual - total_estimado) / total_estimado * 100)
        if total_estimado > 0
        else 0
    )

    # Agrupar por períodos mensuales
    periodos = (
        tareas.annotate(mes=TruncMonth("fechacreacion"))
        .values("mes")
        .annotate(
            estimado=Coalesce(
                Sum("costoestimado"), 0, output_field=models.DecimalField()
            ),
            actual=Coalesce(Sum("costoactual"), 0, output_field=models.DecimalField()),
        )
        .order_by("mes")
    )

    return {
        "total_estimado": total_estimado,
        "total_actual": total_actual,
        "variacion_total": round(variacion_total, 2),
        "porcentaje_utilizado": round(
            (total_actual / total_estimado * 100) if total_estimado > 0 else 0, 2
        ),
        "indice_eficiencia": round(
            total_estimado / total_actual if total_actual > 0 else 0, 2
        ),
        "periodos": [
            {
                "fecha": p["mes"].strftime("%b %Y"),
                "estimado": p["estimado"],
                "actual": p["actual"],
                "variacion": round(
                    (
                        ((p["actual"] - p["estimado"]) / p["estimado"] * 100)
                        if p["estimado"] > 0
                        else 0
                    ),
                    2,
                ),
            }
            for p in periodos
        ],
    }


def calcular_estadisticas_generales(tareas):
    """Calcula estadísticas generales del progreso de tareas por proyecto"""
    # Estadísticas generales de tareas
    totales = tareas.aggregate(
        total_completadas=Count("idtarea", filter=Q(estado="Completada")),
        total_en_progreso=Count("idtarea", filter=Q(estado="En Progreso")),
        total_pendientes=Count("idtarea", filter=Q(estado="Pendiente")),
    )

    # Estadísticas por proyecto
    proyectos = (
        tareas.values(
            "idrequerimiento__idproyecto__idproyecto",
            "idrequerimiento__idproyecto__nombreproyecto",
        )
        .annotate(
            total=Count("idtarea"),
            completadas=Count("idtarea", filter=Q(estado="Completada")),
            en_progreso=Count("idtarea", filter=Q(estado="En Progreso")),
            pendientes=Count("idtarea", filter=Q(estado="Pendiente")),
        )
        .filter(total__gt=0)
    )

    return {
        "total_completadas": totales["total_completadas"],
        "total_en_progreso": totales["total_en_progreso"],
        "total_pendientes": totales["total_pendientes"],
        "proyectos": [
            {
                "nombre": p["idrequerimiento__idproyecto__nombreproyecto"],
                "completadas": p["completadas"],
                "en_progreso": p["en_progreso"],
                "pendientes": p["pendientes"],
                "porcentaje_completado": round(
                    (p["completadas"] / p["total"] * 100) if p["total"] > 0 else 0, 1
                ),
            }
            for p in proyectos
        ],
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
        tareas = Tarea.objects.select_related("idrequerimiento__idproyecto").all()

        if filtros.get("proyecto"):
            tareas = tareas.filter(idrequerimiento__idproyecto_id=filtros["proyecto"])
        if filtros.get("fecha_inicio"):
            tareas = tareas.filter(fechacreacion__gte=filtros["fecha_inicio"])
        if filtros.get("fecha_fin"):
            tareas = tareas.filter(fechacreacion__lte=filtros["fecha_fin"])

        # Definir campo decimal con parámetros específicos
        decimal_field = models.DecimalField(max_digits=10, decimal_places=2)

        # Calcular estadísticas con manejo de valores nulos y tipo de campo consistente
        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "total_horas": tareas.aggregate(
                total=Coalesce(
                    Sum("duracionactual", output_field=decimal_field),
                    0.0,
                    output_field=decimal_field,
                )
            )["total"],
            "costo_total": tareas.aggregate(
                total=Coalesce(
                    Sum("costoactual", output_field=decimal_field),
                    0.0,
                    output_field=decimal_field,
                )
            )["total"],
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
        pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf()

        # Crear response
        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = 'attachment; filename="reporte.pdf"'

        return response

    except Exception as e:
        print(f"Error al exportar PDF: {str(e)}")  # Para debugging
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
