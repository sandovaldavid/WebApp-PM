from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models.functions import TruncMonth
from dashboard.models import (
    Tarea,
    Historialtarea,
    Tarearecurso,
    Recurso,
    Alerta,
    Requerimiento,
    Historialalerta,
)

# Create your views here.


@login_required
def index(request):
    """Vista principal de gestión de tareas"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Filtrar tareas según el tipo de usuario
    if is_admin:
        tareas = Tarea.objects.all().select_related("idrequerimiento__idproyecto")
    else:
        # Filtrar tareas relacionadas al usuario
        tareas = Tarea.objects.filter(
            idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        ).select_related("idrequerimiento__idproyecto")

    # Estadísticas generales
    estadisticas = {
        "total": tareas.count(),
        "pendientes": tareas.filter(estado="Pendiente").count(),
        "en_progreso": tareas.filter(estado="En Progreso").count(),
        "completadas": tareas.filter(estado="Completada").count(),
    }

    # Datos para el gráfico de estado (Donut)
    datos_estado = {
        "labels": ["Pendientes", "En Progreso", "Completadas"],
        "data": [
            estadisticas["pendientes"],
            estadisticas["en_progreso"],
            estadisticas["completadas"],
        ],
    }

    # Datos para el gráfico de prioridades (Barras)
    prioridades = list(
        tareas.values("prioridad")
        .annotate(total=Count("idtarea"))
        .order_by("prioridad")
    )

    datos_prioridad = {
        "labels": ["Baja", "Media", "Alta"],
        "data": [
            next((p["total"] for p in prioridades if p["prioridad"] == 1), 0),
            next((p["total"] for p in prioridades if p["prioridad"] == 2), 0),
            next((p["total"] for p in prioridades if p["prioridad"] == 3), 0),
        ],
    }

    # Datos para el gráfico de tendencia (Líneas)
    # Obtener datos de los últimos 6 meses
    ahora = timezone.now()
    seis_meses_atras = ahora - timezone.timedelta(days=180)

    tendencia_completadas = list(
        tareas.filter(estado="Completada", fechamodificacion__gte=seis_meses_atras)
        .annotate(mes=TruncMonth("fechamodificacion"))
        .values("mes")
        .annotate(total=Count("idtarea"))
        .order_by("mes")
    )

    tendencia_creadas = list(
        tareas.filter(fechacreacion__gte=seis_meses_atras)
        .annotate(mes=TruncMonth("fechacreacion"))
        .values("mes")
        .annotate(total=Count("idtarea"))
        .order_by("mes")
    )

    datos_tendencia = {
        "completadas": [t["total"] for t in tendencia_completadas[-6:]],
        "creadas": [t["total"] for t in tendencia_creadas[-6:]],
    }

    # Datos para el gráfico de tiempo promedio (Barras Horizontales)
    # Calcular promedio de días por estado
    datos_tiempo = {
        "promedio": [
            # Pendientes
            (
                tareas.filter(estado="Pendiente")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechacreacion"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if tareas.filter(estado="Pendiente").exists()
                else 0
            ),
            # En Progreso
            (
                tareas.filter(estado="En progreso")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechacreacion"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if tareas.filter(estado="En pogreso").exists()
                else 0
            ),
            # Completadas
            (
                tareas.filter(estado="Completada")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            F("fechamodificacion") - F("fechacreacion"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if tareas.filter(estado="Completada").exists()
                else 0
            ),
        ]
    }

    context = {
        "tareas": tareas,
        "estadisticas": estadisticas,
        "datos_estado": datos_estado,
        "datos_prioridad": datos_prioridad,
        "datos_tendencia": datos_tendencia,
        "datos_tiempo": datos_tiempo,
        "is_admin": is_admin,
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


@login_required
def tareas_programadas(request):
    """Vista para gestionar tareas programadas"""
    # Obtener filtros
    estado = request.GET.get("estado", "")
    frecuencia = request.GET.get("frecuencia", "")
    fecha_desde = request.GET.get("fecha_desde", "")
    fecha_hasta = request.GET.get("fecha_hasta", "")

    # Query base
    tareas = Tarea.objects.all().select_related("idrequerimiento__idproyecto")

    # Aplicar filtros
    if estado:
        tareas = tareas.filter(estado=estado)
    if frecuencia:
        tareas = tareas.filter(frecuencia=frecuencia)
    if fecha_desde:
        tareas = tareas.filter(fechainicio__gte=fecha_desde)
    if fecha_hasta:
        tareas = tareas.filter(fechafin__lte=fecha_hasta)

    # Estadísticas
    estadisticas = {
        "total": tareas.count(),
        "completadas": tareas.filter(estado="Completada").count(),
        "en_progreso": tareas.filter(estado="En progreso").count(),
        "pendientes": tareas.filter(estado="Pendiente").count(),
    }

    # Historial de ejecuciones
    historial = (
        Historialtarea.objects.filter(idtarea__in=tareas)
        .select_related("idtarea")
        .order_by("-fechacambio")[:10]
    )

    context = {
        "tareas_programadas": tareas,
        "estadisticas": estadisticas,
        "historial_ejecuciones": historial,
        "estados_tarea": ["Pendiente", "En Progreso", "Completada"],
        "frecuencias": ["Diaria", "Semanal", "Mensual"],
        # Mantener los filtros seleccionados
        "filtros": {
            "estado": estado,
            "frecuencia": frecuencia,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        },
    }

    return render(request, "gestion_tareas_programadas/index.html", context)


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


@login_required
def crear_tarea(request):
    """Vista para crear una nueva tarea"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            requerimiento_id = request.POST.get("requerimiento")
            nombre = request.POST.get("nombre")
            estado = request.POST.get("estado")
            prioridad = request.POST.get("prioridad")
            duracion_estimada = request.POST.get("duracion_estimada")
            fecha_inicio = request.POST.get("fecha_inicio")
            fecha_fin = request.POST.get("fecha_fin")

            # Validaciones
            if not all(
                [
                    requerimiento_id,
                    nombre,
                    estado,
                    prioridad,
                    duracion_estimada,
                    fecha_inicio,
                    fecha_fin,
                ]
            ):
                messages.error(request, "Todos los campos son requeridos")
                return redirect("gestion_tareas:crear_tarea")

            # Verificar que la fecha de fin sea posterior a la de inicio
            if fecha_fin < fecha_inicio:
                messages.error(
                    request, "La fecha de fin debe ser posterior a la fecha de inicio"
                )
                return redirect("gestion_tareas:crear_tarea")

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

            # Registrar en el historial usando los nombres correctos de campos
            Historialtarea.objects.create(
                idtarea=tarea,
                fechacambio=timezone.now(),
                descripcioncambio=f"Tarea creada con estado: {estado}",  # Cambio aquí
            )

            messages.success(request, "Tarea creada exitosamente")
            return redirect("gestion_tareas:index")

        except Exception as e:
            messages.error(request, f"Error al crear la tarea: {str(e)}")
            return redirect("gestion_tareas:crear_tarea")

    # GET request: mostrar formulario
    try:
        context = {
            "requerimientos": Requerimiento.objects.all(),
            "estados_tarea": ["Pendiente", "En Progreso", "Completada"],
            "prioridades": ["Baja", "Media", "Alta"],
            "fecha_minima": timezone.now().date(),
        }
        return render(request, "gestion_tareas/crear_tarea.html", context)

    except Exception as e:
        messages.error(request, f"Error al cargar el formulario: {str(e)}")
        return redirect("gestion_tareas:index")


