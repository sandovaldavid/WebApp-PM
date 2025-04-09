import logging
from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import Proyecto, Requerimiento, Tarea, Equipo
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField, Q
from django.utils.timezone import is_naive, make_aware
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

logger = logging.getLogger(__name__)
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.db.models import (
    Count,
    Avg,
    F,
    ExpressionWrapper,
    DurationField,
    When,
    Case,
    FloatField,
    Sum,
)
from django.utils.timezone import is_naive, make_aware
from dashboard.models import (
    Proyecto,
    Requerimiento,
    Tarea,
    Equipo,
    Historialtarea,
    Alerta,
    Tarearecurso,
    Usuario,
    Notificacion,
)
from django.contrib import messages
from django.db import transaction


@login_required
def index(request):
    vista = request.GET.get("vista", "grid")
    busqueda = request.GET.get("busqueda", "")
    filtro = request.GET.get("filtro", "todos")
    page = request.GET.get("page", 1)

    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Query base según permisos
    if is_admin:
        # Consulta para estadísticas y gráficos
        proyectos_totales = Proyecto.objects.all()
        # Consulta para la vista paginada
        proyectos = Proyecto.objects.all()
    else:
        # Filtrar proyectos relacionados al usuario a través de la cadena de relaciones
        proyectos_totales = Proyecto.objects.filter(
            idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        ).distinct()

        # Filtrar proyectos relacionados al usuario a través de la cadena de relaciones
        proyectos = Proyecto.objects.filter(
            idequipo__miembro__idrecurso__recursohumano__idusuario=request.user
        ).distinct()

    if busqueda:
        proyectos = proyectos.filter(
            Q(nombreproyecto__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if filtro and filtro != "todos":
        proyectos = proyectos.filter(estado=filtro)

    # Obtener fecha actual y hace 6 meses
    now = timezone.now()
    six_months_ago = now - timezone.timedelta(days=180)

    # Obtener proyectos de los últimos 6 meses
    proyectos_periodo = proyectos.filter(fechacreacion__range=(six_months_ago, now))

    # Inicializar diccionarios para almacenar conteos
    meses = []
    completados = []
    creados = []

    # Obtener datos para los últimos 6 meses
    for i in range(6):
        fecha = now - timezone.timedelta(days=30 * i)
        mes_inicio = fecha.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        mes_fin = (mes_inicio + timezone.timedelta(days=32)).replace(
            day=1
        ) - timezone.timedelta(seconds=1)

        # Contar proyectos completados (estado Cierre) en el mes
        completados_mes = proyectos_periodo.filter(
            estado="Cierre", fechamodificacion__range=(mes_inicio, mes_fin)
        ).count()

        # Contar proyectos creados en el mes
        creados_mes = proyectos_periodo.filter(
            fechacreacion__range=(mes_inicio, mes_fin)
        ).count()

        # Agregar datos a las listas
        meses.insert(0, fecha.strftime("%b"))
        completados.insert(0, completados_mes)
        creados.insert(0, creados_mes)

    # Estadísticas
    estadisticas = {
        "total": proyectos_totales.count(),
        "inicio": proyectos_totales.filter(estado="Inicio").count(),
        "planificacion": proyectos_totales.filter(estado="Planificación").count(),
        "ejecucion": proyectos_totales.filter(estado="Ejecución").count(),
        "monitoreo_control": proyectos_totales.filter(
            estado="Monitoreo-Control"
        ).count(),
        "cierre": proyectos_totales.filter(estado="Cierre").count(),
    }
    datos_estado = {
        "labels": [
            "Inicio",
            "Planificación",
            "Ejecución",
            "Monitoreo-Control",
            "Cierre",
        ],
        "data": [
            estadisticas["inicio"],
            estadisticas["planificacion"],
            estadisticas["ejecucion"],
            estadisticas["monitoreo_control"],
            estadisticas["cierre"],
        ],
    }
    datos_tendencia = {"labels": meses, "completados": completados, "creados": creados}
    datos_tiempo = {
        "promedio": [
            # Inicio
            (
                proyectos_totales.filter(estado="Inicio")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos_totales.filter(estado="Inicio").exists()
                else 0
            ),
            # Planificación
            (
                proyectos_totales.filter(estado="Planificación")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos_totales.filter(estado="Planificación").exists()
                else 0
            ),
            # Ejecución
            (
                proyectos_totales.filter(estado="Ejecución")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos_totales.filter(estado="Ejecución").exists()
                else 0
            ),
            # Monitoreo-Control
            (
                proyectos_totales.filter(estado="Monitoreo-Control")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos_totales.filter(estado="Monitoreo-Control").exists()
                else 0
            ),
            # Cierre
            (
                proyectos_totales.filter(estado="Cierre")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            F("fechafin") - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos_totales.filter(estado="Cierre").exists()
                else 0
            ),
        ]
    }

    print(datos_tiempo)

    # Paginación
    proyectos = proyectos.order_by("idproyecto")
    paginator = Paginator(proyectos, 9)
    try:
        proyectos_paginados = paginator.page(page)
    except PageNotAnInteger:
        proyectos_paginados = paginator.page(1)
    except EmptyPage:
        proyectos_paginados = paginator.page(paginator.num_pages)

    return render(
        request,
        "gestion_proyectos/index.html",
        {
            "estadisticas": estadisticas,
            "proyectos_totales": proyectos_totales,
            "proyectos": proyectos_paginados,
            "datos_estado": datos_estado,
            "datos_tendencia": datos_tendencia,
            "datos_tiempo": datos_tiempo,
            "vista": vista,
            "filtros": {"busqueda": busqueda, "filtro": filtro},
            "is_admin": is_admin,  # Agregamos is_admin al contexto
        },
    )


@login_required
def lista_proyectos(request):
    """Vista para listar proyectos"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )

    # Query base
    proyectos = Proyecto.objects.all()

    # Aplicar filtros
    estado = request.GET.get("estado")
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")
    busqueda = request.GET.get("busqueda")

    if estado and estado != "":
        proyectos = proyectos.filter(estado=estado)
    if fecha_inicio and fecha_inicio != "":
        proyectos = proyectos.filter(fechainicio__gte=fecha_inicio)
    if fecha_fin and fecha_fin != "":
        proyectos = proyectos.filter(fechafin__lte=fecha_fin)
    if busqueda and busqueda != "None":
        proyectos = proyectos.filter(nombreproyecto__icontains=busqueda)

    # Ordenar y obtener relaciones
    proyectos = proyectos.order_by("-fechacreacion")

    context = {
        "proyectos": proyectos,
        "estados": [
            "Inicio",
            "Planificación",
            "Ejecución",
            "Monitoreo-Control",
            "Cierre",
        ],
        "filtros": {
            "estado": estado,
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "busqueda": busqueda,
        },
        "is_admin": is_admin,
    }

    return render(request, "gestion_proyectos/lista_proyectos.html", context)


@login_required
def detalle_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)

    # 1. Valor Planeado (PV)
    valor_planeado = (
        Tarea.objects.filter(idrequerimiento__idproyecto=proyecto).aggregate(
            pv=Sum("costoestimado")
        )["pv"]
        or 0
    )

    # 2. Valor Ganado (EV)
    valor_ganado = (
        Tarea.objects.filter(
            idrequerimiento__idproyecto=proyecto, estado="Completada"
        ).aggregate(ev=Sum("costoestimado"))["ev"]
        or 0
    )

    # 3. Costo Real (AC)
    costo_real = (
        Tarea.objects.filter(idrequerimiento__idproyecto=proyecto).aggregate(
            ac=Sum("costoactual")
        )["ac"]
        or 0
    )

    # Cálculo de índices
    cpi = valor_ganado / costo_real if costo_real > 0 else 0
    spi = valor_ganado / valor_planeado if valor_planeado > 0 else 0

    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    presupuestoutilizado = proyecto.presupuestoutilizado or 0
    presupuesto_restante = proyecto.presupuesto - presupuestoutilizado
    desviacion_presupuesto = 0
    if proyecto.presupuestoutilizado and proyecto.presupuesto:
        desviacion_presupuesto = (
            (proyecto.presupuestoutilizado - proyecto.presupuesto)
            / proyecto.presupuesto
        ) * 100

    total_tareas = tareas.count()
    total_requerimientos = requerimientos.count()
    tareas_completadas = tareas.filter(estado="Completada").count()
    progreso = 100.0 * tareas_completadas / total_tareas if total_tareas > 0 else 0.0
    if progreso:
        stroke_dashoffset = 282.7 - (282.7 * progreso / 100)
    else:
        stroke_dashoffset = 282.7

    duracion_estimada = tareas.aggregate(total=Sum("duracionestimada"))["total"] or 0
    duracion_actual = tareas.aggregate(total=Sum("duracionactual"))["total"] or 0

    for requerimiento in requerimientos:
        total_tareas_r = requerimiento.tarea_set.count()
        requerimiento.tareas_pendientes = tareas.filter(
            idrequerimiento=requerimiento, estado="Pendiente"
        ).count()
        requerimiento.tareas_en_progreso = tareas.filter(
            idrequerimiento=requerimiento, estado="En Progreso"
        ).count()
        requerimiento.tareas_completadas = tareas.filter(
            idrequerimiento=requerimiento, estado="Completada"
        ).count()

        # Calcular el porcentaje de progreso (equivalente a la operación en la plantilla)
        if total_tareas_r > 0:
            requerimiento.progreso = int(
                (requerimiento.tareas_completadas * 100) / total_tareas_r
            )
        else:
            requerimiento.progreso = 0

    vista = request.GET.get("vista", "grid")
    busqueda = request.GET.get("busqueda", "")

    if busqueda:
        requerimientos = requerimientos.filter(descripcion__icontains=busqueda)

    return render(
        request,
        "gestion_proyectos/detalle_proyecto.html",
        {
            "proyecto": proyecto,
            "valor_planeado": valor_planeado,
            "valor_ganado": valor_ganado,
            "costo_real": costo_real,
            "cpi": round(cpi, 2),
            "spi": round(spi, 2),
            "requerimientos": requerimientos,
            "tareas": tareas,
            "recursos": recursos,
            "presupuesto_restante": presupuesto_restante,
            "desviacion_presupuesto": desviacion_presupuesto,
            "progreso": progreso,
            "stroke_dashoffset": stroke_dashoffset,
            "duracion_estimada": duracion_estimada,
            "duracion_actual": duracion_actual,
            "total_tareas": total_tareas,
            "tareas_completadas": tareas_completadas,
            "total_requerimientos": total_requerimientos,
            "vista": vista,
            "filtros": {"busqueda": busqueda},
        },
    )


@login_required
def crear_proyecto(request):
    if request.method == "POST":
        # Datos principales del proyecto
        nombreproyecto = request.POST.get("nombreproyecto")
        descripcion = request.POST.get("descripcion")
        estado = request.POST.get("estado")
        fechainicio = request.POST.get("fechainicio")
        fechafin = request.POST.get("fechafin")
        presupuesto = request.POST.get("presupuesto")
        idequipo = request.POST.get("idequipo")

        # Validar que la fecha de inicio sea anterior a la fecha de fin
        if fechainicio >= fechafin:
            equipos = Equipo.objects.all()
            return render(
                request,
                "gestion_proyectos/crear_proyecto.html",
                {
                    "equipos": equipos,
                    "error": "La fecha de inicio debe ser anterior a la fecha de finalización.",
                    "nombreproyecto": nombreproyecto,
                    "descripcion": descripcion,
                    "estado": estado,
                    "fechainicio": fechainicio,
                    "fechafin": fechafin,
                    "presupuesto": presupuesto,
                    "idequipo": idequipo,
                },
            )

        # Obtener el último ID de proyecto y asignar el siguiente ID disponible
        ultimo_proyecto = Proyecto.objects.order_by("-idproyecto").first()
        nuevo_id_proyecto = (ultimo_proyecto.idproyecto + 1) if ultimo_proyecto else 1

        # Crear el proyecto
        now = timezone.now()
        if is_naive(now):
            now = make_aware(now)
        proyecto = Proyecto(
            nombreproyecto=nombreproyecto,
            descripcion=descripcion,
            estado=estado,
            fechainicio=fechainicio,
            fechafin=fechafin,
            presupuesto=presupuesto,
            presupuestoutilizado=0,  # Establecer presupuesto utilizado en 0
            idequipo_id=idequipo,
            fechacreacion=now,
            fechamodificacion=now,
        )
        proyecto.save()

        # Guardar requerimientos asociados
        for key, value in request.POST.items():
            if key.startswith("requerimiento_"):
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía

                    requerimiento = Requerimiento(
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=now,
                        fechamodificacion=now,
                    )
                    requerimiento.save()

        messages.success(request, "Proyecto creado exitosamente.")
        return redirect("gestion_proyectos:lista_proyectos")

    equipos = Equipo.objects.all()
    return render(
        request, "gestion_proyectos/crear_proyecto.html", {"equipos": equipos}
    )


@login_required
def editar_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()

    if request.method == "POST":
        nombreproyecto = request.POST.get("nombreproyecto", proyecto.nombreproyecto)
        descripcion = request.POST.get("descripcion", proyecto.descripcion)
        estado = request.POST.get("estado", proyecto.estado)
        fechainicio = request.POST.get("fechainicio", proyecto.fechainicio)
        fechafin = request.POST.get("fechafin", proyecto.fechafin)
        presupuesto = request.POST.get("presupuesto", proyecto.presupuesto)

        # Validar que la fecha de inicio sea anterior a la fecha de fin
        if fechainicio >= fechafin:
            return render(
                request,
                "gestion_proyectos/editar_proyecto.html",
                {
                    "proyecto": proyecto,
                    "requerimientos": requerimientos,
                    "error": "La fecha de inicio debe ser anterior a la fecha de finalización.",
                },
            )

        now = timezone.now()
        if is_naive(now):
            now = make_aware(now)

        proyecto.nombreproyecto = nombreproyecto
        proyecto.descripcion = descripcion
        proyecto.estado = estado
        proyecto.fechainicio = fechainicio
        proyecto.fechafin = fechafin
        proyecto.presupuesto = presupuesto
        proyecto.fechamodificacion = now
        proyecto.save()

        # Primero manejar eliminaciones para evitar problemas con actualizaciones
        # Manejar eliminaciones
        marked_for_deletion = []
        for key, value in request.POST.items():
            if key.startswith("eliminar_requerimiento") and value.strip():
                marked_for_deletion.append(value)

        if marked_for_deletion:
            for req_id in marked_for_deletion:
                try:
                    requerimiento = Requerimiento.objects.get(idrequerimiento=req_id)
                    # Primero eliminar tareas asociadas
                    Tarea.objects.filter(idrequerimiento=requerimiento).delete()
                    # Luego eliminar el requerimiento
                    requerimiento.delete()
                    messages.success(
                        request, f"Requerimiento #{req_id} eliminado exitosamente."
                    )
                except Requerimiento.DoesNotExist:
                    pass

        # Actualizar requerimientos existentes
        for key, value in request.POST.items():
            if key.startswith("requerimiento_") and not key.startswith(
                "requerimiento_orden_"
            ):
                descripcion_requerimiento = value
                req_id = key.split("_")[1]
                if (
                    descripcion_requerimiento.strip() and req_id.isdigit()
                ):  # Validar descripción no vacía y que sea un ID
                    try:
                        requerimiento = Requerimiento.objects.get(
                            idrequerimiento=req_id
                        )
                        requerimiento.descripcion = descripcion_requerimiento
                        requerimiento.fechamodificacion = now
                        requerimiento.save()
                    except Requerimiento.DoesNotExist:
                        pass  # No creamos nuevos si no existen

        # Guardar nuevos requerimientos (solo aquellos con el prefijo específico)
        for key, value in request.POST.items():
            if key.startswith("nuevo_requerimiento_"):
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    requerimiento = Requerimiento(
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=now,
                        fechamodificacion=now,
                    )
                    requerimiento.save()

        messages.success(request, "Proyecto editado exitosamente.")
        return redirect("gestion_proyectos:detalle_proyecto", idproyecto=idproyecto)

    return render(
        request,
        "gestion_proyectos/editar_proyecto.html",
        {"proyecto": proyecto, "requerimientos": requerimientos},
    )


@login_required
def eliminar_proyecto(request, idproyecto):
    if request.method == "POST":
        try:
            proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
            proyecto.delete()
            return JsonResponse({"success": True})
        except Proyecto.DoesNotExist:
            return JsonResponse({"success": False, "error": "Proyecto no encontrado."})
    return JsonResponse({"success": False, "error": "Método no permitido."})


@login_required
def estadisticas_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    presupuestoutilizado = proyecto.presupuestoutilizado or 0
    presupuesto_restante = proyecto.presupuesto - presupuestoutilizado
    return render(
        request,
        "gestion_proyectos/estadisticas_proyecto.html",
        {
            "proyecto": proyecto,
            "requerimientos": requerimientos,
            "tareas": tareas,
            "recursos": recursos,
            "presupuesto_restante": presupuesto_restante,
        },
    )


@login_required
def filtrar_proyectos(request):
    filtro = request.GET.get("filtro", "todos")
    proyectos = Proyecto.objects.all()

    if filtro == "inicio":
        proyectos = proyectos.filter(estado="Inicio")
    elif filtro == "planificacion":
        proyectos = proyectos.filter(estado="Planificación")
    elif filtro == "ejecucion":
        proyectos = proyectos.filter(estado="Ejecución")
    elif filtro == "monitoreo_control":
        proyectos = proyectos.filter(estado="Monitoreo-Control")
    elif filtro == "cierre":
        proyectos = proyectos.filter(estado="Cierre")

    # Paginación
    paginator = Paginator(proyectos, 9)
    page = request.GET.get("page", 1)
    proyectos_paginados = paginator.get_page(page)

    return render(
        request,
        "components/lista_proyectos.html",
        {"proyectos": proyectos_paginados, "filtro_activo": filtro},
    )


@login_required
def panel_proyectos(request):
    vista = request.GET.get("vista", "grid")
    busqueda = request.GET.get("busqueda", "")
    filtro = request.GET.get("filtro", "")
    page = request.GET.get("page", 1)

    # Query base
    proyectos = Proyecto.objects.all()

    # Total para estadísticas
    proyectos_totales = proyectos

    # Filtros
    if busqueda:
        proyectos = proyectos.filter(
            Q(nombreproyecto__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if filtro and filtro != "todos":
        proyectos = proyectos.filter(estado=filtro)

    # Paginación
    proyectos = proyectos.order_by("idproyecto")
    paginator = Paginator(proyectos, 9)
    try:
        proyectos_paginados = paginator.page(page)
    except PageNotAnInteger:
        proyectos_paginados = paginator.page(1)
    except EmptyPage:
        proyectos_paginados = paginator.page(paginator.num_pages)

    context = {
        "proyectos": proyectos_paginados,
        "proyectos_totales": proyectos_totales,
        "vista": vista,  # Asegurarnos que sea consistente
        "filtros": {"busqueda": busqueda, "filtro": filtro},  # Pasamos el filtro
    }

    return render(request, "components/panel_proyectos.html", context)


@login_required
def panel_lista_proyectos(request):
    """Vista que retorna solo el contenido para actualizaciones HTMX"""
    vista = request.GET.get("vista", "grid")  # Por defecto grid
    busqueda = request.GET.get("busqueda", "")
    filtro = request.GET.get("filtro", "")
    page = request.GET.get("page", 1)

    # Query base
    proyectos = Proyecto.objects.all()

    # Filtros
    if busqueda:
        proyectos = proyectos.filter(
            Q(nombreproyecto__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    if filtro and filtro != "todos":
        proyectos = proyectos.filter(estado=filtro)

    # Paginación
    proyectos = proyectos.order_by("idproyecto")
    paginator = Paginator(proyectos, 9)
    try:
        proyectos_paginados = paginator.page(page)
    except PageNotAnInteger:
        proyectos_paginados = paginator.page(1)
    except EmptyPage:
        proyectos_paginados = paginator.page(paginator.num_pages)

    context = {
        "proyectos": proyectos_paginados,
        "vista": vista,  # Aseguramos que se pase el valor de vista
        "filtros": {
            "busqueda": busqueda,
            "filtro": filtro,
        },  # Pasamos el filtro para la selección
    }

    return render(request, "components/lista_proyectos.html", context)


@login_required
def crear_requerimiento(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        if descripcion:
            now = timezone.now()
            requerimiento = Requerimiento(
                descripcion=descripcion,
                idproyecto=proyecto,
                fechacreacion=now,
                fechamodificacion=now,
            )
            requerimiento.save()
            return redirect("gestion_proyectos:detalle_proyecto", idproyecto=idproyecto)
    return render(
        request, "gestion_proyectos/crear_requerimiento.html", {"proyecto": proyecto}
    )


@login_required
def detalle_requerimiento(request, idrequerimiento):
    requerimiento = get_object_or_404(Requerimiento, idrequerimiento=idrequerimiento)
    tareas = Tarea.objects.filter(idrequerimiento=requerimiento)

    # Handle task estimation request
    if request.method == "POST" and "estimate_tasks" in request.POST:
        try:
            # Import the estimation service
            from redes_neuronales.estimacion_tiempo.model_service import (
                EstimacionTiempoService,
            )

            # Initialize the service
            estimation_service = EstimacionTiempoService()

            # Track estimation results
            success_count = 0
            error_count = 0
            total_tasks = tareas.count()

            # Estimate time for each task
            for tarea in tareas:
                # Skip already completed tasks
                if tarea.estado == "Completada":
                    continue

                # Perform the estimation and save
                success, estimated_time, message = estimation_service.estimate_and_save(
                    tarea.idtarea
                )

                if success:
                    success_count += 1
                else:
                    error_count += 1

            # Show results message
            if success_count > 0:
                messages.success(
                    request,
                    f"Tiempo estimado correctamente para {success_count} de {total_tasks} tareas.",
                )

            if error_count > 0:
                messages.warning(
                    request, f"No se pudo estimar el tiempo para {error_count} tareas."
                )

            if success_count == 0 and error_count == 0:
                messages.info(
                    request,
                    "No se encontraron tareas para estimar o todas están completadas.",
                )

            # Refresh tasks to get updated values
            tareas = Tarea.objects.filter(idrequerimiento=requerimiento)

        except Exception as e:
            logger.error(f"Error en la estimación de tiempos: {e}", exc_info=True)
            messages.error(request, f"Error al estimar tiempos: {str(e)}")

    # Handle task parameterization request
    if request.method == "POST" and "parameterize_tasks" in request.POST:
        try:
            # Import the API service
            from services.apiIntermediaria import APIIntermediaService

            # Initialize the service
            api_service = APIIntermediaService()

            # Track parameterization results
            success_count = 0
            error_count = 0
            total_tasks = tareas.count()

            # Parameterize each task
            for tarea in tareas:
                # Skip already completed tasks
                if tarea.estado == "Completada":
                    continue

                # Call the parameterization service
                result = api_service.parameterize_task(tarea)

                if result["success"]:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(
                        f"Error al parametrizar tarea {tarea.idtarea}: {result.get('error', 'Error desconocido')}"
                    )

            # Show results message
            if success_count > 0:
                messages.success(
                    request,
                    f"Se parametrizaron correctamente {success_count} de {total_tasks} tareas con IA.",
                )

            if error_count > 0:
                messages.warning(
                    request, f"No se pudieron parametrizar {error_count} tareas."
                )

            if success_count == 0 and error_count == 0:
                messages.info(
                    request,
                    "No se encontraron tareas para parametrizar o todas están completadas.",
                )

            # Refresh tasks to get updated values
            tareas = Tarea.objects.filter(idrequerimiento=requerimiento)

        except Exception as e:
            logger.error(f"Error en la parametrización de tareas: {e}", exc_info=True)
            messages.error(request, f"Error al parametrizar tareas: {str(e)}")

    # Calcular estadísticas
    total_tareas = tareas.count()
    tareas_pendientes = tareas.filter(estado="Pendiente").count()
    tareas_en_progreso = tareas.filter(estado="En Progreso").count()
    tareas_completadas = tareas.filter(estado="Completada").count()

    # Calcular el porcentaje de progreso
    progreso = 0
    if total_tareas > 0:
        progreso = (tareas_completadas * 100) / total_tareas

    return render(
        request,
        "gestion_proyectos/detalle_requerimiento.html",
        {
            "requerimiento": requerimiento,
            "tareas": tareas,
            "total_tareas": total_tareas,
            "tareas_pendientes": tareas_pendientes,
            "tareas_en_progreso": tareas_en_progreso,
            "tareas_completadas": tareas_completadas,
            "progreso": progreso,
        },
    )


@login_required
def editar_requerimiento(request, idrequerimiento):
    requerimiento = get_object_or_404(Requerimiento, idrequerimiento=idrequerimiento)
    proyecto = requerimiento.idproyecto
    if request.method == "POST":
        descripcion = request.POST.get("descripcion")
        if descripcion:
            requerimiento.descripcion = descripcion
            requerimiento.fechamodificacion = timezone.now()
            requerimiento.save()
            return redirect(
                "gestion_proyectos:detalle_proyecto", idproyecto=proyecto.idproyecto
            )
    return render(
        request,
        "gestion_proyectos/editar_requerimiento.html",
        {"requerimiento": requerimiento, "proyecto": proyecto},
    )


@login_required
def eliminar_requerimiento(request, idrequerimiento):
    requerimiento = get_object_or_404(Requerimiento, idrequerimiento=idrequerimiento)
    proyecto = requerimiento.idproyecto

    # Contar tareas asociadas
    tareas_asociadas = Tarea.objects.filter(idrequerimiento=requerimiento)
    task_count = tareas_asociadas.count()
    has_tasks = task_count > 0

    if request.method == "POST":
        confirmed = request.POST.get("confirmed_task_deletion") == "1"

        try:
            with transaction.atomic():
                # Eliminar primero las tareas asociadas
                if has_tasks:
                    # Eliminar recursos asignados a las tareas
                    for tarea in tareas_asociadas:
                        Tarearecurso.objects.filter(idtarea=tarea).delete()
                        # Eliminar alertas asociadas
                        Alerta.objects.filter(idtarea=tarea).delete()
                        # Eliminar historiales
                        Historialtarea.objects.filter(idtarea=tarea).delete()

                    # Ahora eliminar las tareas
                    tareas_asociadas.delete()

                # Finalmente eliminar el requerimiento
                requerimiento.delete()

                messages.success(
                    request,
                    (
                        f"Requerimiento eliminado exitosamente junto con {task_count} tareas asociadas."
                        if task_count > 0
                        else "Requerimiento eliminado exitosamente."
                    ),
                )
                return redirect(
                    "gestion_proyectos:detalle_proyecto", idproyecto=proyecto.idproyecto
                )

        except Exception as e:
            messages.error(request, f"Error al eliminar: {str(e)}")

    # Si es GET, mostrar la página de confirmación
    return render(
        request,
        "gestion_proyectos/eliminar_requerimiento.html",
        {
            "requerimiento": requerimiento,
            "proyecto": proyecto,
            "has_tasks": has_tasks,
            "task_count": task_count,
        },
    )


@login_required
def ajustar_fechas(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    if request.method == "POST":
        fechainicio = request.POST.get("fechainicio")
        fechafin = request.POST.get("fechafin")
        enviar_notificacion = request.POST.get("enviar_notificacion") == "on"

        # Guardar cambios en el proyecto
        proyecto.fechainicio = fechainicio
        proyecto.fechafin = fechafin
        proyecto.fechamodificacion = timezone.now()
        proyecto.save()

        # Enviar notificaciones si la opción está marcada
        if enviar_notificacion and proyecto.idequipo:
            # Buscar usuarios relacionados con el equipo del proyecto
            from django.db.models import F

            # Obtener los usuarios que son miembros del equipo del proyecto
            usuarios = Usuario.objects.filter(
                recursohumano__idrecurso__miembro__idequipo=proyecto.idequipo
            ).distinct()

            # Crear notificaciones para cada usuario
            contador_notificaciones = 0
            for usuario in usuarios:
                if (
                    usuario.notif_sistema
                ):  # Solo enviar si el usuario tiene habilitadas las notificaciones
                    Notificacion.objects.create(
                        idusuario=usuario,
                        mensaje=f"Las fechas del proyecto '{proyecto.nombreproyecto}' han sido modificadas. Nueva fecha de inicio: {fechainicio}, nueva fecha de fin: {fechafin}",
                        leido=False,
                        fechacreacion=timezone.now(),
                        prioridad="media",
                        categoria="Otro",
                        archivada=False,
                    )
                    contador_notificaciones += 1

            if contador_notificaciones > 0:
                messages.success(
                    request,
                    f"Fechas del proyecto ajustadas y notificaciones enviadas a {contador_notificaciones} miembros del equipo.",
                )
            else:
                messages.success(
                    request,
                    "Fechas del proyecto ajustadas exitosamente. No se enviaron notificaciones.",
                )
        else:
            messages.success(request, "Fechas del proyecto ajustadas exitosamente.")

        return redirect(
            "gestion_proyectos:detalle_proyecto", idproyecto=proyecto.idproyecto
        )

    return render(
        request, "gestion_proyectos/ajustar_fechas.html", {"proyecto": proyecto}
    )


@login_required
def ajustar_presupuesto(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    if request.method == "POST":
        presupuesto = request.POST.get("presupuesto")
        presupuestoutilizado = request.POST.get("presupuestoutilizado")
        proyecto.presupuesto = presupuesto
        proyecto.presupuestoutilizado = presupuestoutilizado
        proyecto.fechamodificacion = timezone.now()
        proyecto.save()
        messages.success(request, "Presupuesto del proyecto ajustado exitosamente.")
        return redirect(
            "gestion_proyectos:detalle_proyecto", idproyecto=proyecto.idproyecto
        )
    return render(
        request, "gestion_proyectos/ajustar_presupuesto.html", {"proyecto": proyecto}
    )


@login_required
def analisis_valor_ganado(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    import json
    from datetime import datetime, timedelta

    # Obtener requerimientos y tareas del proyecto
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)

    # Cálculos básicos de Valor Ganado
    valor_planeado = tareas.aggregate(pv=Sum("costoestimado"))["pv"] or 0
    valor_ganado = (
        tareas.filter(estado="Completada").aggregate(ev=Sum("costoestimado"))["ev"] or 0
    )
    costo_real = tareas.aggregate(ac=Sum("costoactual"))["ac"] or 0

    # Varianzas
    varianza_cronograma = valor_ganado - valor_planeado
    varianza_costo = valor_ganado - costo_real

    # Índices de rendimiento
    spi = valor_ganado / valor_planeado if valor_planeado > 0 else 0
    cpi = valor_ganado / costo_real if costo_real > 0 else 0

    # Estimaciones
    bac = proyecto.presupuesto or 0
    eac = bac / cpi if cpi > 0 else 0
    etc = eac - costo_real
    vac = bac - eac
    tcpi = (bac - valor_ganado) / (bac - costo_real) if (bac - costo_real) > 0 else 0

    # Datos para el Burndown Chart
    tareas_totales = tareas.count()
    fecha_inicio = proyecto.fechainicio
    fecha_fin = proyecto.fechafin

    burndown_labels = []
    burndown_ideal = []
    burndown_real = []

    if fecha_inicio and fecha_fin and fecha_inicio < fecha_fin:
        # Generar fechas entre inicio y fin
        dias_totales = (fecha_fin - fecha_inicio).days
        fechas = [
            (fecha_inicio + timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(dias_totales + 1)
        ]

        # Calcular tareas completadas por día
        tareas_completadas_por_dia = {}
        for tarea in tareas.filter(estado="Completada"):
            if tarea.fechamodificacion:
                fecha_str = tarea.fechamodificacion.date().strftime("%Y-%m-%d")
                if fecha_str in tareas_completadas_por_dia:
                    tareas_completadas_por_dia[fecha_str] += 1
                else:
                    tareas_completadas_por_dia[fecha_str] = 1

        # Calcular tareas restantes por día
        tareas_restantes = tareas_totales
        tareas_restantes_por_dia = {}

        for fecha in fechas:
            tareas_restantes -= tareas_completadas_por_dia.get(fecha, 0)
            tareas_restantes_por_dia[fecha] = tareas_restantes

        # Línea ideal (disminución uniforme)
        ideal_por_dia = tareas_totales / (dias_totales + 1) if dias_totales > 0 else 0
        ideal_restante = tareas_totales

        for fecha in fechas:
            burndown_labels.append(fecha)
            burndown_real.append(tareas_restantes_por_dia[fecha])
            ideal_restante -= ideal_por_dia
            burndown_ideal.append(max(0, ideal_restante))

    # Datos para el diagrama de Gantt
    gantt_data = []
    for tarea in tareas:
        if tarea.fechainicio and tarea.fechafin:
            gantt_data.append(
                {
                    "id": tarea.idtarea,
                    "nombre": tarea.nombretarea,
                    "inicio": tarea.fechainicio.strftime("%Y-%m-%d"),
                    "fin": tarea.fechafin.strftime("%Y-%m-%d"),
                    "estado": tarea.estado,
                    "progreso": (
                        100
                        if tarea.estado == "Completada"
                        else (50 if tarea.estado == "En Progreso" else 0)
                    ),
                }
            )

    context = {
        "proyecto": proyecto,
        "valor_planeado": valor_planeado,
        "valor_ganado": valor_ganado,
        "costo_real": costo_real,
        "varianza_cronograma": varianza_cronograma,
        "varianza_costo": varianza_costo,
        "cpi": round(cpi, 2),
        "spi": round(spi, 2),
        "eac": round(eac, 2),
        "etc": round(etc, 2),
        "vac": round(vac, 2),
        "tcpi": round(tcpi, 2),
        "burndown_labels": json.dumps(burndown_labels),
        "burndown_ideal": json.dumps(burndown_ideal),
        "burndown_real": json.dumps(burndown_real),
        "gantt_data": json.dumps(gantt_data),
        "tareas": tareas,
        "presupuesto_total": bac,
        "porcentaje_completado": (valor_ganado / bac * 100) if bac > 0 else 0,
    }

    return render(request, "gestion_proyectos/analisis_valor_ganado.html", context)
