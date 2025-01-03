from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import Proyecto, Requerimiento, Tarea, Equipo
from django.utils import timezone
from django.db.models import Count, Avg, F, ExpressionWrapper, DurationField
from django.utils.timezone import is_naive, make_aware
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Case, When, FloatField, Sum, F

@login_required
def index(request):
    proyectos = Proyecto.objects.all()
    estadisticas = {
        'total': proyectos.count(),
        'inicio': proyectos.filter(estado='Inicio').count(),
        'planificacion': proyectos.filter(estado='Planificación').count(),
        'ejecucion': proyectos.filter(estado='Ejecución').count(),
        'monitoreo_control': proyectos.filter(estado='Monitoreo-Control').count(),
        'cierre': proyectos.filter(estado='Cierre').count(),
    }
    datos_estado = {
        'labels': ['Inicio', 'Planificación', 'Ejecución', 'Monitoreo-Control', 'Cierre'],
        'data': [estadisticas['inicio'], estadisticas['planificacion'], estadisticas['ejecucion'], estadisticas['monitoreo_control'], estadisticas['cierre']]
    }
    datos_tendencia = {
        'completados': [10, 15, 8, 12, 20, 15],
        'creados': [8, 12, 15, 10, 18, 20]
    }
    datos_tiempo = {
        "promedio": [
            # Inicio
            (
                proyectos.filter(estado="Inicio")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos.filter(estado="Inicio").exists()
                else 0
            ),
            # Planificación
            (
                proyectos.filter(estado="Planificación")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos.filter(estado="Planificación").exists()
                else 0
            ),
            # Ejecución
            (
                proyectos.filter(estado="Ejecución")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos.filter(estado="Ejecución").exists()
                else 0
            ),
            # Monitoreo-Control
            (
                proyectos.filter(estado="Monitoreo-Control")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            timezone.now() - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos.filter(estado="Monitoreo-Control").exists()
                else 0
            ),
            # Cierre
            (
                proyectos.filter(estado="Cierre")
                .aggregate(
                    promedio=Avg(
                        ExpressionWrapper(
                            F("fechafin") - F("fechainicio"),
                            output_field=DurationField(),
                        )
                    )
                )["promedio"]
                .days
                if proyectos.filter(estado="Cierre").exists()
                else 0
            ),
        ]
    }
    return render(request, 'gestion_proyectos/index.html', {
        'estadisticas': estadisticas,
        'datos_estado': datos_estado,
        'datos_tendencia': datos_tendencia,
        'datos_tiempo': datos_tiempo,
        'proyectos': proyectos
    })

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
        "estados": ["Inicio", "Planificación", "Ejecución", "Monitoreo-Control", "Cierre"],
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
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    presupuestoutilizado = proyecto.presupuestoutilizado or 0
    presupuesto_restante = proyecto.presupuesto - presupuestoutilizado
    # Calcular desviación de costos
    desviacion_presupuesto = 0
    if proyecto.presupuestoutilizado and proyecto.presupuesto:
        desviacion_presupuesto  = (
            (proyecto.presupuestoutilizado - proyecto.presupuesto) / proyecto.presupuesto
        ) * 100
    
    # Calcular progreso
    total_tareas = tareas.count()
    total_requerimientos = requerimientos.count()
    tareas_completadas = tareas.filter(estado='Completada').count()
    progreso = 100.0 * tareas_completadas / total_tareas if total_tareas > 0 else 0.0

    # Calcular duración estimada y actual
    duracion_estimada = tareas.aggregate(total=Sum('duracionestimada'))['total'] or 0
    duracion_actual = tareas.aggregate(total=Sum('duracionactual'))['total'] or 0

    # Calcular estadísticas de tareas por requerimiento
    for requerimiento in requerimientos:
        requerimiento.tareas_pendientes = tareas.filter(idrequerimiento=requerimiento, estado='Pendiente').count()
        requerimiento.tareas_en_progreso = tareas.filter(idrequerimiento=requerimiento, estado='En Progreso').count()
        requerimiento.tareas_completadas = tareas.filter(idrequerimiento=requerimiento, estado='Completada').count()

    return render(request, 'gestion_proyectos/detalle_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos,
        'tareas': tareas,
        'recursos': recursos,
        'presupuesto_restante': presupuesto_restante,
        'desviacion_presupuesto': desviacion_presupuesto,
        'progreso': progreso,
        'duracion_estimada': duracion_estimada,
        'duracion_actual': duracion_actual,
        'total_tareas': total_tareas,
        'tareas_completadas': tareas_completadas,
        'total_requerimientos': total_requerimientos
    })

