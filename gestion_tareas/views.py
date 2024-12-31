from django.shortcuts import render

# Create your views here.


def index(request):
    return render(request, "gestion_tareas/index.html")


def tareas_programadas(request):
    return render(request, "gestion_tareas_programadas/index.html")


from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from dashboard.models import Tarea, Historialtarea, Tarearecurso, Recurso, Alerta


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
