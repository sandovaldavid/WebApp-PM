# notificaciones/views.py
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, FloatField, Case, When, F
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.db.models.functions import TruncDate

from .services import MonitoreoService

from dashboard.models import (
    Notificacion,
    Alerta,
    Tarea,
    Usuario,
    Historialalerta,
    Historialnotificacion,
    Proyecto,
)


@login_required
def index(request):
    """
    Vista del dashboard que muestra notificaciones filtradas por usuario
    o todas si es admin
    """
    # Determinar si el usuario es admin
    is_admin = request.user.is_staff or request.user.rol == "Administrador"

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
        notificaciones = Notificacion.objects.all().order_by("-fechacreacion")[:8]
    else:
        notificaciones = (
            Notificacion.objects.filter(idusuario=request.user, leido=False)
            .select_related("idusuario")
            .order_by("-fechacreacion")[:5]
        )

    # Alertas activas
    if is_admin:
        alertas = (
            Alerta.objects.all()
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


@login_required
def crear_notificacion(request):
    if request.method == "POST":
        usuario_id = request.POST.get("usuario")
        mensaje = request.POST.get("mensaje")
        prioridad = request.POST.get("prioridad", "media")
        categoria = request.POST.get("categoria")
        fecha_recordatorio = request.POST.get("fecha_recordatorio")
        fecha_actual = timezone.now()

        # Validar que se haya seleccionado un usuario
        if not usuario_id:
            messages.error(request, "Debe seleccionar un usuario destinatario")
            usuarios = Usuario.objects.all().order_by("nombreusuario")
            # Pasar los datos del formulario para mantenerlos
            context = {
                "usuarios": usuarios,
                "mensaje": mensaje,
                "prioridad": prioridad,
                "categoria": categoria,
                "fecha_recordatorio": fecha_recordatorio,
            }
            return render(request, "notificaciones/crear_notificacion.html", context)

        try:
            fecha_recordatorio_obj = None  # Por defecto es None

            # Validar que la fecha de recordatorio sea posterior a la fecha actual (solo si se proporcionó)
            if fecha_recordatorio and fecha_recordatorio.strip():
                # Convertir la fecha de recordatorio a datetime
                fecha_recordatorio_dt = timezone.datetime.strptime(
                    fecha_recordatorio, "%Y-%m-%dT%H:%M"
                )
                fecha_recordatorio_obj = timezone.make_aware(fecha_recordatorio_dt)

                # Verificar que la fecha sea futura
                if fecha_recordatorio_obj <= fecha_actual:
                    messages.error(
                        request,
                        "La fecha de recordatorio debe ser posterior a la fecha actual",
                    )
                    usuarios = Usuario.objects.all().order_by("nombreusuario")
                    # Pasar los datos del formulario para mantenerlos
                    context = {
                        "usuarios": usuarios,
                        "selected_usuario_id": usuario_id,
                        "mensaje": mensaje,
                        "prioridad": prioridad,
                        "categoria": categoria,
                        "fecha_recordatorio": fecha_recordatorio,
                    }
                    return render(
                        request, "notificaciones/crear_notificacion.html", context
                    )

            notificacion = Notificacion.objects.create(
                idusuario_id=usuario_id,
                mensaje=mensaje,
                leido=False,
                fechacreacion=fecha_actual,
                prioridad=prioridad,
                categoria=categoria,
                fecha_recordatorio=fecha_recordatorio_obj,  # Usar el objeto datetime o None
                archivada=False,
            )

            messages.success(request, "Notificación creada exitosamente")
            return redirect(
                "notificaciones:detalle_notificacion", id=notificacion.idnotificacion
            )

        except ValueError:
            messages.error(
                request, "Formato de fecha inválido. Utilice el formato correcto."
            )
            usuarios = Usuario.objects.all().order_by("nombreusuario")
            return render(
                request,
                "notificaciones/crear_notificacion.html",
                {"usuarios": usuarios},
            )
        except Exception as e:
            messages.error(request, f"Error al crear la notificación: {str(e)}")
            return redirect("notificaciones:crear_notificacion")

    usuarios = Usuario.objects.all().order_by("nombreusuario")
    return render(
        request, "notificaciones/crear_notificacion.html", {"usuarios": usuarios}
    )


@login_required
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
def detalle_alerta(request, id):
    """
    Vista para mostrar los detalles de una alerta específica
    """
    # Obtener la alerta o devolver 404
    alerta = get_object_or_404(Alerta, idalerta=id)
    is_admin = request.user.is_staff or request.user.rol == "Administrador"

    # La tarea está relacionada con un requerimiento que pertenece a un proyecto
    tarea = alerta.idtarea

    # Verificar permisos - El usuario debe ser admin o estar relacionado con el proyecto
    tiene_permiso = (
        is_admin
        or request.user.is_staff
        or Proyecto.objects.filter(
            idequipo__miembro__idrecurso__recursohumano__idusuario=request.user,
            requerimiento__tarea=tarea,
        ).exists()
    )

    if not tiene_permiso:
        messages.error(request, "No tienes permiso para ver esta alerta")
        return redirect("notificaciones:index")

    # Obtener historial ordenado por fecha
    historial = Historialalerta.objects.filter(idalerta=alerta).order_by(
        "-fecharesolucion"
    )

    context = {"alerta": alerta, "historial": historial, "tarea": tarea}

    return render(request, "alertas/detalle_alerta.html", context)


@login_required
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


@login_required
def lista_notificaciones(request):
    """Vista para listar todas las notificaciones con estadísticas y filtros"""
    # Determinar si el usuario es admin
    is_admin = request.user.is_staff or request.user.rol == "Administrador"

    # Obtener el filtro de prioridad
    prioridad = request.GET.get("prioridad", "todas")

    # Query base según permisos
    if is_admin:
        base_query = Notificacion.objects.all()
    else:
        base_query = Notificacion.objects.filter(idusuario=request.user)

    # Aplicar filtro de prioridad si es necesario
    if prioridad != "todas":
        notificaciones = base_query.filter(prioridad=prioridad).order_by(
            "-fechacreacion"
        )
    else:
        notificaciones = base_query.order_by("-fechacreacion")

    # Estadísticas por tipo de prioridad
    alta_prioridad = base_query.filter(prioridad="alta").count()
    media_prioridad = base_query.filter(prioridad="media").count()
    baja_prioridad = base_query.filter(prioridad="baja").count()

    # Paginación
    paginator = Paginator(notificaciones, 10)  # 10 notificaciones por página
    page = request.GET.get("page", 1)

    try:
        notificaciones_paginadas = paginator.page(page)
    except:
        notificaciones_paginadas = paginator.page(1)

    context = {
        "notificaciones": notificaciones_paginadas,
        "is_admin": is_admin,
        "prioridad_actual": prioridad,
        "estadisticas": {
            "alta_prioridad": alta_prioridad,
            "media_prioridad": media_prioridad,
            "baja_prioridad": baja_prioridad,
            "total": alta_prioridad + media_prioridad + baja_prioridad,
        },
    }

    return render(request, "notificaciones/lista_notificaciones.html", context)


@login_required
def lista_alertas(request):
    """Vista para listar todas las alertas"""
    is_admin = request.user.is_staff or request.user.rol == "Administrador"

    # Filtrar alertas según permisos
    if is_admin:
        alertas = Alerta.objects.all()
    else:
        alertas = Alerta.objects.filter(
            idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
            )
        )

    """Muestra la lista completa de alertas."""
    tipo = request.GET.get("tipo", "todas")

    # Filtrar por tipo
    if tipo != "todas":
        alertas = alertas.filter(tipoalerta=tipo).order_by("-fechacreacion")
    else:
        alertas = alertas.all().order_by("-fechacreacion")

    # Paginación
    paginator = Paginator(alertas, 10)
    page = request.GET.get("page", 1)
    alertas_paginadas = paginator.get_page(page)

    # Estadísticas por tipo de alerta
    tipos_alerta = ["retraso", "presupuesto", "riesgo", "bloqueo"]

    # Calcular total por tipo
    tipos_alertas = []
    total_alertas = Alerta.objects.count()

    for tipo_alerta in tipos_alerta:
        count = Alerta.objects.filter(tipoalerta=tipo_alerta).count()
        tipos_alertas.append(
            {
                "tipoalerta": tipo_alerta,
                "total": count,
                "porcentaje": (count / total_alertas * 100) if total_alertas > 0 else 0,
            }
        )

    return render(
        request,
        "alertas/listar_alertas.html",
        {
            "alertas": alertas_paginadas,
            "tipo_actual": tipo,
            "tipos_alerta": tipos_alerta,
            "tipos_alertas": tipos_alertas,
        },
    )


