import json

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Case, When, Count, FloatField, F, Sum, DecimalField
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.shortcuts import render, redirect

from .models import (
    Proyecto,
    Tarea,
    Requerimiento,
    Desarrollador,
    Tester,
    Administrador,
    Cliente,
    Notificacion,
    Alerta,
    Equipo,
)


def verificar_rol_administrador(view_func):
    def wrapper(request, *args, **kwargs):
        if request.session.get("usuario_rol") != "Administrador":
            return redirect("usuarios:login")
        return view_func(request, *args, **kwargs)

    return wrapper


@login_required
def dashboard(request):
    # Obtiene los últimos 3 proyectos agregados
    proyectos = Proyecto.objects.annotate(
        total_tareas=Count("requerimiento__tarea"),
        tareas_completadas=Count(
            Case(When(requerimiento__tarea__estado="Completada", then=1)),
            output_field=FloatField(),
        ),
        porcentaje_progreso=Coalesce(
            Case(
                When(total_tareas=0, then=0.0),
                default=100.0 * F("tareas_completadas") / F("total_tareas"),
                output_field=FloatField(),
            ),
            0.0,  # Si no hay tareas, el progreso es 0.0
        ),
    ).order_by("-fechacreacion")[
        :6
    ]  # Ordenar por fecha de creación descendente y obtener los primeros 3 proyectos

    tareas_estadisticas = {
        "pendientes": Tarea.objects.filter(estado="Pendiente").count(),
        "en_progreso": Tarea.objects.filter(estado="En Progreso").count(),
        "completadas": Tarea.objects.filter(estado="Completada").count(),
    }

    # Calcular resumen financiero
    resumen_financiero = Proyecto.objects.aggregate(
        presupuesto_total=Coalesce(
            Sum('presupuesto', output_field=DecimalField(max_digits=15, decimal_places=2)),
            0,
            output_field=DecimalField(max_digits=15, decimal_places=2)
        ),
        presupuesto_utilizado=Coalesce(
            Sum('presupuestoutilizado', output_field=DecimalField(max_digits=15, decimal_places=2)),
            0,
            output_field=DecimalField(max_digits=15, decimal_places=2)
        )
    )

    resumen_financiero['presupuesto_restante'] = (
        resumen_financiero['presupuesto_total'] - 
        resumen_financiero['presupuesto_utilizado']
    )

    # Calcular distribución de recursos
    distribucion_recursos = {
        "desarrolladores": Desarrollador.objects.count(),
        "testers": Tester.objects.count(),
        "administradores": Administrador.objects.count(),
        "clientes": Cliente.objects.count(),
    }

    # Obtener notificaciones recientes
    notificaciones = Notificacion.objects.filter(leido=False).order_by(
        "-fechacreacion"
    )[:5]

    # Obtener alertas activas
    alertas = Alerta.objects.filter(activa=True).order_by("-fechacreacion")[:5]

    # Calcular estadísticas de usuarios
    usuarios_estadisticas = {
        "administradores": Administrador.objects.count(),
        "desarrolladores": Desarrollador.objects.count(),
        "testers": Tester.objects.count(),
        "clientes": Cliente.objects.count(),
    }

    # Calcular proyectos por equipo
    equipos_proyectos = Equipo.objects.annotate(
        total_proyectos=Count("proyecto")
    ).values("nombreequipo", "total_proyectos")

    equipos_proyectos_estadisticas = {
        "labels": [equipo["nombreequipo"] for equipo in equipos_proyectos],
        "data": [equipo["total_proyectos"] for equipo in equipos_proyectos],
    }

    context = {
        "usuario": request.user,
        "proyectos": proyectos,
        "tareas_estadisticas": json.dumps(tareas_estadisticas, cls=DjangoJSONEncoder),
        "resumen_financiero": resumen_financiero,
        "recursos_estadisticas": json.dumps(
            distribucion_recursos, cls=DjangoJSONEncoder
        ),
        "notificaciones": notificaciones,
        "alertas": alertas,
        "usuarios_estadisticas": json.dumps(
            usuarios_estadisticas, cls=DjangoJSONEncoder
        ),
        "equipos_proyectos_estadisticas": json.dumps(
            equipos_proyectos_estadisticas, cls=DjangoJSONEncoder
        ),
    }
    return render(request, "dashboard/index.html", context)


@login_required
def api_requerimientos(request, proyecto_id):
    requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_id)
    data = list(requerimientos.values("idrequerimiento", "descripcion"))
    return JsonResponse(data, safe=False)


@login_required
def api_tareas(request, requerimiento_id):
    tareas = Tarea.objects.filter(idrequerimiento=requerimiento_id)
    data = list(tareas.values("idtarea", "nombretarea"))
    return JsonResponse(data, safe=False)
