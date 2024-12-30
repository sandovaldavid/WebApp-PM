# notificaciones/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from dashboard.models import (
    Notificacion,
    Alerta,
    Tarea,
    Usuario,
    Historialalerta,
    Historialnotificacion,
)

# @login_required
def index(request):
    # Obtener notificaciones y alertas activas
    notificaciones = (
        Notificacion.objects.filter(leido=False)
        .select_related("idusuario")
        .order_by("-fechacreacion")
    )

    alertas = (
        Alerta.objects.filter(activa=True)
        .select_related("idtarea")
        .order_by("-fechacreacion")
    )

    context = {
        "notificaciones": notificaciones,
        "alertas": alertas,
        "fecha_actual": timezone.now(),
    }

    return render(request, "notificaciones/index.html", context)


# @login_required
def crear_notificacion(request):
    if request.method == "POST":
        usuario_id = request.POST.get("usuario")
        mensaje = request.POST.get("mensaje")

        # Crear nueva notificación
        notificacion = Notificacion.objects.create(
            idusuario_id=usuario_id,
            mensaje=mensaje,
            leido=False,
            fechacreacion=timezone.now(),
        )

        messages.success(request, "Notificación creada exitosamente")
        return redirect("notificaciones:index")

    usuarios = Usuario.objects.all()
    return render(
        request, "notificaciones/crear_notificacion.html", {"usuarios": usuarios}
    )


# @login_required
def crear_alerta(request):
    if request.method == "POST":
        tarea_id = request.POST.get("tarea")
        tipo_alerta = request.POST.get("tipo_alerta")
        mensaje = request.POST.get("mensaje")

        # Crear nueva alerta
        alerta = Alerta.objects.create(
            idtarea_id=tarea_id,
            tipoalerta=tipo_alerta,
            mensaje=mensaje,
            activa=True,
            fechacreacion=timezone.now(),
        )

        messages.success(request, "Alerta creada exitosamente")
        return redirect("notificaciones:index")

    tareas = Tarea.objects.all()
    tipos_alerta = ["retraso", "presupuesto", "riesgo", "bloqueo"]

    return render(
        request,
        "notificaciones/crear_alerta.html",
        {"tareas": tareas, "tipos_alerta": tipos_alerta},
    )

#@login_required
def dashboard(request):
    # Obtener fecha hace 30 días para filtrar
    fecha_30_dias = timezone.now() - timedelta(days=30)

    # Estadísticas generales
    estadisticas = {
        "total_notificaciones": Notificacion.objects.count(),
        "no_leidas": Notificacion.objects.filter(leido=False).count(),
        "alertas_activas": Alerta.objects.filter(activa=True).count(),
    }

    # Notificaciones recientes sin leer
    notificaciones_recientes = (
        Notificacion.objects.filter(leido=False)
        .select_related("idusuario")
        .order_by("-fechacreacion")[:5]
    )

    # Alertas activas
    alertas_activas = (
        Alerta.objects.filter(activa=True)
        .select_related("idtarea")
        .order_by("-fechacreacion")[:5]
    )

    # Historial de actividad
    historial_alertas = (
        Historialalerta.objects.select_related("idalerta")
        .filter(fecharesolucion__gte=fecha_30_dias)
        .order_by("-fecharesolucion")[:10]
    )

    historial_notificaciones = (
        Historialnotificacion.objects.select_related("idnotificacion")
        .filter(fechalectura__gte=fecha_30_dias)
        .order_by("-fechalectura")[:10]
    )

    # Análisis de tipos de alertas
    tipos_alertas = (
        Alerta.objects.filter(fechacreacion__gte=fecha_30_dias)
        .values("tipoalerta")
        .annotate(total=Count("idalerta"))
        .order_by("-total")
    )

    context = {
        "estadisticas": estadisticas,
        "notificaciones_recientes": notificaciones_recientes,
        "alertas_activas": alertas_activas,
        "historial_alertas": historial_alertas,
        "historial_notificaciones": historial_notificaciones,
        "tipos_alertas": tipos_alertas,
        "fecha_actual": timezone.now(),
    }

    return render(request, "notificaciones/dashboard.html", context)
