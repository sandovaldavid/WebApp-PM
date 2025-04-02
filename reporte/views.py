import csv
import json
from datetime import datetime, timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import models
from django.db.models import Sum, Q, Count, F, Value, Case, When
from django.db.models.functions import TruncMonth, TruncDay, Coalesce
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.translation import gettext as _
from weasyprint import HTML

from dashboard.models import (
    Proyecto,
    Tarea,
    Historialtarea,
    Actividad,
    DetalleActividad,
    Recurso,
    Tarearecurso,
)


@login_required
def index(request):
    """Vista principal de reportes que muestra estadísticas en un rango de fechas"""
    try:
        # Obtener fechas del request o usar valores por defecto
        fecha_fin = parse_date(
            request.GET.get("fecha_fin"), default=timezone.now().date()
        )
        fecha_inicio = parse_date(
            request.GET.get("fecha_inicio"),
            default=(
                (fecha_fin - timedelta(days=30))
                if fecha_fin
                else timezone.now().date() - timedelta(days=30)
            ),
        )

        # Validar que fecha_inicio no sea posterior a fecha_fin
        if fecha_inicio and fecha_fin and fecha_inicio > fecha_fin:
            messages.warning(
                request,
                _(
                    "La fecha de inicio no puede ser posterior a la fecha de fin. Se han invertido las fechas."
                ),
            )
            # Intercambiar fechas
            fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

        # Obtener otros filtros
        proyecto_id = request.GET.get("proyecto")
        tipo_reporte = request.GET.get("tipo_reporte", "general")

        # Query base optimizada con selects relacionados
        tareas = Tarea.objects.select_related(
            "idrequerimiento", "idrequerimiento__idproyecto"
        )

        # Aplicar filtros de fecha (asegurando que son dates completos)
        if fecha_inicio:
            fecha_inicio_datetime = timezone.make_aware(
                datetime.combine(fecha_inicio, datetime.min.time())
            )
            tareas = tareas.filter(fechacreacion__gte=fecha_inicio_datetime)

        if fecha_fin:
            fecha_fin_datetime = timezone.make_aware(
                datetime.combine(fecha_fin, datetime.max.time())
            )
            tareas = tareas.filter(fechacreacion__lte=fecha_fin_datetime)

        # Aplicar filtro de proyecto si existe
        if proyecto_id:
            proyecto_obj = None
            try:
                proyecto_obj = Proyecto.objects.get(idproyecto=proyecto_id)
                tareas = tareas.filter(idrequerimiento__idproyecto=proyecto_obj)
            except Proyecto.DoesNotExist:
                messages.warning(request, _("El proyecto seleccionado no existe."))

        # Calcular estadísticas básicas con tipos de datos consistentes
        decimal_field = models.DecimalField(max_digits=10, decimal_places=2)

        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "tareas_en_progreso": tareas.filter(estado="En Progreso").count(),
            "tareas_pendientes": tareas.filter(estado="Pendiente").count(),
            "porcentaje_completadas": calculate_percentage(
                tareas.filter(estado="Completada").count(), tareas.count()
            ),
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
            proyecto_obj=proyecto_obj if "proyecto_obj" in locals() else None,
            estadisticas=estadisticas,
            request=request,
        )

        return render(request, "reportes/index.html", context)

    except Exception as e:
        messages.error(request, f"Error al generar reporte: {str(e)}")
        return redirect("dashboard:panel_control")


def parse_date(date_str, default=None):
    """Convierte string a fecha o retorna valor por defecto"""
    if not date_str:
        return default

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return default


def calculate_percentage(part, total):
    """Calcula el porcentaje seguro (evitando división por cero)"""
    return round((part / total) * 100, 2) if total > 0 else 0