@login_required
def filtrar_alertas(request):
    """Filtra alertas por tipo (endpoint para HTMX)."""
    tipo = request.GET.get("tipo", "todas")

    # Determinar si el usuario es admin
    is_admin = request.user.is_staff or request.user.rol == "Administrador"

    # Query base según permisos
    if is_admin:
        alertas = Alerta.objects.all()
    else:
        alertas = Alerta.objects.filter(
            idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
            )
        )

    tipo = request.GET.get("tipo", "todas")

    # Filtrar por tipo
    if tipo != "todas":
        alertas = alertas.filter(tipoalerta=tipo).order_by("-fechacreacion")
    else:
        alertas = alertas.all().order_by("-fechacreacion")

    # Paginación
    paginator = Paginator(alertas, 10)
    page = request.GET.get("page", 1)
    alertas_paginadas = paginator.get_page(page)

    return render(
        request,
        "alertas/lista_filtrada.html",
        {"alertas": alertas_paginadas, "tipo_actual": tipo},
    )


@login_required
def filtrar_notificaciones(request):
    """Vista para filtrar notificaciones con paginación correcta"""
    prioridad = request.GET.get("prioridad", "todas")
    page = request.GET.get("page", 1)

    is_admin = request.user.is_staff or request.user.rol == "Administrador"

    if is_admin:
        base_query = Notificacion.objects.all()
    else:
        # Query base
        base_query = Notificacion.objects.filter(
            idusuario=request.user, archivada=False
        )

    # Aplicar filtro de prioridad
    if prioridad != "todas":
        notificaciones_filtradas = base_query.filter(prioridad=prioridad).order_by(
            "-fechacreacion"
        )
    else:
        notificaciones_filtradas = base_query.order_by("-fechacreacion")

    # Paginación
    paginator = Paginator(notificaciones_filtradas, 10)  # 10 notificaciones por página

    try:
        notificaciones_paginadas = paginator.page(page)
    except:
        notificaciones_paginadas = paginator.page(1)

    context = {
        "notificaciones": notificaciones_paginadas,
        "prioridad_actual": prioridad,
    }

    # Renderizar con la plantilla lista_filtrada.html
    return render(request, "notificaciones/lista_filtrada.html", context)


