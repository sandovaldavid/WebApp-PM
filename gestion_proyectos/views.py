from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import Proyecto, Requerimiento, Tarea, Equipo
from django.utils import timezone
from django.utils.timezone import is_naive, make_aware
from django.http import JsonResponse

def lista_proyectos(request):
    proyectos = Proyecto.objects.all()
    return render(request, 'gestion_proyectos/lista_proyectos.html', {'proyectos': proyectos})

def detalle_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()
    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
    recursos = proyecto.idequipo.miembro_set.all()
    presupuestoutilizado = proyecto.presupuestoutilizado or 0
    presupuesto_restante = proyecto.presupuesto - presupuestoutilizado
    return render(request, 'gestion_proyectos/detalle_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos,
        'tareas': tareas,
        'recursos': recursos,
        'presupuesto_restante': presupuesto_restante
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
        presupuestoutilizado = request.POST.get('presupuestoutilizado')
        idequipo = request.POST.get('idequipo')

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
            presupuestoutilizado=presupuestoutilizado,
            idequipo_id=idequipo,
            fechacreacion=now,
            fechamodificacion=now
        )
        proyecto.save()

        # Guardar requerimientos asociados
        for key, value in request.POST.items():
            if key.startswith('requerimiento_'):
                descripcion_requerimiento = value
                if descripcion_requerimiento.strip():  # Validar descripción no vacía
                    requerimiento = Requerimiento(
                        descripcion=descripcion_requerimiento,
                        idproyecto=proyecto,
                        fechacreacion=now,
                        fechamodificacion=now
                    )
                    requerimiento.save()

        return redirect('gestion_proyectos:lista_proyectos')

    equipos = Equipo.objects.all()
    return render(request, 'gestion_proyectos/crear_proyecto.html', {'equipos': equipos})

def editar_proyecto(request, idproyecto):
    proyecto = get_object_or_404(Proyecto, idproyecto=idproyecto)
    requerimientos = proyecto.requerimiento_set.all()

    if request.method == 'POST':
        proyecto.nombreproyecto = request.POST.get('nombreproyecto', proyecto.nombreproyecto)
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
                            requerimiento = Requerimiento.objects.get(idrequerimiento=req_id)
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
                            fechamodificacion=now
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
                        fechamodificacion=now
                    )
                    requerimiento.save()

        # Eliminar requerimientos y sus tareas asociadas
        for key in request.POST.getlist('eliminar_requerimiento'):
            requerimiento = Requerimiento.objects.get(idrequerimiento=key)
            Tarea.objects.filter(idrequerimiento=requerimiento).delete()
            requerimiento.delete()

        return redirect('gestion_proyectos:detalle_proyecto', idproyecto=idproyecto)

    return render(request, 'gestion_proyectos/editar_proyecto.html', {
        'proyecto': proyecto,
        'requerimientos': requerimientos
    })

def eliminar_requerimiento(request, idrequerimiento):
    if request.method == 'POST':
        try:
            requerimiento = Requerimiento.objects.get(idrequerimiento=idrequerimiento)
            Tarea.objects.filter(idrequerimiento=requerimiento).delete()
            requerimiento.delete()
            return JsonResponse({'success': True})
        except Requerimiento.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Requerimiento no encontrado.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})