@login_required
def editar_tarea(request, id):
    """Vista para editar una tarea existente"""
    # Obtener la tarea o devolver 404
    tarea = get_object_or_404(Tarea, idtarea=id)

    if request.method == "POST":
        try:
            # Obtener datos del formulario
            requerimiento_id = request.POST.get("requerimiento")
            nombre = request.POST.get("nombre")
            estado = request.POST.get("estado")
            prioridad = request.POST.get("prioridad")
            duracion_estimada = request.POST.get("duracion_estimada")
            duracion_actual = request.POST.get("duracion_actual")
            costo_estimado = request.POST.get("costo_estimado")
            costo_actual = request.POST.get("costo_actual")
            fecha_inicio = request.POST.get("fecha_inicio")
            fecha_fin = request.POST.get("fecha_fin")

            # Validaciones
            if not all(
                [
                    requerimiento_id,
                    nombre,
                    estado,
                    prioridad,
                    duracion_estimada,
                    fecha_inicio,
                    fecha_fin,
                ]
            ):
                messages.error(request, "Todos los campos obligatorios son requeridos")
                return redirect("gestion_tareas:editar_tarea", id=id)

            # Verificar que la fecha de fin sea posterior a la de inicio
            if fecha_fin < fecha_inicio:
                messages.error(
                    request, "La fecha de fin debe ser posterior a la fecha de inicio"
                )
                return redirect("gestion_tareas:editar_tarea", id=id)

            # Actualizar la tarea
            tarea.idrequerimiento_id = requerimiento_id
            tarea.nombretarea = nombre
            tarea.estado = estado
            tarea.prioridad = prioridad
            tarea.duracionestimada = duracion_estimada
            tarea.duracionactual = duracion_actual or None
            tarea.costoestimado = costo_estimado
            tarea.costoactual = costo_actual or None
            tarea.fechainicio = fecha_inicio
            tarea.fechafin = fecha_fin
            tarea.fechamodificacion = timezone.now()
            tarea.save()

            # Registrar en el historial
            Historialtarea.objects.create(
                idtarea=tarea,
                fechacambio=timezone.now(),
                descripcioncambio=f"Tarea actualizada - Estado: {estado}",
            )

            messages.success(request, "Tarea actualizada exitosamente")
            return redirect("gestion_tareas:detalle_tarea", id=id)

        except Exception as e:
            messages.error(request, f"Error al actualizar la tarea: {str(e)}")
            return redirect("gestion_tareas:editar_tarea", id=id)

    # GET request
    try:
        context = {
            "tarea": tarea,
            "requerimientos": Requerimiento.objects.all(),
            "estados_tarea": ["Pendiente", "En Progreso", "Completada"],
            "prioridades": ["Baja", "Media", "Alta"],
            "fecha_minima": timezone.now().date(),
        }
        return render(request, "gestion_tareas/editar_tarea.html", context)

    except Exception as e:
        messages.error(request, f"Error al cargar el formulario: {str(e)}")
        return redirect("gestion_tareas:detalle_tarea", id=id)