@login_required
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


@login_required
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
            return redirect("notificaciones:index")

        except Exception as e:
            messages.error(request, f"Error al marcar notificaciones: {str(e)}")

    return redirect("notificaciones:index")


@login_required  # Asegura que el usuario esté autenticado
def archivar_notificacion(request, id):
    """
    Vista para archivar una notificación
    """
    if request.method == "POST":
        try:
            # Primero intentamos obtener la notificación solo por ID
            notificacion = get_object_or_404(Notificacion, idnotificacion=id)
            is_admin = request.user.is_staff or request.user.rol == "Administrador"
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
            is_admin = request.user.is_staff or request.user.rol == "Administrador"
            # Verificar que el usuario sea el propietario o admin
            if (
                notificacion.idusuario == request.user
                or request.user.is_staff
                or is_admin
            ):
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


@login_required
def estadisticas_notificaciones(request):
    """Vista para mostrar estadísticas de notificaciones según el rol del usuario"""
    try:
        # Determinar si el usuario es admin
        is_admin = request.user.is_staff or request.user.rol == "Administrador"

        # Obtener fechas del filtro
        fecha_fin = request.GET.get("fecha_fin")
        fecha_inicio = request.GET.get("fecha_inicio")

        # Query base según el rol del usuario
        if is_admin:
            base_query = Notificacion.objects.all()
            query_anterior = None
        else:
            base_query = Notificacion.objects.filter(idusuario=request.user)
            query_anterior = None

        # Si hay filtros de fecha, aplicarlos
        if fecha_fin and fecha_inicio:
            fecha_fin = timezone.datetime.strptime(fecha_fin, "%Y-%m-%d")
            fecha_fin = timezone.make_aware(fecha_fin)
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_inicio = timezone.make_aware(fecha_inicio)

            # Calcular período anterior para comparación
            periodo_anterior_inicio = fecha_inicio - timedelta(days=30)
            periodo_anterior_fin = fecha_fin - timedelta(days=30)

            # Aplicar filtro de fechas
            if is_admin:
                query_anterior = Notificacion.objects.filter(
                    fechacreacion__range=[periodo_anterior_inicio, periodo_anterior_fin]
                )
            else:
                query_anterior = Notificacion.objects.filter(
                    idusuario=request.user,
                    fechacreacion__range=[
                        periodo_anterior_inicio,
                        periodo_anterior_fin,
                    ],
                )

            base_query = base_query.filter(
                fechacreacion__range=[fecha_inicio, fecha_fin]
            )

        # Calcular estadísticas
        total = base_query.count()
        no_leidas = base_query.filter(leido=False).count()
        leidas = base_query.filter(leido=True).count()
        archivadas = base_query.filter(archivada=True).count()
        no_archivadas = base_query.filter(archivada=False).count()

        # Calcular porcentajes de cambio si hay período anterior
        if query_anterior:
            total_anterior = query_anterior.count()
            no_leidas_anterior = query_anterior.filter(leido=False).count()
            leidas_anterior = query_anterior.filter(leido=True).count()
            archivadas_anterior = query_anterior.filter(archivada=True).count()
            no_archivadas_anterior = query_anterior.filter(archivada=False).count()

            def calcular_porcentaje_cambio(actual, anterior):
                if anterior == 0:
                    return 100 if actual > 0 else 0
                return ((actual - anterior) / anterior) * 100

            porcentaje_cambio = {
                "total": calcular_porcentaje_cambio(total, total_anterior),
                "no_leidas": calcular_porcentaje_cambio(no_leidas, no_leidas_anterior),
                "leidas": calcular_porcentaje_cambio(leidas, leidas_anterior),
                "archivadas": calcular_porcentaje_cambio(
                    archivadas, archivadas_anterior
                ),
                "no_archivadas": calcular_porcentaje_cambio(
                    no_archivadas, no_archivadas_anterior
                ),
            }
        else:
            porcentaje_cambio = {
                "total": 0,
                "no_leidas": 0,
                "leidas": 0,
                "archivadas": 0,
                "no_archivadas": 0,
            }

        # Estadísticas por prioridad
        por_prioridad = list(
            base_query.values("prioridad")
            .annotate(total=Count("idnotificacion"))
            .order_by("-total")
        )

        # Calcular porcentajes para prioridad
        total_prioridad = sum(item["total"] for item in por_prioridad)
        for item in por_prioridad:
            item["porcentaje"] = (
                (item["total"] / total_prioridad * 100) if total_prioridad > 0 else 0
            )

        # Estadísticas por categoría
        por_categoria = list(
            base_query.values("categoria")
            .annotate(total=Count("idnotificacion"))
            .order_by("-total")
        )

        # Calcular porcentajes para categoría
        total_categoria = sum(item["total"] for item in por_categoria)
        for item in por_categoria:
            item["porcentaje"] = (
                (item["total"] / total_categoria * 100) if total_categoria > 0 else 0
            )

        # Estadísticas por usuario (solo para admin)
        por_usuario = []
        if is_admin:
            por_usuario = list(
                base_query.values("idusuario__nombreusuario")
                .annotate(total=Count("idnotificacion"))
                .order_by("-total")
            )
            total_usuario = sum(item["total"] for item in por_usuario)
            for item in por_usuario:
                item["porcentaje"] = (
                    (item["total"] / total_usuario * 100) if total_usuario > 0 else 0
                )

        context = {
            "total": total,
            "no_leidas": no_leidas,
            "leidas": leidas,
            "archivadas": archivadas,
            "no_archivadas": no_archivadas,
            "porcentaje_cambio": porcentaje_cambio,
            "por_prioridad": por_prioridad,
            "por_categoria": por_categoria,
            "por_usuario": por_usuario if is_admin else [],
            "fecha_inicio": fecha_inicio if fecha_inicio else None,
            "fecha_fin": fecha_fin if fecha_fin else None,
            "is_admin": is_admin,
        }

        return render(request, "notificaciones/estadisticas.html", context)

    except Exception as e:
        messages.error(request, f"Error al procesar las estadísticas: {str(e)}")
        return redirect("notificaciones:index")