@login_required
def crear_proyecto(request):
    if request.method == 'POST':
        # Datos principales del proyecto
        nombreproyecto = request.POST.get('nombreproyecto')
        descripcion = request.POST.get('descripcion')
        estado = request.POST.get('estado')
        fechainicio = request.POST.get('fechainicio')
        fechafin = request.POST.get('fechafin')
        presupuesto = request.POST.get('presupuesto')
        idequipo = request.POST.get('idequipo')

        # Validar que la fecha de inicio sea anterior a la fecha de fin
        if fechainicio >= fechafin:
            equipos = Equipo.objects.all()
            return render(
                request,
                'gestion_proyectos/crear_proyecto.html',
                {
                    'equipos': equipos,
                    'error': 'La fecha de inicio debe ser anterior a la fecha de finalización.',
                    'nombreproyecto': nombreproyecto,
                    'descripcion': descripcion,
                    'estado': estado,
                    'fechainicio': fechainicio,
                    'fechafin': fechafin,
                    'presupuesto': presupuesto,
                    'idequipo': idequipo,
                },
            )

        # Obtener el último ID de proyecto y asignar el siguiente ID disponible
        ultimo_proyecto = Proyecto.objects.order_by('-idproyecto').first()
        nuevo_id_proyecto = (ultimo_proyecto.idproyecto + 1) if ultimo_proyecto else 1

        # Crear el proyecto
        now = timezone.now()
        if is_naive(now):
            now = make_aware(now)
        proyecto = Proyecto(
            idproyecto=nuevo_id_proyecto,
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
            if key.startswith('requerimiento_'):
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    # Obtener el último ID de requerimiento y asignar el siguiente ID disponible
                    ultimo_requerimiento = Requerimiento.objects.order_by(
                        '-idrequerimiento'
                    ).first()
                    nuevo_id_requerimiento = (
                        (ultimo_requerimiento.idrequerimiento + 1)
                        if ultimo_requerimiento
                        else 1
                    )

                    requerimiento = Requerimiento(
                        idrequerimiento=nuevo_id_requerimiento,
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=now,
                        fechamodificacion=now,
                    )
                    requerimiento.save()

        return redirect('gestion_proyectos:lista_proyectos')

    equipos = Equipo.objects.all()
    return render(
        request, 'gestion_proyectos/crear_proyecto.html', {'equipos': equipos}
    )


@login_required
def editar_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()

    if request.method == 'POST':
        proyecto.nombreproyecto = request.POST.get(
            'nombreproyecto', proyecto.nombreproyecto
        )
        proyecto.descripcion = request.POST.get('descripcion', proyecto.descripcion)
        proyecto.estado = request.POST.get('estado', proyecto.estado)
        proyecto.fechainicio = request.POST.get('fechainicio', proyecto.fechainicio)
        proyecto.fechafin = request.POST.get('fechafin', proyecto.fechafin)
        now = timezone.now()
        if is_naive(now):
            now = make_aware(now)
        proyecto.fechamodificacion = now
        proyecto.save()

        # Actualizar requerimientos existentes y agregar nuevos
        for key, value in request.POST.items():
            if key.startswith('requerimiento_'):
                descripcion_requerimiento = value
                req_id = key.split('_')[1]
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    if req_id.isdigit():
                        try:
                            requerimiento = Requerimiento.objects.get(
                                idrequerimiento=req_id
                            )
                            requerimiento.descripcion = descripcion_requerimiento
                            requerimiento.fechamodificacion = now
                            requerimiento.save()
                        except Requerimiento.DoesNotExist:
                            pass
                    else:
                        requerimiento = Requerimiento(
                            descripcion=descripcion_requerimiento,
                            idproyecto=proyecto,
                            fechacreacion=now,
                            fechamodificacion=now,
                        )
                        requerimiento.save()

        # Guardar nuevos requerimientos
        for key, value in request.POST.items():
            if key.startswith('nuevo_requerimiento_'):
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    requerimiento = Requerimiento(
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=now,
                        fechamodificacion=now,
                    )
                    requerimiento.save()

        # Eliminar requerimientos y sus tareas asociadas
        for key in request.POST.getlist('eliminar_requerimiento'):
            requerimiento = Requerimiento.objects.get(idrequerimiento=key)
            Tarea.objects.filter(idrequerimiento=requerimiento).delete()
            requerimiento.delete()

        return redirect('gestion_proyectos:detalle_proyecto', idproyecto=idproyecto)

    return render(
        request,
        'gestion_proyectos/editar_proyecto.html',
        {'proyecto': proyecto, 'requerimientos': requerimientos},
    )


@login_required
def eliminar_requerimiento(request, idrequerimiento):
    if request.method == 'POST':
        try:
            requerimiento = Requerimiento.objects.get(idrequerimiento=idrequerimiento)
            Tarea.objects.filter(idrequerimiento=requerimiento).delete()
            requerimiento.delete()
            return JsonResponse({'success': True})
        except Requerimiento.DoesNotExist:
            return JsonResponse(
                {'success': False, 'error': 'Requerimiento no encontrado.'}
            )
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})

@login_required
def estadisticas_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    presupuestoutilizado = proyecto.presupuestoutilizado or 0
    presupuesto_restante = proyecto.presupuesto - presupuestoutilizado
    return render(request, 'gestion_proyectos/estadisticas_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos,
        'tareas': tareas,
        'recursos': recursos,
        'presupuesto_restante': presupuesto_restante
    })

@login_required
def filtrar_proyectos(request):
    filtro = request.GET.get('filtro', 'todos')
    proyectos = Proyecto.objects.all()

    if filtro == 'inicio':
        proyectos = proyectos.filter(estado='Inicio')
    elif filtro == 'planificacion':
        proyectos = proyectos.filter(estado='Planificación')
    elif filtro == 'ejecucion':
        proyectos = proyectos.filter(estado='Ejecución')
    elif filtro == 'monitoreo_control':
        proyectos = proyectos.filter(estado='Monitoreo-Control')
    elif filtro == 'cierre':
        proyectos = proyectos.filter(estado='Cierre')

    return render(request, 'components/lista_proyectos.html', {'proyectos': proyectos, 'filtro_activo': filtro})