@login_required
def tarea_marcar_completada(request, id):
    """Vista para marcar una tarea como completada"""
    if request.method == "POST":
        try:
            # Obtener la tarea
            tarea = get_object_or_404(Tarea, idtarea=id)

            # Actualizar estado
            tarea.estado = "Completada"
            tarea.fechamodificacion = timezone.now()

            # Si no hay duración actual, usar la estimada
            if not tarea.duracionactual:
                tarea.duracionactual = tarea.duracionestimada

            # Si no hay costo actual, usar el estimado
            if not tarea.costoactual:
                tarea.costoactual = tarea.costoestimado

            tarea.save()

            # Registrar en el historial
            Historialtarea.objects.create(
                idtarea=tarea,
                fechacambio=timezone.now(),
                descripcioncambio="Tarea marcada como completada",
            )

            # Verificar si hay alertas activas y resolverlas
            alertas = Alerta.objects.filter(idtarea=tarea, activa=True)
            for alerta in alertas:
                alerta.activa = False
                alerta.save()
                Historialalerta.objects.create(
                    idalerta=alerta, fecharesolucion=timezone.now()
                )

            messages.success(request, "Tarea marcada como completada exitosamente")

        except Exception as e:
            messages.error(
                request, f"Error al marcar la tarea como completada: {str(e)}"
            )

        return redirect("gestion_tareas:detalle_tarea", id=id)

    return redirect("gestion_tareas:detalle_tarea", id=id)


@login_required
def tareas_programadas(request):
    """Vista para gestionar tareas programadas"""
    # Obtener todas las tareas programadas
    tareas = Tarea.objects.all().select_related("idrequerimiento__idproyecto")

    # Estadísticas
    estadisticas = {
        "total": tareas.count(),
        "completadas": tareas.filter(estado="Completada").count(),
        "en_progreso": tareas.filter(estado="En progreso").count(),
        "fallidas": tareas.filter(estado="Fallida").count(),
    }

    # Historial de ejecuciones
    historial = (
        Historialtarea.objects.all()
        .select_related("idtarea")
        .order_by("-fechacambio")[:10]
    )

    context = {
        "tareas_programadas": tareas,
        "estadisticas": estadisticas,
        "historial_ejecuciones": historial,
        "estados_tarea": ["Pendiente", "En Progreso", "Completada", "Fallida"],
        "frecuencias": ["Diaria", "Semanal", "Mensual"],
    }

    return render(request, "gestion_tareas_programadas/index.html", context)


def ejecutar_tarea(request, id):
    tarea = get_object_or_404(Tarea, idtarea=id)
    tarea.estado = "En Progreso"
    tarea.save()
    Historialtarea.objects.create(
        idtarea=tarea,
        fechacambio=timezone.now(),
        descripcioncambio="Tarea en progreso",
    )
    messages.success(request, "Tarea en progreso")
    return redirect("gestion_tareas:detalle_tarea", id=id)


