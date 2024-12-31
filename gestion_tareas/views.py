from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.utils import timezone
from dashboard.models import (
    Tarea,
    Historialtarea,
    Tarearecurso,
    Recurso,
    Alerta,
    Requerimiento,
)

# Create your views here.


@login_required
def index(request):
    """Vista principal de gestión de tareas"""
    # Obtener todas las tareas
    tareas = Tarea.objects.all().select_related("idrequerimiento__idproyecto")

    # Estadísticas generales
    estadisticas = {
        "total": tareas.count(),
        "pendientes": tareas.filter(estado="Pendiente").count(),
        "en_progreso": tareas.filter(estado="En Progreso").count(),
        "completadas": tareas.filter(estado="Completada").count(),
    }

    # Datos para el gráfico de estado
    datos_estado = {
        "labels": ["Pendientes", "En Progreso", "Completadas"],
        "data": [
            estadisticas["pendientes"],
            estadisticas["en_progreso"],
            estadisticas["completadas"],
        ],
    }

    # Distribución por prioridad
    prioridades = list(
        tareas.values("prioridad").annotate(total=Count("idtarea")).order_by("-total")
    )

    # Preparar datos para el gráfico de prioridades
    datos_prioridad = {
        "labels": [p["prioridad"] for p in prioridades],
        "data": [p["total"] for p in prioridades],
    }

    context = {
        "tareas": tareas,
        "estadisticas": estadisticas,
        "datos_estado": datos_estado,
        "datos_prioridad": datos_prioridad,
    }

    return render(request, "gestion_tareas/index.html", context)


@login_required
def crear_tarea(request):
    """Vista para crear una nueva tarea"""
    if request.method == "POST":
        # Obtener datos del formulario
        requerimiento_id = request.POST.get("requerimiento")
        nombre = request.POST.get("nombre")
        estado = request.POST.get("estado")
        prioridad = request.POST.get("prioridad")
        duracion_estimada = request.POST.get("duracion_estimada")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")

        # Crear la tarea
        tarea = Tarea.objects.create(
            idrequerimiento_id=requerimiento_id,
            nombretarea=nombre,
            estado=estado,
            prioridad=prioridad,
            duracionestimada=duracion_estimada,
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            fechacreacion=timezone.now(),
            fechamodificacion=timezone.now(),
        )

        return redirect("gestion_tareas:index")

    # Obtener requerimientos para el formulario
    requerimientos = Requerimiento.objects.all()
    return render(
        request, "gestion_tareas/crear_tarea.html", {"requerimientos": requerimientos}
    )


def tareas_programadas(request):
    return render(request, "gestion_tareas_programadas/index.html")


@login_required
def detalle_tarea(request, id):
    # Obtener la tarea y datos relacionados
    tarea = get_object_or_404(Tarea, idtarea=id)
    historial = Historialtarea.objects.filter(idtarea=tarea).order_by("-fechacambio")

    # Obtener recursos asignados
    recursos_asignados = Tarearecurso.objects.filter(idtarea=tarea).select_related(
        "idrecurso"
    )

    # Obtener alertas activas relacionadas
    alertas = Alerta.objects.filter(idtarea=tarea, activa=True).order_by(
        "-fechacreacion"
    )

    # Calcular progreso y métricas
    progreso = 0
    if tarea.duracionactual and tarea.duracionestimada:
        progreso = (tarea.duracionactual / tarea.duracionestimada) * 100

    # Calcular desviación de costos
    desviacion_costos = 0
    if tarea.costoactual and tarea.costoestimado:
        desviacion_costos = (
            (tarea.costoactual - tarea.costoestimado) / tarea.costoestimado
        ) * 100

    context = {
        "tarea": tarea,
        "historial": historial,
        "recursos_asignados": recursos_asignados,
        "alertas": alertas,
        "progreso": progreso,
        "desviacion_costos": desviacion_costos,
    }

    return render(request, "gestion_tareas/detalle_tarea.html", context)


@login_required
def crear_tarea(request):
    """Vista para crear una nueva tarea"""
    if request.method == "POST":
        # Obtener datos del formulario
        requerimiento_id = request.POST.get("requerimiento")
        nombre = request.POST.get("nombre")
        estado = request.POST.get("estado")
        prioridad = request.POST.get("prioridad")
        duracion_estimada = request.POST.get("duracion_estimada")
        fecha_inicio = request.POST.get("fecha_inicio")
        fecha_fin = request.POST.get("fecha_fin")

        # Crear la tarea
        tarea = Tarea.objects.create(
            idrequerimiento_id=requerimiento_id,
            nombretarea=nombre,
            estado=estado,
            prioridad=prioridad,
            duracionestimada=duracion_estimada,
            fechainicio=fecha_inicio,
            fechafin=fecha_fin,
            fechacreacion=timezone.now(),
            fechamodificacion=timezone.now(),
        )

        return redirect("gestion_tareas:index")

    # Obtener requerimientos para el formulario
    requerimientos = Requerimiento.objects.all()
    return render(
        request, "gestion_tareas/crear_tarea.html", {"requerimientos": requerimientos}
    )
