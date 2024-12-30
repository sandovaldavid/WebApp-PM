# notificaciones/views.py
from django.http import JsonResponse
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
    fecha_30_dias = timezone.now() - timedelta(days=30)

    # Estadísticas generales
    estadisticas = {
        "total_notificaciones": Notificacion.objects.filter(
            idusuario=request.user
        ).count(),
        "no_leidas": Notificacion.objects.filter(
            idusuario=request.user, leido=False
        ).count(),
        "alertas_activas": Alerta.objects.filter(
            idtarea__idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user,
            activa=True,
        ).count(),
    }

    # Notificaciones recientes sin leer
    notificaciones = (
        Notificacion.objects.filter(idusuario=request.user, leido=False)
        .select_related("idusuario")
        .order_by("-fechacreacion")[:5]
    )

    # Alertas activas
    alertas = (
        Alerta.objects.filter(
            idtarea__idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user,
            activa=True,
        )
        .select_related("idtarea")
        .order_by("-fechacreacion")[:5]
    )

    # Análisis de tipos de alertas
    tipos_alertas = (
        Alerta.objects.filter(
            fechacreacion__gte=fecha_30_dias,
            idtarea__idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user,
        )
        .values("tipoalerta")
        .annotate(total=Count("idalerta"))
        .order_by("-total")
    )

    context = {
        "estadisticas": estadisticas,
        "notificaciones": notificaciones,
        "alertas": alertas,
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


# @login_required
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


# @login_required
def lista_notificaciones(request):
    notificaciones = Notificacion.objects.filter(idusuario=request.user).order_by(
        "-fechacreacion"
    )

    return render(
        request,
        "notificaciones/lista_notificaciones.html",
        {"notificaciones": notificaciones},
    )


# @login_required
def crear_notificacion(request):
    if request.method == "POST":
        mensaje = request.POST.get("mensaje")
        usuario_id = request.POST.get("usuario")
        prioridad = request.POST.get("prioridad", "media")
        categoria = request.POST.get("categoria")

        notificacion = Notificacion.objects.create(
            mensaje=mensaje,
            idusuario_id=usuario_id,
            leido=False,
            fechacreacion=timezone.now(),
            prioridad=prioridad,
            categoria=categoria,
        )

        messages.success(request, "Notificación creada exitosamente")
        return redirect("notificaciones:lista_notificaciones")

    usuarios = Usuario.objects.all()
    return render(
        request, "notificaciones/crear_notificacion.html", {"usuarios": usuarios}
    )


# @login_required
def editar_notificacion(request, id):
    notificacion = get_object_or_404(Notificacion, idnotificacion=id)

    if request.method == "POST":
        notificacion.mensaje = request.POST.get("mensaje")
        notificacion.prioridad = request.POST.get("prioridad")
        notificacion.categoria = request.POST.get("categoria")
        notificacion.save()

        messages.success(request, "Notificación actualizada exitosamente")
        return redirect("notificaciones:lista_notificaciones")

    return render(
        request,
        "notificaciones/editar_notificacion.html",
        {"notificacion": notificacion},
    )


# @login_required
def eliminar_notificacion(request, id):
    if request.method == "POST":
        notificacion = get_object_or_404(Notificacion, idnotificacion=id)
        notificacion.delete()
        messages.success(request, "Notificación eliminada exitosamente")
    return redirect("notificaciones:lista_notificaciones")


# @login_required
def marcar_leida(request, id):
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


# @login_required
def detalle_notificacion(request, id):
    notificacion = get_object_or_404(Notificacion, idnotificacion=id)
    historial = Historialnotificacion.objects.filter(
        idnotificacion=notificacion
    ).order_by("-fechalectura")

    return render(
        request,
        "notificaciones/detalle_notificacion.html",
        {"notificacion": notificacion, "historial": historial},
    )


# @login_required
def resolver_alerta(request, id):
    """
    Vista para resolver una alerta y registrar su resolución en el historial
    """
    if request.method == "POST":
        # Obtener la alerta o devolver 404 si no existe
        alerta = get_object_or_404(Alerta, idalerta=id)

        try:
            # Marcar la alerta como inactiva
            alerta.activa = False
            alerta.save()

            # Crear registro en el historial
            Historialalerta.objects.create(
                idalerta=alerta, fecharesolucion=timezone.now()
            )

            messages.success(request, "Alerta resuelta exitosamente")

            # Retornar respuesta exitosa
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "success"})
            return redirect("notificaciones:index")

        except Exception as e:
            messages.error(request, f"Error al resolver la alerta: {str(e)}")
            if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                return JsonResponse({"status": "error", "message": str(e)}, status=500)
            return redirect("notificaciones:index")

    # Si el método no es POST, redirigir al index
    return redirect("notificaciones:index")