@login_required
def eliminar_tarea(request, id):
    """Vista para eliminar una tarea y sus registros relacionados"""
    try:
        tarea = get_object_or_404(Tarea, idtarea=id)

        # Eliminar registros relacionados
        Historialtarea.objects.filter(idtarea=tarea).delete()
        Tarearecurso.objects.filter(idtarea=tarea).delete()
        Alerta.objects.filter(idtarea=tarea).delete()
        # Eliminar la tarea
        tarea.delete()

        messages.success(request, "Tarea eliminada exitosamente")
        return redirect("gestion_tareas:index")

    except Exception as e:
        messages.error(request, f"Error al eliminar la tarea: {str(e)}")
        return redirect("gestion_tareas:index")


@login_required
def lista_tareas(request):
    """Vista para listar tareas"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Query base
    if is_admin:
        tareas = Tarea.objects.all()
    else:
        tareas = Tarea.objects.filter(
            idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        )

    # Aplicar filtros
    estado = request.GET.get("estado")
    prioridad = request.GET.get("prioridad")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")
    busqueda = request.GET.get("busqueda")

    if estado:
        tareas = tareas.filter(estado=estado)
    if prioridad:
        tareas = tareas.filter(prioridad=prioridad)
    if fecha_desde:
        tareas = tareas.filter(fechainicio__gte=fecha_desde)
    if fecha_hasta:
        tareas = tareas.filter(fechafin__lte=fecha_hasta)
    if busqueda:
        tareas = tareas.filter(nombretarea__icontains=busqueda)

    # Ordenar y obtener relaciones
    tareas = tareas.select_related("idrequerimiento__idproyecto").order_by(
        "-fechacreacion"
    )

    context = {
        "tareas": tareas,
        "estados": ["Pendiente", "En Progreso", "Completada"],
        "prioridades": [1, 2, 3],
        "filtros": {
            "estado": estado,
            "prioridad": prioridad,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
            "busqueda": busqueda,
        },
        "is_admin": is_admin,
    }

    return render(request, "gestion_tareas/lista_tareas.html", context)


@login_required
def panel_tareas(request):
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Obtener tareas según el rol
    if is_admin:
        tareas = Tarea.objects.all()
    else:
        tareas = Tarea.objects.filter(
            idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        )

    # Aplicar filtros
    filtro = request.GET.get("filtro", "todas")
    if filtro == "pendientes":
        tareas = tareas.filter(estado="Pendiente")
    elif filtro == "en_progreso":
        tareas = tareas.filter(estado="En Progreso")
    elif filtro == "completadas":
        tareas = tareas.filter(estado="Completada")

    # Ordenar tareas
    tareas = tareas.order_by("-fechamodificacion")

    # Paginación
    paginator = Paginator(tareas, 9)  # 9 tareas por página
    page = request.GET.get("page")
    tareas_paginadas = paginator.get_page(page)

    context = {
        "tareas": tareas_paginadas,
        "filtro_activo": filtro,
        "is_admin": is_admin,
    }

    return render(request, "components/panel_tareas.html", context)


@login_required
def filtrar_tareas(request):
    """Vista para filtrar tareas via HTMX"""
    try:
        # Verificar si es admin
        is_admin = (
            request.user.is_staff
            or request.user.is_superuser
            or request.user.rol == "Administrador"
        )

        # Obtener tareas según el rol
        if is_admin:
            tareas = Tarea.objects.all()
        else:
            tareas = Tarea.objects.filter(
                idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
            )

        # Obtener filtro
        filtro = request.GET.get("filtro", "todas")

        # Aplicar filtros
        if filtro == "pendientes":
            tareas = tareas.filter(estado="Pendiente")
        elif filtro == "en_progreso":
            tareas = tareas.filter(estado="En Progreso")
        elif filtro == "completadas":
            tareas = tareas.filter(estado="Completada")

        # Optimizar consultas
        tareas = tareas.select_related(
            "idrequerimiento", "idrequerimiento__idproyecto"
        ).order_by("-fechamodificacion")

        # Paginación
        paginator = Paginator(tareas, 9)
        page = request.GET.get("page", 1)
        tareas_paginadas = paginator.get_page(page)

        context = {
            "tareas": tareas_paginadas,
            "filtro_activo": filtro,
            "is_admin": is_admin,
        }

        return render(request, "components/lista_tareas.html", context)

    except Exception as e:
        return HttpResponse(
            f'<div class="text-red-500 p-4">Error al filtrar tareas: {str(e)}</div>',
            status=500,
        )


@login_required
def lista_tareas_programadas(request):
    """Vista para listar todas las tareas programadas"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Query base según permisos
    if is_admin:
        tareas = Tarea.objects.all()
    else:
        tareas = Tarea.objects.filter(
            idrequerimiento__idproyecto__idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        )

    # Aplicar filtros
    estado = request.GET.get("estado")
    frecuencia = request.GET.get("frecuencia")
    fecha_desde = request.GET.get("fecha_desde")
    fecha_hasta = request.GET.get("fecha_hasta")

    if estado:
        tareas = tareas.filter(estado=estado)
    if frecuencia:
        tareas = tareas.filter(frecuencia=frecuencia)
    if fecha_desde:
        tareas = tareas.filter(fechainicio__gte=fecha_desde)
    if fecha_hasta:
        tareas = tareas.filter(fechafin__lte=fecha_hasta)

    # Optimizar consultas
    tareas = tareas.select_related(
        "idrequerimiento", "idrequerimiento__idproyecto"
    ).order_by("-fechamodificacion")

    # Estadísticas
    estadisticas = {
        "total": tareas.count(),
        "completadas": tareas.filter(estado="Completada").count(),
        "en_progreso": tareas.filter(estado="En Progreso").count(),
        "fallidas": tareas.filter(estado="Fallida").count(),
    }

    # Paginación
    paginator = Paginator(tareas, 9)  # 9 tareas por página
    page = request.GET.get("page")
    tareas_paginadas = paginator.get_page(page)

    context = {
        "tareas": tareas_paginadas,
        "estadisticas": estadisticas,
        "estados_tarea": ["Pendiente", "En Progreso", "Completada", "Fallida"],
        "frecuencias": ["Diaria", "Semanal", "Mensual"],
        "filtros": {
            "estado": estado,
            "frecuencia": frecuencia,
            "fecha_desde": fecha_desde,
            "fecha_hasta": fecha_hasta,
        },
        "is_admin": is_admin,
    }

    return render(
        request, "gestion_tareas_programadas/lista_tareas_programadas.html", context
    )


