import json
import datetime
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import (
    Case,
    When,
    Count,
    FloatField,
    F,
    Sum,
    DecimalField,
    Value,
    Avg,
)
from django.db.models.functions import Coalesce, TruncMonth
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import (
    Proyecto,
    Tarea,
    Requerimiento,
    Desarrollador,
    Tester,
    Administrador,
    Cliente,
    Notificacion,
    Jefeproyecto,
    Alerta,
    Equipo,
    Recurso,
    Tarearecurso,
    Tiporecurso,
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
            Sum(
                'presupuesto',
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            0,
            output_field=DecimalField(max_digits=15, decimal_places=2),
        ),
        presupuesto_utilizado=Coalesce(
            Sum(
                'presupuestoutilizado',
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            0,
            output_field=DecimalField(max_digits=15, decimal_places=2),
        ),
    )

    resumen_financiero['presupuesto_restante'] = (
        resumen_financiero['presupuesto_total']
        - resumen_financiero['presupuesto_utilizado']
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


@login_required
def panel_control(request):
    # Filtros de fecha (por defecto, último mes)
    fecha_fin = datetime.datetime.now().date()
    fecha_inicio = fecha_fin - datetime.timedelta(days=30)
    '''
    if request.GET.get('fecha_inicio') and request.GET.get('fecha_fin'):
        try:
            fecha_inicio = datetime.datetime.strptime(request.GET.get('fecha_inicio'), '%Y-%m-%d').date()
            fecha_fin = datetime.datetime.strptime(request.GET.get('fecha_fin'), '%Y-%m-%d').date()
        except ValueError:
            pass
    
    # Agregar un día más a fecha_fin para incluir ese día completo en las consultas
    fecha_fin_consulta = fecha_fin + datetime.timedelta(days=1)
    '''
    # Filtro de equipo
    equipo_id = request.GET.get('equipo', None)

    # Obtener todos los equipos para el filtro
    equipos = Equipo.objects.all()

    # Estadísticas generales
    # Corregir el cálculo del porcentaje de presupuesto utilizado usando tipos consistentes
    presupuestos = Proyecto.objects.aggregate(
        utilizado=Coalesce(
            Sum(
                'presupuestoutilizado',
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            Value(
                Decimal('0'), output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
        ),
        total=Coalesce(
            Sum(
                'presupuesto',
                output_field=DecimalField(max_digits=15, decimal_places=2),
            ),
            Value(
                Decimal('1'), output_field=DecimalField(max_digits=15, decimal_places=2)
            ),
        ),
    )

    presupuesto_utilizado = float(presupuestos['utilizado'])
    presupuesto_total = float(presupuestos['total'])

    # Evitar división por cero
    if presupuesto_total > 0:
        porcentaje_utilizado = int((presupuesto_utilizado / presupuesto_total) * 100)
    else:
        porcentaje_utilizado = 0

    # Obtener el primer día del mes actual y del mes anterior
    hoy = timezone.now().date()
    primer_dia_mes_actual = timezone.make_aware(
        datetime.datetime(hoy.year, hoy.month, 1)
    )

    # Calcular el primer día del mes anterior
    if hoy.month == 1:  # Si estamos en enero
        primer_dia_mes_anterior = timezone.make_aware(
            datetime.datetime(hoy.year - 1, 12, 1)
        )
    else:
        primer_dia_mes_anterior = timezone.make_aware(
            datetime.datetime(hoy.year, hoy.month - 1, 1)
        )

    # Calcular el primer día del mes siguiente
    if hoy.month == 12:  # Si estamos en diciembre
        primer_dia_mes_siguiente = timezone.make_aware(
            datetime.datetime(hoy.year + 1, 1, 1)
        )
    else:
        primer_dia_mes_siguiente = timezone.make_aware(
            datetime.datetime(hoy.year, hoy.month + 1, 1)
        )

    # Contar proyectos nuevos en el mes actual y anterior
    proyectos_mes_actual = Proyecto.objects.filter(
        fechacreacion__gte=primer_dia_mes_actual,
        fechacreacion__lt=primer_dia_mes_siguiente,
    ).count()

    proyectos_mes_anterior = Proyecto.objects.filter(
        fechacreacion__gte=primer_dia_mes_anterior,
        fechacreacion__lt=primer_dia_mes_actual,
    ).count()

    # Calcular la tendencia (diferencia entre este mes y el anterior)
    proyectos_tendencia = proyectos_mes_actual - proyectos_mes_anterior

    stats = {
        'proyectos_activos': Proyecto.objects.filter(estado='Ejecución').count(),
        'proyectos_tendencia': proyectos_tendencia,
        'tareas_pendientes': Tarea.objects.filter(estado='Pendiente').count(),
        'tareas_vencidas': Tarea.objects.filter(
            fechafin__lt=datetime.date.today(), estado__in=['Pendiente', 'En Progreso']
        ).count(),
        'presupuesto_utilizado_porcentaje': porcentaje_utilizado,
        'total_equipos': Equipo.objects.count(),
        'total_recursos': Recurso.objects.count(),
    }

    # Proyectos con información de progreso y estado
    proyectos_query = Proyecto.objects.annotate(
        total_tareas=Count('requerimiento__tarea'),
        tareas_completadas=Count(
            Case(When(requerimiento__tarea__estado='Completada', then=1)),
            output_field=FloatField(),
        ),
        porcentaje_progreso=Coalesce(
            Case(
                When(total_tareas=0, then=0.0),
                default=100.0 * F('tareas_completadas') / F('total_tareas'),
                output_field=FloatField(),
            ),
            0.0,
        ),
    )

    if equipo_id:
        proyectos_query = proyectos_query.filter(idequipo=equipo_id)

    proyectos = proyectos_query.order_by('-fechacreacion')[:10]

    # Proyectos por equipo (para el gráfico)
    equipos_list = Equipo.objects.all()
    equipos_nombres = []
    proyectos_por_estado = {
        'Inicio': [],
        'Planificación': [],
        'Ejecución': [],
        'Monitoreo-Control': [],
        'Cierre': [],
    }

    # Obtener todos los equipos y contar sus proyectos por estado
    for equipo in equipos_list:
        equipos_nombres.append(equipo.nombreequipo)

        # Contar proyectos por estado para este equipo
        for estado in proyectos_por_estado.keys():
            count = Proyecto.objects.filter(
                idequipo=equipo.idequipo, estado=estado
            ).count()
            proyectos_por_estado[estado].append(count)

    # Definir colores para cada estado
    estados_colores = {
        'Inicio': 'rgba(255, 206, 86, 0.8)',  # Amarillo
        'Planificación': 'rgba(54, 162, 235, 0.8)',  # Azul
        'Ejecución': 'rgba(75, 192, 192, 0.8)',  # Verde claro
        'Monitoreo-Control': 'rgba(153, 102, 255, 0.8)',  # Púrpura
        'Cierre': 'rgba(255, 99, 132, 0.8)',  # Rojo
    }

    # Construir estructura para Chart.js
    proyectos_equipo_datos = {'labels': equipos_nombres, 'datasets': []}

    # Crear dataset para cada estado
    for estado, datos in proyectos_por_estado.items():
        dataset = {
            'label': f'Proyectos en {estado}',
            'data': datos,
            'backgroundColor': estados_colores.get(estado),
        }
        proyectos_equipo_datos['datasets'].append(dataset)

    # Proyectos con información financiera
    proyectos_presupuesto = Proyecto.objects.annotate(
        porcentaje_presupuesto=Case(
            When(presupuesto=0, then=0),
            default=100 * F('presupuestoutilizado') / F('presupuesto'),
            output_field=FloatField(),
        ),
        presupuesto_restante=F('presupuesto') - F('presupuestoutilizado'),
    ).order_by('-porcentaje_presupuesto')[:10]

    # Tareas recientes
    tareas = (
        Tarea.objects.select_related('idrequerimiento__idproyecto')
        .annotate(proyecto_nombre=F('idrequerimiento__idproyecto__nombreproyecto'))
        .order_by('-fechamodificacion')[:15]
    )

    # Datos para el gráfico de tareas completadas por mes (últimos 12 meses)
    doce_meses_atras = hoy - datetime.timedelta(days=365)

    # Obtener las tareas completadas agrupadas por mes
    tareas_completadas_mes = (
        Tarea.objects.filter(
            estado='Completada', fechamodificacion__gte=doce_meses_atras
        )
        .annotate(mes=TruncMonth('fechamodificacion'))
        .values('mes')
        .annotate(total=Count('idtarea'))
        .order_by('mes')
    )

    # Crear un diccionario que mapee cada mes a su total de tareas completadas
    meses_completados = {
        item['mes'].strftime('%m'): item['total'] for item in tareas_completadas_mes
    }

    # Definir nombres de meses y preparar datos para el gráfico
    nombres_meses = [
        'Ene',
        'Feb',
        'Mar',
        'Abr',
        'May',
        'Jun',
        'Jul',
        'Ago',
        'Sep',
        'Oct',
        'Nov',
        'Dic',
    ]
    datos_tareas_completadas = []

    # Llenar el array con datos para cada mes
    for i in range(1, 13):
        mes_str = f"{i:02d}"  # Formato de dos dígitos: 01, 02, ..., 12
        datos_tareas_completadas.append(meses_completados.get(mes_str, 0))

    # Recursos con carga de trabajo
    recursos = Recurso.objects.annotate(
        total_tareas=Count('tarearecurso'),
        carga_trabajo_porcentaje=Case(
            When(disponibilidad=False, then=100),
            default=Coalesce(F('carga_trabajo') * 100, 0),
            output_field=FloatField(),
        ),
    ).order_by('-carga_trabajo_porcentaje')[:10]

    # Distribución de usuarios por tipo
    usuarios_por_tipo = {
        'Desarrolladores': Desarrollador.objects.count(),
        'Testers': Tester.objects.count(),
        'Administradores': Administrador.objects.count(),
        'Clientes': Cliente.objects.count(),
        'Jefes de proyecto': Jefeproyecto.objects.count(),
    }

    # Notificaciones recientes
    notificaciones = Notificacion.objects.order_by('-fechacreacion')[:8]

    # Alertas activas
    alertas = Alerta.objects.filter(activa=True).order_by('-fechacreacion')[:8]

    # Datos para gráficos
    # Estado de proyectos
    estado_proyectos = {}
    for estado in [
        'Inicio',
        'Planificación',
        'Ejecución',
        'Monitoreo-Control',
        'Cierre',
    ]:
        estado_proyectos[estado] = Proyecto.objects.filter(estado=estado).count()

    # Estado de tareas
    estado_tareas = {}
    for estado in ['Pendiente', 'En Progreso', 'Completada', 'Atrasada', 'Bloqueada']:
        estado_tareas[estado] = Tarea.objects.filter(estado=estado).count()

    # Prioridad de tareas
    prioridad_tareas = {}
    for prioridad in range(1, 4):  # Asumiendo prioridades 1-5
        prioridad_tareas[f'Prioridad {prioridad}'] = Tarea.objects.filter(
            prioridad=prioridad
        ).count()

    # Rendimiento de equipos (con datos reales)
    equipos_rendimiento_datos = {
        'labels': [
            'Efectividad',
            'Puntualidad',
            'Calidad',
            'Productividad',
            'Colaboración',
        ],
        'datasets': [],
    }

    # Obtener hasta 5 equipos con más miembros
    equipos_con_rendimiento = Equipo.objects.annotate(
        num_miembros=Count('miembro')
    ).order_by('-num_miembros')[:5]

    # Para cada equipo, calcular sus métricas de rendimiento
    for i, equipo in enumerate(equipos_con_rendimiento):
        # Proyectos del equipo
        proyectos_equipo = Proyecto.objects.filter(idequipo=equipo.idequipo)

        # Si no hay proyectos, usar valores promedio genéricos
        if not proyectos_equipo.exists():
            continue

        # Tareas relacionadas con proyectos de este equipo
        tareas_equipo = Tarea.objects.filter(
            idrequerimiento__idproyecto__in=proyectos_equipo
        )

        # 1. Efectividad: Porcentaje de tareas_equipo completadas
        if tareas_equipo.count() > 0:
            efectividad = min(
                int(
                    (
                        tareas_equipo.filter(estado='Completada').count()
                        / tareas_equipo.count()
                    )
                    * 100
                ),
                100,
            )
        else:
            efectividad = 0

        # 2. Puntualidad: Tareas_equipo entregadas a tiempo vs atrasadas
        tareas_equipo_completadas = tareas_equipo.filter(estado='Completada')
        if tareas_equipo_completadas.count() > 0:
            tareas_equipo_a_tiempo = tareas_equipo_completadas.filter(
                fechamodificacion__lte=F('fechafin')
            ).count()
            puntualidad = min(
                int((tareas_equipo_a_tiempo / tareas_equipo_completadas.count()) * 100),
                100,
            )
        else:
            puntualidad = 0

        # 3. Calidad: Inverse de tareas_equipo bloqueadas/con problemas
        if tareas_equipo.count() > 0:
            problemas = tareas_equipo.filter(
                estado__in=['Bloqueada', 'Atrasada']
            ).count()
            calidad = max(
                min(
                    int(
                        ((tareas_equipo.count() - problemas) / tareas_equipo.count())
                        * 100
                    ),
                    100,
                ),
                0,
            )
        else:
            calidad = 0

        # 4. Productividad: Basado en duración estimada vs actual
        tareas_equipo_con_duracion = tareas_equipo.exclude(
            duracionestimada=None
        ).exclude(duracionactual=None)
        if tareas_equipo_con_duracion.count() > 0:
            # Si duracionactual es menor que duracionestimada, se considera más productivo
            productividad_total = 0
            for t in tareas_equipo_con_duracion:
                if t.duracionactual > 0:
                    ratio = min((t.duracionestimada / t.duracionactual), 1)  # Máx 100%
                    productividad_total += ratio * 100

            productividad = int(
                productividad_total / tareas_equipo_con_duracion.count()
            )
        else:
            productividad = 0

        # 5. Colaboración: Basado en número de recursos por tarea
        recursos_por_tarea = (
            Tarearecurso.objects.filter(idtarea__in=tareas_equipo)
            .values('idtarea')
            .annotate(num_recursos=Count('idrecurso'))
            .aggregate(
                promedio=Coalesce(Avg('num_recursos'), 0, output_field=FloatField())
            )['promedio']
        )

        # Convertimos a escala 0-100, donde 3 recursos es óptimo (100%)
        if recursos_por_tarea > 0:
            colaboracion = min(int(100 - abs(3 - recursos_por_tarea) * 15), 100)
        else:
            colaboracion = 0

        # Colores para cada equipo
        colores_bg = [
            'rgba(59, 130, 246, 0.2)',  # Azul
            'rgba(16, 185, 129, 0.2)',  # Verde
            'rgba(245, 158, 11, 0.2)',  # Amarillo
            'rgba(139, 92, 246, 0.2)',  # Morado
            'rgba(236, 72, 153, 0.2)',  # Rosa
        ]

        colores_borde = [
            '#3b82f6',  # Azul
            '#10b981',  # Verde
            '#f59e0b',  # Amarillo
            '#8b5cf6',  # Morado
            '#ec4899',  # Rosa
        ]

        # Crear dataset para este equipo
        dataset = {
            'label': equipo.nombreequipo,
            'data': [efectividad, puntualidad, calidad, productividad, colaboracion],
            'backgroundColor': colores_bg[i % len(colores_bg)],
            'borderColor': colores_borde[i % len(colores_borde)],
            'borderWidth': 2,
            'pointBackgroundColor': colores_borde[i % len(colores_borde)],
        }
        equipos_rendimiento_datos['datasets'].append(dataset)

        # Datos para el gráfico de presupuesto global
        presupuesto_global_datos = [porcentaje_utilizado, 100 - porcentaje_utilizado]

        # Gastos por tipo de recurso
        gastos_categorias = {}

        # Consulta para obtener los tipos de recursos
        tipos_recurso = Tiporecurso.objects.all()

        for tipo in tipos_recurso:
            # Obtener todos los recursos de este tipo
            recursos_tipo = Recurso.objects.filter(idtiporecurso=tipo.idtiporecurso)

            # Obtener las tareas asociadas a estos recursos
            tareas_ids = Tarearecurso.objects.filter(
                idrecurso__in=recursos_tipo
            ).values_list('idtarea', flat=True)

            # Sumar los costos actuales de estas tareas
            gasto_total = Tarea.objects.filter(idtarea__in=tareas_ids).aggregate(
                total=Coalesce(
                    Sum('costoactual'),
                    Value(
                        0, output_field=DecimalField(max_digits=15, decimal_places=2)
                    ),
                )
            )['total']

            # Si no hay gastos reales, usar los estimados
            if gasto_total == 0:
                gasto_total = Tarea.objects.filter(idtarea__in=tareas_ids).aggregate(
                    total=Coalesce(
                        Sum('costoestimado'),
                        Value(
                            0,
                            output_field=DecimalField(max_digits=15, decimal_places=2),
                        ),
                    )
                )['total']

            # Solo añadir tipos con gastos mayores a cero
            if gasto_total > 0:
                gastos_categorias[tipo.nametiporecurso] = float(gasto_total)

    # Tendencia de gastos mensuales (últimos 12 meses)
    doce_meses_atras = hoy - datetime.timedelta(days=365)

    # Obtener gastos por mes (costos actuales de tareas)
    gastos_mensuales = (
        Tarea.objects.filter(fechamodificacion__gte=doce_meses_atras)
        .annotate(mes=TruncMonth('fechamodificacion'))
        .values('mes')
        .annotate(
            total_actual=Coalesce(
                Sum(
                    'costoactual',
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
            total_estimado=Coalesce(
                Sum(
                    'costoestimado',
                    output_field=DecimalField(max_digits=15, decimal_places=2),
                ),
                Value(0, output_field=DecimalField(max_digits=15, decimal_places=2)),
            ),
        )
        .order_by('mes')
    )

    # Crear dos diccionarios que mapeen cada mes a sus costos
    meses_gastos_actuales = {
        item['mes'].strftime('%m'): float(item['total_actual'])
        for item in gastos_mensuales
    }
    meses_gastos_estimados = {
        item['mes'].strftime('%m'): float(item['total_estimado'])
        for item in gastos_mensuales
    }

    # Preparar datos para el gráfico
    datos_gastos_actuales = []
    datos_gastos_estimados = []

    # Llenar los arrays con datos para cada mes
    for i in range(1, 13):
        mes_str = f"{i:02d}"  # Formato de dos dígitos: 01, 02, ..., 12
        datos_gastos_actuales.append(meses_gastos_actuales.get(mes_str, 0))
        datos_gastos_estimados.append(meses_gastos_estimados.get(mes_str, 0))

    # Contexto para la plantilla
    context = {
        'usuario': request.user,
        'stats': stats,
        'proyectos': proyectos,
        'tareas': tareas,
        'recursos': recursos,
        'notificaciones': notificaciones,
        'alertas': alertas,
        'equipos': equipos,
        'proyectos_equipo_datos': json.dumps(proyectos_equipo_datos),
        'tareas_completadas_data': json.dumps(datos_tareas_completadas),
        'usuarios_por_tipo': json.dumps(usuarios_por_tipo),
        'equipos_rendimiento_datos': json.dumps(equipos_rendimiento_datos),
        'presupuesto_global_datos': json.dumps(presupuesto_global_datos),
        'gastos_por_categoria': json.dumps(gastos_categorias),
        'gastos_mensuales_actuales': json.dumps(datos_gastos_actuales),
        'gastos_mensuales_estimados': json.dumps(datos_gastos_estimados),
        'proyectos_presupuesto': proyectos_presupuesto,
        'estado_proyectos': json.dumps(estado_proyectos),
        'estado_tareas': json.dumps(estado_tareas),
        'prioridad_tareas': json.dumps(prioridad_tareas),
        #'filtro_activo': True,
        #'fecha_inicio_str': fecha_inicio.strftime('%d/%m/%Y'),
        #'fecha_fin_str': fecha_fin.strftime('%d/%m/%Y'),
    }

    return render(request, 'dashboard/panel_control.html', context)
