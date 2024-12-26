from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import Proyecto, Requerimiento, Tarea, Equipo
# from gestion_tareas.models import Tarea
from django.utils import timezone

def lista_proyectos(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'gestion_proyectos/lista_proyectos.html', {'proyectos': proyectos})

def detalle_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    return render(request, 'gestion_proyectos/detalle_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos,
        'tareas': tareas,
        'recursos': recursos
    })

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

        # Crear el proyecto
        proyecto = Proyecto(
            nombreproyecto=nombreproyecto,
            descripcion=descripcion,
            estado=estado,
            fechainicio=fechainicio,
            fechafin=fechafin,
            presupuesto=presupuesto,
            idequipo_id=idequipo,
            fechacreacion=timezone.now(),
            fechamodificacion=timezone.now()
        )
        proyecto.save()

        # Guardar requerimientos asociados
        for key, value in request.POST.items():
            if key.startswith('requerimiento_'):
                print(f"Guardando req {key}: {value}")
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    requerimiento = Requerimiento(
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=timezone.now(),
                        fechamodificacion=timezone.now()
                    )
                    requerimiento.save()

                    # Guardar tareas asociadas al requerimiento
                    for tarea_key, tarea_value in request.POST.items():
                        print(f"Guardando tarea {tarea_key}: {tarea_value}")
                        if tarea_key.startswith(f'tarea_{key}_'):
                            print(f"Guardando corectamente {tarea_key}: {tarea_value}")
                            # Obtener el índice desde la clave
                            index = tarea_key.split('_')[3]
                            if tarea_key.startswith(f'tarea_{key}_{index}_nombre'):
                                nombretarea = request.POST.get(f'tarea_{key}_{index}_nombre')
                                estado_tarea = request.POST.get(f'tarea_{key}_{index}_estado')
                                prioridad = request.POST.get(f'tarea_{key}_{index}_prioridad')
                                duracionestimada = request.POST.get(f'tarea_{key}_{index}_duracionestimada')
                                if nombretarea and estado_tarea and prioridad and duracionestimada:
                                    tarea = Tarea(
                                        idrequerimiento=requerimiento,
                                        nombretarea=nombretarea,
                                        estado=estado_tarea,
                                        prioridad=prioridad,
                                        duracionestimada=duracionestimada,
                                        fechacreacion=timezone.now(),
                                        fechamodificacion=timezone.now()
                                    )
                                    tarea.save()

        # Eliminar requerimientos
        for key in request.POST.getlist('eliminar_requerimiento'):
            Requerimiento.objects.filter(idrequerimiento=key).delete()

        return redirect('gestion_proyectos:lista_proyectos')

    equipos = Equipo.objects.all()
    return render(request, 'gestion_proyectos/crear_proyecto.html', {'equipos': equipos})

def editar_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)

    if request.method == 'POST':
        proyecto.nombreproyecto = request.POST.get('nombreproyecto', proyecto.nombreproyecto)
        proyecto.descripcion = request.POST.get('descripcion', proyecto.descripcion)
        proyecto.estado = request.POST.get('estado', proyecto.estado)
        proyecto.fechainicio = request.POST.get('fechainicio', proyecto.fechainicio)
        proyecto.fechafin = request.POST.get('fechafin', proyecto.fechafin)
        proyecto.presupuesto = request.POST.get('presupuesto', proyecto.presupuesto)
        proyecto.fechamodificacion = timezone.now()
        proyecto.save()

        # Actualizar requerimientos existentes y agregar nuevos
        for key, value in request.POST.items():
            if key.startswith('requerimiento_'):
                descripcion_requerimiento = value
                req_id = key.split('_')[1]
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    if req_id.isdigit():
                        requerimiento = Requerimiento.objects.get(idrequerimiento=req_id)
                        requerimiento.descripcion = descripcion_requerimiento
                        requerimiento.fechamodificacion = timezone.now()
                        requerimiento.save()
                    else:
                        requerimiento = Requerimiento(
                            descripcion=descripcion_requerimiento,
                            idproyecto=proyecto,
                            fechacreacion=timezone.now(),
                            fechamodificacion=timezone.now()
                        )
                        requerimiento.save()

                    # Actualizar tareas existentes y agregar nuevas
                    for tarea_key, tarea_value in request.POST.items():
                        if tarea_key.startswith(f'tarea_{key}_'):
                            index = tarea_key.split('_')[3]
                            if tarea_key.startswith(f'tarea_{key}_{index}_nombre'):
                                nombretarea = request.POST.get(f'tarea_{key}_{index}_nombre')
                                estado_tarea = request.POST.get(f'tarea_{key}_{index}_estado')
                                prioridad = request.POST.get(f'tarea_{key}_{index}_prioridad')
                                duracionestimada = request.POST.get(f'tarea_{key}_{index}_duracionestimada')
                                if nombretarea and estado_tarea and prioridad and duracionestimada:
                                    tarea_id = tarea_key.split('_')[2]
                                    if tarea_id.isdigit():
                                        tarea = Tarea.objects.get(idtarea=tarea_id)
                                        tarea.nombretarea = nombretarea
                                        tarea.estado = estado_tarea
                                        tarea.prioridad = prioridad
                                        tarea.duracionestimada = duracionestimada
                                        tarea.fechamodificacion = timezone.now()
                                        tarea.save()
                                    else:
                                        tarea = Tarea(
                                            idrequerimiento=requerimiento,
                                            nombretarea=nombretarea,
                                            estado=estado_tarea,
                                            prioridad=prioridad,
                                            duracionestimada=duracionestimada,
                                            fechacreacion=timezone.now(),
                                            fechamodificacion=timezone.now()
                                        )
                                        tarea.save()

        return redirect('gestion_proyectos:detalle_proyecto', idproyecto=idproyecto)

    return render(request, 'gestion_proyectos/editar_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos,
        'tareas': tareas
    })