@login_required
def estadisticas_alertas(request):
    """Vista para mostrar estadísticas de alertas según el rol del usuario"""
    try:
        # Determinar si el usuario es admin o superuser
        is_admin = (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.rol == "Administrador"
        )

        # Obtener fechas del filtro
        fecha_fin = request.GET.get("fecha_fin")
        fecha_inicio = request.GET.get("fecha_inicio")

        # Si no hay fechas, usar últimos 30 días por defecto
        if not fecha_fin:
            fecha_fin = timezone.now()
        else:
            fecha_fin = timezone.datetime.strptime(fecha_fin, "%Y-%m-%d")
            fecha_fin = timezone.make_aware(fecha_fin)

        if not fecha_inicio:
            fecha_inicio = fecha_fin - timedelta(days=30)
        else:
            fecha_inicio = timezone.datetime.strptime(fecha_inicio, "%Y-%m-%d")
            fecha_inicio = timezone.make_aware(fecha_inicio)

        # Query base según el rol del usuario
        if is_admin:
            base_query = Alerta.objects.all()
        else:
            base_query = Alerta.objects.filter(
                idtarea__idrequerimiento__idproyecto__in=Proyecto.objects.filter(
                    idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
                )
            )

        # Aplicar filtros de fecha si existen
        if fecha_inicio and fecha_fin:
            filtered_query = base_query.filter(
                fechacreacion__range=[fecha_inicio, fecha_fin]
            )
            # Período anterior para comparación
            periodo_anterior_inicio = fecha_inicio - timedelta(days=30)
            periodo_anterior_fin = fecha_fin - timedelta(days=30)
            query_anterior = base_query.filter(
                fechacreacion__range=[periodo_anterior_inicio, periodo_anterior_fin]
            )
        else:
            filtered_query = base_query
            query_anterior = base_query.filter(fechacreacion__lt=fecha_inicio)

        # Calcular estadísticas generales
        total = filtered_query.count()
        activas = filtered_query.filter(activa=True).count()
        resueltas = filtered_query.filter(activa=False).count()

        # Estadísticas del período anterior
        total_anterior = query_anterior.count()
        activas_anterior = query_anterior.filter(activa=True).count()
        resueltas_anterior = query_anterior.filter(activa=False).count()

        # Calcular porcentajes de cambio
        def calcular_porcentaje_cambio(actual, anterior):
            if anterior == 0:
                return 100 if actual > 0 else 0
            return ((actual - anterior) / anterior) * 100

        porcentaje_cambio = {
            "total": calcular_porcentaje_cambio(total, total_anterior),
            "activas": calcular_porcentaje_cambio(activas, activas_anterior),
            "resueltas": calcular_porcentaje_cambio(resueltas, resueltas_anterior),
        }

        # Estadísticas por tipo de alerta
        por_tipo = list(
            filtered_query.values("tipoalerta")
            .annotate(
                total=Count("idalerta"),
                porcentaje=Case(
                    When(total__gt=0, then=100.0 * F("total") / filtered_query.count()),
                    default=0.0,
                    output_field=FloatField(),
                ),
            )
            .order_by("-total")
        )

        # Estadísticas por tarea
        por_tarea = list(
            filtered_query.values("idtarea__nombretarea", "idtarea__estado")
            .annotate(total=Count("idalerta"))
            .order_by("-total")
        )

        # Estadísticas por proyecto (solo para admin)
        por_proyecto = []
        if is_admin:
            por_proyecto = list(
                filtered_query.values(
                    "idtarea__idrequerimiento__idproyecto__nombreproyecto"
                )
                .annotate(
                    total=Count("idalerta"),
                    porcentaje=Case(
                        When(
                            total__gt=0,
                            then=100.0 * F("total") / filtered_query.count(),
                        ),
                        default=0.0,
                        output_field=FloatField(),
                    ),
                )
                .order_by("-total")
            )

        # Historial temporal (para gráfico)
        historico_temporal = (
            filtered_query.annotate(fecha=TruncDate("fechacreacion"))
            .values("fecha")
            .annotate(total=Count("idalerta"))
            .order_by("fecha")
        )

        context = {
            "total": total,
            "activas": activas,
            "resueltas": resueltas,
            "porcentaje_cambio": porcentaje_cambio,
            "por_tipo": por_tipo,
            "por_tarea": por_tarea,
            "por_proyecto": por_proyecto,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "is_admin": is_admin,
            "historico_temporal": historico_temporal,
        }

        return render(request, "alertas/estadisticas.html", context)

    except Exception as e:
        messages.error(request, f"Error al procesar las estadísticas: {str(e)}")
        return redirect("notificaciones:index")