@login_required
def crear_tarea_programada(request):
    """Vista para crear una nueva tarea programada"""
    if request.method == "POST":
        try:
            # Obtener datos del formulario
            requerimiento_id = request.POST.get("requerimiento")
            nombre = request.POST.get("nombre")
            estado = request.POST.get("estado")
            prioridad = request.POST.get("prioridad")
            frecuencia = request.POST.get("frecuencia")
            duracion_estimada = request.POST.get("duracion_estimada")
            costo_estimado = request.POST.get("costo_estimado")
            fecha_inicio = request.POST.get("fecha_inicio")
            fecha_fin = request.POST.get("fecha_fin")

            # Validaciones
            if not all(
                [
                    requerimiento_id,
                    nombre,
                    estado,
                    prioridad,
                    frecuencia,
                    duracion_estimada,
                    costo_estimado,
                    fecha_inicio,
                    fecha_fin,
                ]
            ):
                messages.error(request, "Todos los campos son requeridos")
                return redirect("gestion_tareas:crear_tarea_programada")

            # Verificar que la fecha de fin sea posterior a la de inicio
            if fecha_fin < fecha_inicio:
                messages.error(
                    request, "La fecha límite debe ser posterior a la primera ejecución"
                )
                return redirect("gestion_tareas:crear_tarea_programada")

            # Crear la tarea programada
            tarea = Tarea.objects.create(
                idrequerimiento_id=requerimiento_id,
                nombretarea=nombre,
                estado=estado,
                prioridad=prioridad,
                duracionestimada=duracion_estimada,
                costoestimado=costo_estimado,
                fechainicio=fecha_inicio,
                fechafin=fecha_fin,
                fechacreacion=timezone.now(),
                fechamodificacion=timezone.now(),
            )

            # Registrar en el historial
            Historialtarea.objects.create(
                idtarea=tarea,
                fechacambio=timezone.now(),
                descripcioncambio=f"Tarea programada creada con frecuencia {frecuencia}",
            )

            messages.success(request, "Tarea programada creada exitosamente")
            return redirect("gestion_tareas:lista_tareas_programadas")

        except Exception as e:
            messages.error(request, f"Error al crear la tarea programada: {str(e)}")
            return redirect("gestion_tareas:crear_tarea_programada")

    # GET request
    try:
        context = {
            "requerimientos": Requerimiento.objects.all(),
            "estados_tarea": ["Pendiente", "En Progreso"],
            "frecuencias": ["Diaria", "Semanal", "Mensual"],
            "fecha_minima": timezone.now(),
        }
        return render(
            request, "gestion_tareas_programadas/crear_tarea_programada.html", context
        )

    except Exception as e:
        messages.error(request, f"Error al cargar el formulario: {str(e)}")
        return redirect("gestion_tareas:lista_tareas_programadas")


def eliminar_tarea_programada(request):
    return None
