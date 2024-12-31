# notificaciones/views.py
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.core.paginator import Paginator
from dashboard.models import (
    Notificacion,
    Alerta,
    Tarea,
    Usuario,
    Historialalerta,
    Historialnotificacion,
    Proyecto,
)


# @login_required
def crear_notificacion(request):
    if request.method == "POST":
        usuario_id = request.POST.get("usuario")
        mensaje = request.POST.get("mensaje")
        prioridad = request.POST.get("prioridad", "media")
        categoria = request.POST.get("categoria")
        fecha_recordatorio = request.POST.get("fecha_recordatorio")

        notificacion = Notificacion.objects.create(
            idusuario_id=usuario_id,
            mensaje=mensaje,
            leido=False,
            fechacreacion=timezone.now(),
            prioridad=prioridad,
            categoria=categoria,
            fecha_recordatorio=fecha_recordatorio if fecha_recordatorio else None,
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


@login_required
def dashboard(request):
    """
    Vista del dashboard que muestra notificaciones filtradas por usuario
    o todas si es admin
    """
    # Determinar si el usuario es admin
    is_admin = request.user.is_staff or request.user.rol == "Admin"

    # Estadísticas generales
    if is_admin:
        # Para administradores: mostrar todas las estadísticas
        estadisticas = {
            "total_notificaciones": Notificacion.objects.all().count(),
            "no_leidas": Notificacion.objects.filter(leido=False).count(),
            "alertas_activas": Alerta.objects.filter(activa=True).count(),
        }
    else:
        # Para usuarios normales: mostrar solo sus estadísticas
        estadisticas = {
            "total_notificaciones": Notificacion.objects.filter(
                idusuario=request.user
            ).count(),
            "no_leidas": Notificacion.objects.filter(
                idusuario=request.user, leido=False
            ).count(),
            "alertas_activas": Alerta.objects.filter(
                idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                    idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
                ),
                activa=True,
            ).count(),
        }

    # Notificaciones recientes sin leer
    if is_admin:
        notificaciones = Notificacion.objects.all()
    else:
        notificaciones = (
            Notificacion.objects.filter(idusuario=request.user, leido=False)
            .select_related("idusuario")
            .order_by("-fechacreacion")[:5]
        )

    # Alertas activas
    if is_admin:
        alertas = (
            Alerta.objects.filter(activa=True)
            .select_related("idtarea")
            .order_by("-fechacreacion")[:5]
        )
    else:
        alertas = (
            Alerta.objects.filter(
                idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                    idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
                ),
                activa=True,
            )
            .select_related("idtarea")
            .order_by("-fechacreacion")[:5]
        )

    # Análisis de tipos de alertas
    if is_admin:
        tipos_alertas = (
            Alerta.objects.values("tipoalerta")
            .annotate(total=Count("idalerta"))
            .order_by("-total")
        )
    else:
        tipos_alertas = (
            Alerta.objects.filter(
                idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                    idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
                )
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
        "is_admin": is_admin,
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
        usuario_id = request.POST.get("usuario")
        mensaje = request.POST.get("mensaje")
        prioridad = request.POST.get("prioridad", "media")
        categoria = request.POST.get("categoria")
        fecha_recordatorio = request.POST.get("fecha_recordatorio")

        try:
            notificacion = Notificacion.objects.create(
                idusuario_id=usuario_id,
                mensaje=mensaje,
                leido=False,
                fechacreacion=timezone.now(),
                prioridad=prioridad,
                categoria=categoria,
                fecha_recordatorio=fecha_recordatorio if fecha_recordatorio else None,
                archivada=False,
            )

            messages.success(request, "Notificación creada exitosamente")
            return redirect(
                "notificaciones:ver_notificacion", id=notificacion.idnotificacion
            )

        except Exception as e:
            messages.error(request, f"Error al crear la notificación: {str(e)}")
            return redirect("notificaciones:crear_notificacion")

    usuarios = Usuario.objects.all().order_by("nombreusuario")
    return render(
        request, "notificaciones/crear_notificacion.html", {"usuarios": usuarios}
    )


# @login_required
def ver_notificacion(request, id):
    """
    Vista para mostrar los detalles de una notificación recién creada
    """
    notificacion = get_object_or_404(Notificacion, idnotificacion=id)
    return render(
        request, "notificaciones/ver_notificacion.html", {"notificacion": notificacion}
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
    return redirect("notificaciones:index")


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


# @login_required
def marcar_todas_leidas(request):
    """Vista para marcar todas las notificaciones como leídas"""
    if request.method == "POST":
        try:
            # Obtener notificaciones no leídas del usuario
            notificaciones = Notificacion.objects.filter(
                idusuario=request.user, leido=False
            )

            # Marcar como leídas
            for notif in notificaciones:
                notif.leido = True
                notif.save()

                # Registrar en historial
                Historialnotificacion.objects.create(
                    idnotificacion=notif, fechalectura=timezone.now()
                )

            messages.success(
                request, f"{notificaciones.count()} notificaciones marcadas como leídas"
            )
            return redirect("notificaciones:listar_notificaciones")

        except Exception as e:
            messages.error(request, f"Error al marcar notificaciones: {str(e)}")

    return redirect("notificaciones:listar_notificaciones")


# @login_required
def filtrar_notificaciones(request):
    """Vista para filtrar notificaciones"""
    prioridad = request.GET.get("prioridad", "todas")

    is_admin = request.user.is_staff or request.user.rol == "Admin"

    if is_admin:
        notificaciones = Notificacion.objects.all().order_by("-fechacreacion")
    else:
        # Query base
        notificaciones = Notificacion.objects.filter(
            idusuario=request.user, archivada=False
        ).order_by("-fechacreacion")

    # Aplicar filtro de prioridad
    if prioridad != "todas":
        notificaciones = notificaciones.filter(prioridad=prioridad)

    context = {"notificaciones": notificaciones, "prioridad_actual": prioridad}

    # Solo renderizar la lista de notificaciones para peticiones HTMX
    return render(request, "components/lista_notificaciones.html", context)


@login_required  # Asegura que el usuario esté autenticado
def archivar_notificacion(request, id):
    """
    Vista para archivar una notificación
    """
    if request.method == "POST":
        try:
            # Primero intentamos obtener la notificación solo por ID
            notificacion = get_object_or_404(Notificacion, idnotificacion=id)
            is_admin = request.user.is_staff or request.user.rol == "Admin"
            # Verificar si el usuario tiene permiso para archivar esta notificación
            if (
                notificacion.idusuario == request.user
                or request.user.is_staff
                or is_admin
            ):
                notificacion.archivada = True
                notificacion.save()
                messages.success(request, "Notificación archivada correctamente")
            else:
                messages.error(
                    request, "No tienes permiso para archivar esta notificación"
                )

        except Notificacion.DoesNotExist:
            messages.error(request, "La notificación no existe")
        except Exception as e:
            messages.error(request, f"Error al archivar la notificación: {str(e)}")

    return redirect("notificaciones:index")


# @login_required
def notificaciones_archivadas(request):
    """
    Vista para mostrar notificaciones archivadas
    """
    notificaciones = Notificacion.objects.filter(
        idusuario=request.user, archivada=True
    ).order_by("-fechacreacion")

    paginator = Paginator(notificaciones, 10)
    page = request.GET.get("page")

    try:
        notificaciones = paginator.page(page)
    except:
        notificaciones = paginator.page(1)

    return render(
        request, "notificaciones/archivadas.html", {"notificaciones": notificaciones}
    )


# @login_required
def estadisticas_notificaciones(request):
    """
    Vista para mostrar estadísticas de notificaciones
    """
    total_notificaciones = Notificacion.objects.filter(idusuario=request.user).count()
    no_leidas = Notificacion.objects.filter(idusuario=request.user, leido=False).count()
    archivadas = Notificacion.objects.filter(
        idusuario=request.user, archivada=True
    ).count()

    # Estadísticas por prioridad
    por_prioridad = (
        Notificacion.objects.filter(idusuario=request.user)
        .values("prioridad")
        .annotate(total=Count("idnotificacion"))
    )

    # Estadísticas por categoría
    por_categoria = (
        Notificacion.objects.filter(idusuario=request.user)
        .values("categoria")
        .annotate(total=Count("idnotificacion"))
    )

    return render(
        request,
        "notificaciones/estadisticas.html",
        {
            "total": total_notificaciones,
            "no_leidas": no_leidas,
            "archivadas": archivadas,
            "por_prioridad": por_prioridad,
            "por_categoria": por_categoria,
        },
    )


@login_required
def eliminar_notificacion(request, id):
    """
    Vista para eliminar una notificación específica.
    Solo permite eliminar si es el propietario o admin.
    """
    if request.method == "POST":
        try:
            # Obtener la notificación o devolver 404
            notificacion = get_object_or_404(Notificacion, idnotificacion=id)

            # Verificar que el usuario sea el propietario o admin
            if notificacion.idusuario == request.user or request.user.is_staff:
                # Eliminar la notificación y su historial
                Historialnotificacion.objects.filter(
                    idnotificacion=notificacion
                ).delete()
                notificacion.delete()

                messages.success(request, "Notificación eliminada correctamente")
            else:
                messages.error(
                    request, "No tienes permiso para eliminar esta notificación"
                )

        except Notificacion.DoesNotExist:
            messages.error(request, "La notificación no existe")
        except Exception as e:
            messages.error(request, f"Error al eliminar la notificación: {str(e)}")

        # Si es una petición AJAX/HTMX
        if request.headers.get("HX-Request"):
            return render(
                request,
                "components/lista_notificaciones.html",
                {
                    "notificaciones": Notificacion.objects.filter(
                        idusuario=request.user, archivada=False
                    ).order_by("-fechacreacion")
                },
            )

        # Redirigir según el contexto
        next_url = request.POST.get("next") or request.GET.get("next")
        if next_url:
            return redirect(next_url)
        return redirect("notificaciones:index")

    # Si no es POST, redirigir al index
    return redirect("notificaciones:index")
