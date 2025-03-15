from django.urls import path

from dashboard.views import verificar_rol_administrador
from . import views
from . import views_configuracion  # Importar las nuevas vistas

app_name = "gestion_tareas"
urlpatterns = [
    path("", verificar_rol_administrador(views.index), name="index"),
    path("crear-tarea/", views.crear_tarea, name="crear_tarea"),
    path(
        "tareas_programadas/", views.tareas_programadas, name="lista_tareas_programadas"
    ),
    path("detalle-tarea/<int:id>/", views.detalle_tarea, name="detalle_tarea"),
    path("editar-tarea/<int:id>/", views.editar_tarea, name="editar_tarea"),
    path(
        "tarea/marcar-completada/<int:id>/",
        views.tarea_marcar_completada,
        name="tarea_marcar_completada",
    ),
    path("ejecutar-tarea/<int:id>/", views.ejecutar_tarea, name="ejecutar_tarea"),
    path("eliminar-tarea/<int:id>/", views.eliminar_tarea, name="eliminar_tarea"),
    path("lista-tareas/", views.lista_tareas, name="lista_tareas"),
    path("panel-tareas/", views.panel_tareas, name="panel_tareas"),
    path("filtrar-tareas/", views.filtrar_tareas, name="filtrar_tareas"),
    path(
        "lista-tareas-programadas/",
        views.lista_tareas_programadas,
        name="tareas_programadas",
    ),
    path(
        "crear-tarea-programada/",
        views.crear_tarea_programada,
        name="crear_tarea_programada",
    ),
    path('estimar-tarea/', views.estimar_tarea, name='estimar_tarea'),
    # Configuración de tareas - Usando las vistas del nuevo archivo
    path(
        'configuracion/',
        views_configuracion.configuracion_tareas,
        name='configuracion_tareas',
    ),
    # Tipos de tarea
    path(
        'configuracion/tipos-tarea/',
        views_configuracion.lista_tipos_tarea,
        name='lista_tipos_tarea',
    ),
    path(
        'configuracion/tipos-tarea/crear/',
        views_configuracion.crear_tipo_tarea,
        name='crear_tipo_tarea',
    ),
    path(
        'configuracion/tipos-tarea/editar/<int:id>/',
        views_configuracion.editar_tipo_tarea,
        name='editar_tipo_tarea',
    ),
    path(
        'configuracion/tipos-tarea/eliminar/<int:id>/',
        views_configuracion.eliminar_tipo_tarea,
        name='eliminar_tipo_tarea',
    ),
    # Fases
    path('configuracion/fases/', views_configuracion.lista_fases, name='lista_fases'),
    path(
        'configuracion/fases/crear/', views_configuracion.crear_fase, name='crear_fase'
    ),
    path(
        'configuracion/fases/editar/<int:id>/',
        views_configuracion.editar_fase,
        name='editar_fase',
    ),
    path(
        'configuracion/fases/eliminar/<int:id>/',
        views_configuracion.eliminar_fase,
        name='eliminar_fase',
    ),
    path(
        'configuracion/fases/actualizar-orden/',
        views_configuracion.actualizar_orden_fases,
        name='actualizar_orden_fases',
    ),
    # Tareas comunes
    path(
        'configuracion/tareas-comunes/',
        views_configuracion.lista_tareas_comunes,
        name='lista_tareas_comunes',
    ),
    path(
        'configuracion/tareas-comunes/crear/',
        views_configuracion.crear_tarea_comun,
        name='crear_tarea_comun',
    ),
    path(
        'configuracion/tareas-comunes/editar/<int:id>/',
        views_configuracion.editar_tarea_comun,
        name='editar_tarea_comun',
    ),
    path(
        'configuracion/tareas-comunes/eliminar/<int:id>/',
        views_configuracion.eliminar_tarea_comun,
        name='eliminar_tarea_comun',
    ),
    # Agregar esta ruta en urlpatterns
    path('api/tareas/<int:id>/', views.api_tarea_por_id, name='api_tarea_por_id'),
]