def prepare_context(
    tareas,
    tipo_reporte,
    fecha_inicio,
    fecha_fin,
    proyecto_id,
    proyecto_obj,
    estadisticas,
    request,
):
    """Prepara el contexto según el tipo de reporte"""
    context = {
        "proyectos": Proyecto.objects.all().order_by("nombreproyecto"),
        "estadisticas": estadisticas,
        "filtros": {
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "proyecto": proyecto_id,
            "proyecto_obj": proyecto_obj,
            "tipo_reporte": tipo_reporte,
        },
    }

    # Para el reporte general, incluir datos de todos los tipos de reportes
    if tipo_reporte == "general" or not tipo_reporte:
        context["datos_generales"] = calcular_estadisticas_tareas(tareas)
        context["datos_recursos"] = calcular_estadisticas_recursos(tareas)
        context["datos_costos"] = calcular_estadisticas_costos(tareas)

        # Incluir historial para el reporte general
        if Actividad.objects.filter(entidad_tipo="Tarea").exists():
            # Usar el nuevo modelo Actividad
            historial = Actividad.objects.select_related("idusuario").filter(
                entidad_tipo="Tarea",
                entidad_id__in=tareas.values_list("idtarea", flat=True),
            )

            if fecha_inicio and fecha_fin:
                fecha_inicio_dt = timezone.make_aware(
                    datetime.combine(fecha_inicio, datetime.min.time())
                )
                fecha_fin_dt = timezone.make_aware(
                    datetime.combine(fecha_fin, datetime.max.time())
                )
                historial = historial.filter(
                    fechacreacion__range=(fecha_inicio_dt, fecha_fin_dt)
                )

            historial = historial.order_by("-fechacreacion")
        else:
            # Usar el modelo legacy Historialtarea con optimizaciones
            historial = (
                Historialtarea.objects.select_related(
                    "idtarea",
                    "idtarea__idrequerimiento",
                    "idtarea__idrequerimiento__idproyecto",
                )
                .filter(idtarea__in=tareas, idtarea__isnull=False)
                .order_by("-fechacambio")
            )

        # Aplicar paginación
        paginator = Paginator(historial, 10)
        page = request.GET.get("page", 1)

        context["historial"] = paginator.get_page(page)
        context["filtro_actual"] = request.GET.get("tipo_filtro", "todos")
        context["proyecto_actual"] = proyecto_id
        context["using_actividad"] = (
            "idusuario" in dir(historial.first()) if historial.exists() else False
        )

    # Agregar datos específicos según tipo de reporte específico
    elif tipo_reporte == "recursos":
        context["datos_recursos"] = calcular_estadisticas_recursos(tareas)
    elif tipo_reporte == "costos":
        context["datos_costos"] = calcular_estadisticas_costos(tareas)
    else:  # tipo_reporte == "tareas" u otros
        context["datos_generales"] = calcular_estadisticas_tareas(tareas)

        # Determinar qué modelo de historial usar
        if Actividad.objects.filter(entidad_tipo="Tarea").exists():
            # Usar el nuevo modelo Actividad
            historial = Actividad.objects.select_related("idusuario").filter(
                entidad_tipo="Tarea",
                entidad_id__in=tareas.values_list("idtarea", flat=True),
            )

            if fecha_inicio and fecha_fin:
                fecha_inicio_dt = timezone.make_aware(
                    datetime.combine(fecha_inicio, datetime.min.time())
                )
                fecha_fin_dt = timezone.make_aware(
                    datetime.combine(fecha_fin, datetime.max.time())
                )
                historial = historial.filter(
                    fechacreacion__range=(fecha_inicio_dt, fecha_fin_dt)
                )

            historial = historial.order_by("-fechacreacion")
        else:
            # Usar el modelo legacy Historialtarea con optimizaciones
            historial = (
                Historialtarea.objects.select_related(
                    "idtarea",
                    "idtarea__idrequerimiento",
                    "idtarea__idrequerimiento__idproyecto",
                )
                .filter(idtarea__in=tareas, idtarea__isnull=False)
                .order_by("-fechacambio")
            )

        # Aplicar paginación
        paginator = Paginator(historial, 10)
        page = request.GET.get("page", 1)

        context["historial"] = paginator.get_page(page)
        context["filtro_actual"] = request.GET.get("tipo_filtro", "todos")
        context["proyecto_actual"] = proyecto_id
        context["using_actividad"] = (
            "idusuario" in dir(historial.first()) if historial.exists() else False
        )

    return context


def calcular_estadisticas_recursos(tareas):
    """Calcula estadísticas relacionadas con los recursos y su utilización"""
    # Obtener IDs de las tareas filtradas
    tarea_ids = list(tareas.values_list("idtarea", flat=True))

    # Optimizar consulta usando prefetch_related
    tareas_recursos = Tarearecurso.objects.filter(idtarea__in=tarea_ids).select_related(
        "idrecurso", "idrecurso__idtiporecurso", "idtarea"
    )

    # Agrupar datos por recurso
    recursos_data = {}
    for tr in tareas_recursos:
        recurso_id = tr.idrecurso.idrecurso
        if recurso_id not in recursos_data:
            recursos_data[recurso_id] = {
                "nombre": tr.idrecurso.nombrerecurso,
                "tipo": tr.idrecurso.idtiporecurso.nametiporecurso,
                "horas_asignadas": 0,
                "horas_utilizadas": 0,
                "cantidad": tr.cantidad or 1,
            }

        # Sumar horas considerando la cantidad de recursos
        duracion_estimada = tr.idtarea.duracionestimada or 0
        duracion_actual = tr.idtarea.duracionactual or 0

        # Distribuir tiempo según la cantidad de recursos asignados
        recursos_data[recurso_id]["horas_asignadas"] += duracion_estimada * (
            tr.cantidad or 1
        )
        recursos_data[recurso_id]["horas_utilizadas"] += duracion_actual * (
            tr.cantidad or 1
        )

    # Calcular eficiencias
    for recurso in recursos_data.values():
        recurso["eficiencia"] = round(
            (
                (recurso["horas_utilizadas"] / recurso["horas_asignadas"] * 100)
                if recurso["horas_asignadas"] > 0
                else 100
            ),
            2,
        )

    # Convertir a lista para la plantilla
    recursos_list = list(recursos_data.values())

    # Ordenar por eficiencia descendente
    recursos_list.sort(key=lambda x: x["eficiencia"], reverse=True)

    return {
        "total_horas_asignadas": sum(r["horas_asignadas"] for r in recursos_list),
        "total_horas_utilizadas": sum(r["horas_utilizadas"] for r in recursos_list),
        "recursos": recursos_list,
    }


