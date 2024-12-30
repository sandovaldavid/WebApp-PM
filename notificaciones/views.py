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

    context = {
        "tareas": Tarea.objects.all().order_by("-fechacreacion"),
        "tipos_alerta": ["retraso", "presupuesto", "riesgo", "bloqueo"],
    }

    return render(request, "alertas/crear_alerta.html", context)


# @login_required
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


# @login_required
def detalle_alerta(request, id):
    alerta = get_object_or_404(Alerta, idalerta=id)
    historial = Historialalerta.objects.filter(idalerta=alerta).order_by(
        "-fecharesolucion"
    )

    if request.method == "POST" and "resolver_alerta" in request.POST:
        alerta.activa = False
        alerta.save()

        # Crear registro en historial
        Historialalerta.objects.create(
            idalerta=alerta, fecharesolucion=timezone.now(), estado="Resuelta"
        )

        messages.success(request, "Alerta marcada como resuelta")
        return redirect("notificaciones:lista_alertas")

    context = {
        "alerta": alerta,
        "historial": historial,
        "tarea": alerta.idtarea,
    }

    return render(request, "alertas/detalle_alerta.html", context)


# @login_required
def marcar_notificacion(request, id):
    if request.method == "POST":
        notificacion = get_object_or_404(Notificacion, idnotificacion=id)
        notificacion.leido = True
        notificacion.save()

        # Crear registro en historial
        Historialnotificacion.objects.create(
            idnotificacion=notificacion, fechalectura=timezone.now()
        )

        messages.success(request, "Notificación marcada como leída")
        return redirect("notificaciones:lista_notificaciones")

    return redirect("notificaciones:lista_notificaciones")


@login_required
def detalle_notificacion(request, id):
    # Obtener la notificación o devolver 404 si no existe
    notificacion = get_object_or_404(Notificacion, idnotificacion=id)

    # Obtener el historial de la notificación
    historial = Historialnotificacion.objects.filter(
        idnotificacion=notificacion
    ).order_by("-fechalectura")

    # Si la notificación no está leída, marcarla como leída
    if not notificacion.leido:
        notificacion.leido = True
        notificacion.save()

        # Crear registro en historial
        Historialnotificacion.objects.create(
            idnotificacion=notificacion, fechalectura=timezone.now()
        )

    context = {
        "notificacion": notificacion,
        "historial": historial,
        "usuario": notificacion.idusuario,
        "fecha_actual": timezone.now(),
    }

    return render(request, "notificaciones/detalle_notificacion.html", context)