@login_required
def vista_previa_notificacion(request):
    """Vista para renderizar la vista previa de la notificación"""
    usuario_id = request.GET.get("usuario")
    prioridad = request.GET.get("prioridad", "media")
    mensaje = request.GET.get("mensaje", "")
    categoria = request.GET.get("categoria", "")

    try:
        usuario = Usuario.objects.get(idusuario=usuario_id) if usuario_id else None
    except Usuario.DoesNotExist:
        usuario = None

    context = {
        "mensaje": mensaje,
        "prioridad": prioridad,
        "categoria": categoria,
        "usuario": usuario,
    }

    return render(request, "components/vista_previa_notificacion.html", context)


@login_required
def vista_previa_alerta(request):
    """Vista para renderizar la vista previa de la alerta"""
    tarea_id = request.GET.get("tarea")
    tipo_alerta = request.GET.get("tipo_alerta", "")
    mensaje = request.GET.get("mensaje", "")

    try:
        tarea = Tarea.objects.get(idtarea=tarea_id) if tarea_id else None
    except Tarea.DoesNotExist:
        tarea = None

    context = {"mensaje": mensaje, "tipo_alerta": tipo_alerta, "tarea": tarea}

    return render(request, "components/vista_previa_alerta.html", context)


@login_required
def generar_alertas(request):
    """Vista para generar alertas manualmente (solo para administradores)"""
    if not request.user.is_staff and request.user.rol != "Administrador":
        messages.error(request, "No tienes permiso para realizar esta acción")
        return redirect("notificaciones:index")

    alertas_creadas = 0

    if request.method == "POST":
        tipo = request.POST.get("tipo")

        if tipo == "retrasadas":
            alertas_creadas = MonitoreoService.verificar_tareas_retrasadas()
            messages.success(
                request,
                f"Se han generado {alertas_creadas} alertas de tareas retrasadas",
            )
        elif tipo == "presupuesto":
            alertas_creadas = MonitoreoService.verificar_presupuesto_excedido()
            messages.success(
                request,
                f"Se han generado {alertas_creadas} alertas de presupuesto excedido",
            )
        elif tipo == "bloqueo":
            alertas_creadas = MonitoreoService.verificar_tareas_bloqueadas()
            messages.success(
                request,
                f"Se han generado {alertas_creadas} alertas de tareas bloqueadas",
            )
        elif tipo == "todas":
            alertas_retraso = MonitoreoService.verificar_tareas_retrasadas()
            alertas_presupuesto = MonitoreoService.verificar_presupuesto_excedido()
            alertas_bloqueo = MonitoreoService.verificar_tareas_bloqueadas()
            alertas_creadas = alertas_retraso + alertas_presupuesto + alertas_bloqueo
            messages.success(
                request, f"Se han generado {alertas_creadas} alertas en total"
            )

    # Estadísticas sobre alertas actuales
    stats = {
        "total_alertas": Alerta.objects.count(),
        "alertas_activas": Alerta.objects.filter(activa=True).count(),
        "alertas_retraso": Alerta.objects.filter(
            tipoalerta="retraso", activa=True
        ).count(),
        "alertas_presupuesto": Alerta.objects.filter(
            tipoalerta="presupuesto", activa=True
        ).count(),
        "alertas_bloqueo": Alerta.objects.filter(
            tipoalerta="bloqueo", activa=True
        ).count(),
    }

    return render(request, "alertas/generar_alertas_2.html", {"stats": stats})