def calcular_estadisticas_costos(tareas):
    """Calcula estadísticas relacionadas con los costos y presupuestos"""
    # Calcular totales con valores por defecto
    totales = tareas.aggregate(
        total_estimado=Coalesce(
            Sum("costoestimado"),
            0,
            output_field=models.DecimalField(max_digits=15, decimal_places=2),
        ),
        total_actual=Coalesce(
            Sum("costoactual"),
            0,
            output_field=models.DecimalField(max_digits=15, decimal_places=2),
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

    # Primero verificar rangos de fecha para agrupar adecuadamente
    fecha_min = tareas.aggregate(min_fecha=models.Min("fechacreacion"))["min_fecha"]
    fecha_max = tareas.aggregate(max_fecha=models.Max("fechacreacion"))["max_fecha"]

    # Si no hay fechas o el rango es menor a 30 días, agrupar por día
    if not fecha_min or not fecha_max or (fecha_max - fecha_min).days < 30:
        # Agrupar por días
        periodos = (
            tareas.annotate(periodo=TruncDay("fechacreacion"))
            .values("periodo")
            .annotate(
                estimado=Coalesce(
                    Sum("costoestimado"),
                    0,
                    output_field=models.DecimalField(max_digits=15, decimal_places=2),
                ),
                actual=Coalesce(
                    Sum("costoactual"),
                    0,
                    output_field=models.DecimalField(max_digits=15, decimal_places=2),
                ),
            )
            .order_by("periodo")
        )
        periodo_str = "diario"
    else:
        # Agrupar por meses
        periodos = (
            tareas.annotate(periodo=TruncMonth("fechacreacion"))
            .values("periodo")
            .annotate(
                estimado=Coalesce(
                    Sum("costoestimado"),
                    0,
                    output_field=models.DecimalField(max_digits=15, decimal_places=2),
                ),
                actual=Coalesce(
                    Sum("costoactual"),
                    0,
                    output_field=models.DecimalField(max_digits=15, decimal_places=2),
                ),
            )
            .order_by("periodo")
        )
        periodo_str = "mensual"

    # Calcular presupuesto del proyecto si hay un proyecto específico
    presupuesto_proyecto = 0
    proyecto_relacionado = None

    if tareas.exists():
        # Intentar obtener el proyecto de la primera tarea
        primera_tarea = tareas.first()
        if primera_tarea:
            proyecto_relacionado = primera_tarea.idrequerimiento.idproyecto
            presupuesto_proyecto = proyecto_relacionado.presupuesto or 0

    # Añadir valores pre-calculados para evitar filtros en la plantilla PDF
    presupuesto_restante = (
        presupuesto_proyecto - total_actual if presupuesto_proyecto > 0 else 0
    )
    porcentaje_restante = (
        100 - round((total_actual / presupuesto_proyecto * 100), 2)
        if presupuesto_proyecto > 0
        else 0
    )

    return {
        "total_estimado": total_estimado,
        "total_actual": total_actual,
        "variacion_total": round(variacion_total, 2),
        "porcentaje_utilizado": round(
            (
                (total_actual / presupuesto_proyecto * 100)
                if presupuesto_proyecto > 0
                else (total_actual / total_estimado * 100) if total_estimado > 0 else 0
            ),
            2,
        ),
        "indice_eficiencia": round(
            total_estimado / total_actual if total_actual > 0 else 0, 2
        ),
        "presupuesto_total": presupuesto_proyecto,
        "presupuesto_restante": presupuesto_restante,  # Valor pre-calculado
        "porcentaje_restante": porcentaje_restante,  # Valor pre-calculado
        "periodo": periodo_str,
        "proyecto": (
            proyecto_relacionado.nombreproyecto
            if proyecto_relacionado
            else "Todos los proyectos"
        ),
        "periodos": [
            {
                "fecha": (
                    p["periodo"].strftime("%d/%m/%Y")
                    if periodo_str == "diario"
                    else p["periodo"].strftime("%b %Y")
                ),
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


def calcular_estadisticas_tareas(tareas):
    """Calcula estadísticas generales del progreso de tareas por proyecto"""
    # Estadísticas generales de tareas
    totales = tareas.aggregate(
        total_completadas=Count("idtarea", filter=Q(estado="Completada")),
        total_en_progreso=Count("idtarea", filter=Q(estado="En Progreso")),
        total_pendientes=Count("idtarea", filter=Q(estado="Pendiente")),
    )

    # Estadísticas por proyecto con optimización
    proyectos = (
        tareas.values(
            "idrequerimiento__idproyecto__idproyecto",
            "idrequerimiento__idproyecto__nombreproyecto",
            "idrequerimiento__idproyecto__fechainicio",
            "idrequerimiento__idproyecto__fechafin",
        )
        .annotate(
            total=Count("idtarea"),
            completadas=Count("idtarea", filter=Q(estado="Completada")),
            en_progreso=Count("idtarea", filter=Q(estado="En Progreso")),
            pendientes=Count("idtarea", filter=Q(estado="Pendiente")),
        )
        .filter(total__gt=0)
    )

    # Enriquecer datos con información adicional
    for proyecto in proyectos:
        # Calcular porcentaje de completitud
        proyecto["porcentaje_completado"] = round(
            (
                (proyecto["completadas"] / proyecto["total"] * 100)
                if proyecto["total"] > 0
                else 0
            ),
            1,
        )

        # Calcular días restantes
        if proyecto["idrequerimiento__idproyecto__fechafin"]:
            dias_restantes = (
                proyecto["idrequerimiento__idproyecto__fechafin"]
                - datetime.now().date()
            ).days
            proyecto["dias_restantes"] = max(0, dias_restantes)
        else:
            proyecto["dias_restantes"] = None

    return {
        "total_completadas": totales["total_completadas"],
        "total_en_progreso": totales["total_en_progreso"],
        "total_pendientes": totales["total_pendientes"],
        "proyectos": [
            {
                "id": p["idrequerimiento__idproyecto__idproyecto"],
                "nombre": p["idrequerimiento__idproyecto__nombreproyecto"],
                "completadas": p["completadas"],
                "en_progreso": p["en_progreso"],
                "pendientes": p["pendientes"],
                "total": p["total"],
                "porcentaje_completado": p["porcentaje_completado"],
                "dias_restantes": p["dias_restantes"],
            }
            for p in proyectos
        ],
    }


@login_required
def filtrar_historial(request):
    """Vista para filtrar el historial de tareas/actividades"""
    try:
        # Obtener parámetros de filtro
        tipo_filtro = request.GET.get("tipo_filtro", "todos")
        proyecto_id = request.GET.get("proyecto")
        page = request.GET.get("page", 1)

        # Determinar si usar Actividad (nuevo) o Historialtarea (legado)
        if Actividad.objects.filter(entidad_tipo="Tarea").exists():
            # Usar el nuevo modelo Actividad
            historial = (
                Actividad.objects.select_related("idusuario")
                .filter(entidad_tipo="Tarea")
                .order_by("-fechacreacion")
            )

            # Aplicar filtros
            if tipo_filtro == "estado":
                historial = historial.filter(
                    Q(accion__icontains="estado") | Q(nombre__icontains="estado")
                )
            elif tipo_filtro == "asignacion":
                historial = historial.filter(
                    Q(accion__icontains="asignación") | Q(nombre__icontains="asign")
                )
            elif tipo_filtro == "recursos":
                historial = historial.filter(
                    Q(accion__icontains="recurso") | Q(nombre__icontains="recurso")
                )

            if proyecto_id:
                # Buscar todas las tareas del proyecto
                tareas_proyecto = Tarea.objects.filter(
                    idrequerimiento__idproyecto_id=proyecto_id
                ).values_list("idtarea", flat=True)

                historial = historial.filter(entidad_id__in=tareas_proyecto)
        else:
            # Usar el modelo legacy Historialtarea con mejores optimizaciones
            historial = (
                Historialtarea.objects.select_related(
                    "idtarea",
                    "idtarea__idrequerimiento",
                    "idtarea__idrequerimiento__idproyecto",
                )
                .filter(idtarea__isnull=False)  # Filtrar entradas con tareas nulas
                .order_by("-fechacambio")
            )

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
        proyectos = Proyecto.objects.all().order_by("nombreproyecto")

        context = {
            "historial": historial_paginado,
            "proyectos": proyectos,
            "filtro_actual": tipo_filtro,
            "proyecto_actual": proyecto_id,
            "using_actividad": (
                "idusuario" in dir(historial.first()) if historial.exists() else False
            ),
        }

        return render(request, "components/historial_tareas.html", context)

    except Exception as e:
        messages.error(request, f"Error al filtrar historial: {str(e)}")
        return redirect("reportes:index")


@login_required
def exportar_csv(request):
    """Exportar datos a CSV con formato mejorado e información completa"""
    try:
        # Obtener los filtros individualmente del request.POST (similar a exportar_pdf)
        tipo_reporte = request.POST.get("tipo_reporte", "general")
        fecha_inicio_str = request.POST.get("fecha_inicio")
        fecha_fin_str = request.POST.get("fecha_fin")
        proyecto_id = request.POST.get("proyecto")

        # Registro de depuración
        print(f"CSV - POST recibido: {request.POST}")
        print(f"CSV - Tipo reporte: {tipo_reporte}")
        print(f"CSV - Fecha inicio: {fecha_inicio_str}")
        print(f"CSV - Fecha fin: {fecha_fin_str}")
        print(f"CSV - Proyecto: {proyecto_id}")

        # Aplicar filtros a la consulta
        tareas = Tarea.objects.select_related(
            "idrequerimiento__idproyecto", "tipo_tarea", "fase"
        ).prefetch_related("tarearecurso_set__idrecurso")

        # Aplicar filtro de proyecto (corrigiendo el manejo de "None")
        if proyecto_id and proyecto_id != "" and proyecto_id != "None":
            try:
                tareas = tareas.filter(idrequerimiento__idproyecto_id=proyecto_id)
            except Exception as e:
                print(f"Error al aplicar filtro de proyecto: {str(e)}")

        # Validar y aplicar filtros de fecha
        if fecha_inicio_str and fecha_fin_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

                # Asegurar que fecha_inicio <= fecha_fin
                if fecha_inicio > fecha_fin:
                    fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

                # Convertir a datetime aware para el filtrado
                fecha_inicio_dt = timezone.make_aware(
                    datetime.combine(fecha_inicio, datetime.min.time())
                )
                fecha_fin_dt = timezone.make_aware(
                    datetime.combine(fecha_fin, datetime.max.time())
                )

                tareas = tareas.filter(
                    fechacreacion__range=(fecha_inicio_dt, fecha_fin_dt)
                )
            except (ValueError, TypeError) as e:
                print(f"Error al parsear fechas: {str(e)}")
                # Si hay error en fechas, no aplicar filtro

        # Crear response HTTP con tipo CSV
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        filename = f"reporte_{tipo_reporte}_{timestamp}.csv"
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        # Crear writer CSV con configuración para español
        writer = csv.writer(
            response, delimiter=";", quotechar='"', quoting=csv.QUOTE_MINIMAL
        )

        # Encabezado con metadatos
        writer.writerow(["REPORTE DE TAREAS"])
        writer.writerow(
            [f"Fecha de generación: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}"]
        )
        writer.writerow(
            [
                f"Período: {fecha_inicio_str or 'No especificado'} a {fecha_fin_str or 'No especificado'}"
            ]
        )

        # Proyecto si está filtrado
        if proyecto_id and proyecto_id != "" and proyecto_id != "None":
            try:
                proyecto = Proyecto.objects.get(idproyecto=proyecto_id)
                writer.writerow([f"Proyecto: {proyecto.nombreproyecto}"])
            except Proyecto.DoesNotExist:
                writer.writerow(["Proyecto: No encontrado"])
        else:
            writer.writerow(["Proyecto: Todos"])

        writer.writerow([f"Tipo de reporte: {tipo_reporte.capitalize()}"])
        writer.writerow([])  # Línea en blanco

        # Escribir cabecera según tipo de reporte
        if tipo_reporte == "recursos":
            writer.writerow(
                [
                    "Recurso",
                    "Tipo",
                    "Asignado a",
                    "Horas Asignadas",
                    "Horas Utilizadas",
                    "Eficiencia (%)",
                    "Carga Trabajo",
                    "Disponibilidad",
                ]
            )

            # Obtener datos de recursos
            datos_recursos = calcular_estadisticas_recursos(tareas)

            # Escribir datos de recursos
            for recurso in datos_recursos["recursos"]:
                # Obtener las tareas asociadas a este recurso
                tareas_recurso = set()
                for tr in Tarearecurso.objects.filter(
                    idtarea__in=tareas, idrecurso__nombrerecurso=recurso["nombre"]
                ).select_related("idtarea"):
                    tareas_recurso.add(tr.idtarea.nombretarea)

                # Obtener datos adicionales del recurso
                try:
                    recurso_obj = Recurso.objects.get(nombrerecurso=recurso["nombre"])
                    carga_trabajo = recurso_obj.carga_trabajo or 0
                    disponibilidad = "Sí" if recurso_obj.disponibilidad else "No"
                except Recurso.DoesNotExist:
                    carga_trabajo = 0
                    disponibilidad = "Desconocida"

                writer.writerow(
                    [
                        recurso["nombre"],
                        recurso["tipo"],
                        ", ".join(tareas_recurso)[:100]
                        + ("..." if len(", ".join(tareas_recurso)) > 100 else ""),
                        recurso["horas_asignadas"],
                        recurso["horas_utilizadas"],
                        f"{recurso['eficiencia']}%",
                        f"{carga_trabajo*100:.1f}%",
                        disponibilidad,
                    ]
                )

            # Añadir totales
            writer.writerow([])
            writer.writerow(
                [
                    "TOTAL",
                    "",
                    "",
                    datos_recursos["total_horas_asignadas"],
                    datos_recursos["total_horas_utilizadas"],
                    (
                        f"{(datos_recursos['total_horas_utilizadas'] / datos_recursos['total_horas_asignadas'] * 100):.2f}%"
                        if datos_recursos["total_horas_asignadas"]
                        else "0%"
                    ),
                    "",
                    "",
                ]
            )

        elif tipo_reporte == "costos":
            # Escribir cabecera para reporte de costos
            writer.writerow(
                [
                    "Período",
                    "Costo Estimado",
                    "Costo Real",
                    "Variación (%)",
                    "Comentarios",
                ]
            )

            # Obtener datos de costos
            datos_costos = calcular_estadisticas_costos(tareas)

            # Escribir datos de períodos
            for periodo in datos_costos["periodos"]:
                # Generar comentarios basados en la variación
                comentarios = ""
                if periodo["variacion"] > 10:
                    comentarios = "Sobrecosto significativo"
                elif periodo["variacion"] < -10:
                    comentarios = "Ahorro significativo"
                elif abs(periodo["variacion"]) <= 5:
                    comentarios = "Dentro del presupuesto"

                writer.writerow(
                    [
                        periodo["fecha"],
                        f"${periodo['estimado']:.2f}",
                        f"${periodo['actual']:.2f}",
                        f"{periodo['variacion']:.2f}%",
                        comentarios,
                    ]
                )

            # Añadir resumen
            writer.writerow([])
            writer.writerow(
                [
                    "TOTAL",
                    f"${datos_costos['total_estimado']:.2f}",
                    f"${datos_costos['total_actual']:.2f}",
                    f"{datos_costos['variacion_total']:.2f}%",
                    (
                        "SOBRE PRESUPUESTO"
                        if datos_costos["variacion_total"] > 0
                        else "BAJO PRESUPUESTO"
                    ),
                ]
            )
            writer.writerow([])
            writer.writerow(["Indicadores de Rendimiento", "", "", "", ""])
            writer.writerow(
                [
                    "Presupuesto Utilizado",
                    f"{datos_costos['porcentaje_utilizado']:.2f}%",
                    "",
                    "",
                    "",
                ]
            )
            writer.writerow(
                [
                    "Índice de Eficiencia de Costos",
                    f"{datos_costos['indice_eficiencia']:.2f}",
                    "",
                    "",
                    "",
                ]
            )

        else:  # Reporte general o de tareas
            # Escribir cabecera de tareas detalladas
            writer.writerow(
                [
                    "ID",
                    "Tarea",
                    "Proyecto",
                    "Requerimiento",
                    "Estado",
                    "Duración Estimada (hrs)",
                    "Duración Real (hrs)",
                    "Costo Estimado",
                    "Costo Real",
                    "Fecha Inicio",
                    "Fecha Fin",
                    "Tipo",
                    "Fase",
                    "Prioridad",
                    "Recursos Asignados",
                    "% Completado",
                ]
            )

            # Escribir datos de tareas
            for tarea in tareas:
                # Calcular porcentaje completado
                if tarea.estado == "Completada":
                    porcentaje_completado = 100
                elif tarea.estado == "Pendiente":
                    porcentaje_completado = 0
                else:  # En progreso
                    if tarea.duracionestimada and tarea.duracionactual:
                        porcentaje_completado = min(
                            round(
                                (tarea.duracionactual / tarea.duracionestimada) * 100, 1
                            ),
                            99.9,
                        )
                    else:
                        porcentaje_completado = 50  # Valor por defecto

                # Obtener recursos asignados
                recursos_asignados = Tarearecurso.objects.filter(
                    idtarea=tarea
                ).select_related("idrecurso")

                recursos_str = ", ".join(
                    [
                        f"{tr.idrecurso.nombrerecurso} ({tr.cantidad or 1})"
                        for tr in recursos_asignados
                    ]
                )

                writer.writerow(
                    [
                        tarea.idtarea,
                        tarea.nombretarea,
                        tarea.idrequerimiento.idproyecto.nombreproyecto,
                        tarea.idrequerimiento.descripcion[:50]
                        + (
                            "..." if len(tarea.idrequerimiento.descripcion) > 50 else ""
                        ),
                        tarea.estado,
                        tarea.duracionestimada or 0,
                        tarea.duracionactual or 0,
                        f"${tarea.costoestimado or 0:.2f}",
                        f"${tarea.costoactual or 0:.2f}",
                        (
                            tarea.fechainicio.strftime("%d/%m/%Y")
                            if tarea.fechainicio
                            else "No definida"
                        ),
                        (
                            tarea.fechafin.strftime("%d/%m/%Y")
                            if tarea.fechafin
                            else "No definida"
                        ),
                        (
                            tarea.tipo_tarea.nombre
                            if tarea.tipo_tarea
                            else "No especificado"
                        ),
                        tarea.fase.nombre if tarea.fase else "No especificada",
                        tarea.prioridad or "N/A",
                        recursos_str,
                        f"{porcentaje_completado:.1f}%",
                    ]
                )

            # Añadir totales
            writer.writerow([])

            # Estadísticas generales
            total_tareas = tareas.count()
            completadas = tareas.filter(estado="Completada").count()
            en_progreso = tareas.filter(estado="En Progreso").count()
            pendientes = tareas.filter(estado="Pendiente").count()

            writer.writerow(["Resumen"])
            writer.writerow(["Total tareas", total_tareas])
            writer.writerow(
                [
                    "Completadas",
                    completadas,
                    f"{(completadas/total_tareas*100) if total_tareas else 0:.1f}%",
                ]
            )
            writer.writerow(
                [
                    "En progreso",
                    en_progreso,
                    f"{(en_progreso/total_tareas*100) if total_tareas else 0:.1f}%",
                ]
            )
            writer.writerow(
                [
                    "Pendientes",
                    pendientes,
                    f"{(pendientes/total_tareas*100) if total_tareas else 0:.1f}%",
                ]
            )

            # Agregar datos de costos totales
            total_estimado = (
                tareas.aggregate(Sum("costoestimado"))["costoestimado__sum"] or 0
            )
            total_actual = tareas.aggregate(Sum("costoactual"))["costoactual__sum"] or 0

            writer.writerow([])
            writer.writerow(["Costos totales"])
            writer.writerow(["Costo Estimado", f"${total_estimado:.2f}"])
            writer.writerow(["Costo Real", f"${total_actual:.2f}"])
            writer.writerow(
                [
                    "Variación",
                    f"${total_actual - total_estimado:.2f}",
                    f"{((total_actual-total_estimado)/total_estimado*100) if total_estimado else 0:.1f}%",
                ]
            )

        return response

    except Exception as e:
        return JsonResponse({"error": f"Error al exportar CSV: {str(e)}"}, status=500)


@login_required
def exportar_pdf(request):
    """Exportar datos a PDF con formato mejorado y diseño profesional"""
    try:
        # Obtener los filtros individualmente del request.POST
        tipo_reporte = request.POST.get("tipo_reporte", "general")
        fecha_inicio_str = request.POST.get("fecha_inicio")
        fecha_fin_str = request.POST.get("fecha_fin")
        proyecto_id = request.POST.get("proyecto")

        # Registro de depuración
        print(f"POST recibido: {request.POST}")
        print(f"Tipo reporte: {tipo_reporte}")
        print(f"Fecha inicio: {fecha_inicio_str}")
        print(f"Fecha fin: {fecha_fin_str}")
        print(f"Proyecto: {proyecto_id}")

        # Aplicar filtros a la consulta con optimización de consultas
        tareas = Tarea.objects.select_related(
            "idrequerimiento__idproyecto", "tipo_tarea", "fase"
        ).prefetch_related("tarearecurso_set__idrecurso")

        # Aplicar filtro de proyecto
        proyecto_obj = None
        if proyecto_id and proyecto_id != "":
            try:
                proyecto_obj = Proyecto.objects.get(idproyecto=proyecto_id)
                tareas = tareas.filter(idrequerimiento__idproyecto=proyecto_obj)
            except Proyecto.DoesNotExist:
                pass

        # Validar y aplicar filtros de fecha
        fecha_inicio = None
        fecha_fin = None

        if fecha_inicio_str and fecha_fin_str:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio_str, "%Y-%m-%d").date()
                fecha_fin = datetime.strptime(fecha_fin_str, "%Y-%m-%d").date()

                # Asegurar que fecha_inicio <= fecha_fin
                if fecha_inicio > fecha_fin:
                    fecha_inicio, fecha_fin = fecha_fin, fecha_inicio

                # Convertir a datetime aware para el filtrado
                fecha_inicio_dt = timezone.make_aware(
                    datetime.combine(fecha_inicio, datetime.min.time())
                )
                fecha_fin_dt = timezone.make_aware(
                    datetime.combine(fecha_fin, datetime.max.time())
                )

                tareas = tareas.filter(
                    fechacreacion__range=(fecha_inicio_dt, fecha_fin_dt)
                )
            except (ValueError, TypeError) as e:
                print(f"Error al parsear fechas: {str(e)}")
                # Si hay error en las fechas, usar fechas por defecto
                fecha_inicio = (timezone.now() - timedelta(days=30)).date()
                fecha_fin = timezone.now().date()

        # Definir decimal_field para su uso posterior
        decimal_field = models.DecimalField(max_digits=10, decimal_places=2)

        # Enriquecer tareas con datos calculados
        tareas_enriquecidas = []
        for tarea in tareas:
            # Calcular porcentaje de completitud
            if tarea.estado == "Completada":
                porcentaje_completado = 100
            elif tarea.estado == "Pendiente":
                porcentaje_completado = 0
            else:  # En progreso
                if tarea.duracionestimada and tarea.duracionactual:
                    porcentaje_completado = min(
                        round((tarea.duracionactual / tarea.duracionestimada) * 100, 1),
                        99.9,
                    )
                else:
                    porcentaje_completado = 50

            # Añadir campos calculados
            tarea.porcentaje_completado = porcentaje_completado

            tareas_enriquecidas.append(tarea)

        # Calcular estadísticas
        estadisticas = {
            "total_tareas": tareas.count(),
            "tareas_completadas": tareas.filter(estado="Completada").count(),
            "porcentaje_completadas": calculate_percentage(
                tareas.filter(estado="Completada").count(), tareas.count()
            ),
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

        # Datos específicos según tipo de reporte
        datos_especificos = {}
        if tipo_reporte == "recursos":
            datos_especificos["datos_recursos"] = calcular_estadisticas_recursos(tareas)
        elif tipo_reporte == "costos":
            datos_especificos["datos_costos"] = calcular_estadisticas_costos(tareas)
        elif tipo_reporte == "tareas":
            # Mejorada la forma en que se calculan los datos para el reporte de tareas
            tareas_por_estado = []
            estados = ["Completada", "En Progreso", "Pendiente"]

            for estado in estados:
                count = tareas.filter(estado=estado).count()
                tareas_por_estado.append({"estado": estado, "count": count})

            datos_especificos["datos_tareas"] = {
                "tareas_por_tipo": tareas.values("tipo_tarea__nombre")
                .annotate(count=Count("idtarea"))
                .order_by("-count"),
                "tareas_por_fase": tareas.values("fase__nombre")
                .annotate(count=Count("idtarea"))
                .order_by("fase__orden"),
                "tareas_por_estado": tareas_por_estado,
                "tareas_list": tareas_enriquecidas,  # Lista completa para el reporte de tareas
            }
        else:  # general
            # Para el reporte general, incluir todos los tipos de datos
            datos_especificos["datos_generales"] = calcular_estadisticas_tareas(tareas)
            datos_especificos["datos_recursos"] = calcular_estadisticas_recursos(tareas)
            datos_especificos["datos_costos"] = calcular_estadisticas_costos(tareas)

        # Seleccionar plantilla según tipo de reporte
        template_map = {
            "general": "reportes/pdf_template.html",
            "tareas": "reportes/pdf_template_tareas.html",
            "recursos": "reportes/pdf_template_recursos.html",
            "costos": "reportes/pdf_template_costos.html",
        }

        template_name = template_map.get(tipo_reporte, "reportes/pdf_template.html")
        print(f"Usando plantilla: {template_name}")  # Depuración

        # Preparar contexto completo para el PDF
        context_pdf = {
            "tareas": tareas_enriquecidas,
            "estadisticas": estadisticas,
            "fecha_generacion": timezone.now(),
            "filtros": {
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "proyecto": (
                    proyecto_obj
                    if "proyecto_obj" in locals() and proyecto_obj
                    else None
                ),
                "tipo_reporte": tipo_reporte,
            },
            "request": request,
            **datos_especificos,
        }

        # Renderizar a HTML
        html = render_to_string(template_name, context_pdf)

        # Crear PDF con opciones mejoradas
        pdf = HTML(string=html, base_url=request.build_absolute_uri()).write_pdf(
            stylesheets=[],
            presentational_hints=True,
        )

        # Crear response con nombre de archivo dinámico
        timestamp = timezone.now().strftime("%Y%m%d_%H%M%S")
        proyecto_nombre = (
            proyecto_obj.nombreproyecto.replace(" ", "_")
            if "proyecto_obj" in locals() and proyecto_obj
            else "todos"
        )
        filename = f"reporte_{tipo_reporte}_{proyecto_nombre}_{timestamp}.pdf"

        response = HttpResponse(pdf, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'

        return response

    except Exception as e:
        print(f"Error al exportar PDF: {str(e)}")  # Para debugging
        return JsonResponse({"error": f"Error al exportar PDF: {str(e)}"}, status=500)
