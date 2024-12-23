from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from .models import Proyecto, Tarea, Requerimiento
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Case, When, Count, Q, FloatField
from django.db.models.functions import Coalesce
import json

def dashboard(request):
    # Obtiene los primeros 3 proyectos
    proyectos = Proyecto.objects.annotate(
        porcentaje_progreso=Coalesce(
            100.0 * Count(
                Case(
                    When(requerimiento__tarea__estado='Completada', then=1)
                ),
                output_field=FloatField()
            ) / Count('requerimiento__tarea'),
            0.0  # Si no hay tareas, el progreso es 0.0
        )
    )[:3]  # Obtén los primeros 3 proyectos
    print(proyectos)
    tareas_estadisticas = {
        'pendientes': Tarea.objects.filter(estado='Pendiente').count(),
        'en_progreso': Tarea.objects.filter(estado='En Progreso').count(),
        'completadas': Tarea.objects.filter(estado='Completada').count(),
    }
    context = {
        'usuario': request.user,
        'proyectos': proyectos,
        'tareas_estadisticas': json.dumps(tareas_estadisticas, cls=DjangoJSONEncoder),
    }
    return render(request, 'dashboard/index.html', context)

def api_requerimientos(request, proyecto_id):
    requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_id)
    data = list(requerimientos.values('idrequerimiento', 'descripcion'))
    return JsonResponse(data, safe=False)

def api_tareas(request, requerimiento_id):
    tareas = Tarea.objects.filter(idrequerimiento=requerimiento_id)
    data = list(tareas.values('idtarea', 'nombretarea'))
    return JsonResponse(data, safe=False)




