from django.urls import path

from dashboard.views import verificar_rol_administrador
from . import views

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
]
