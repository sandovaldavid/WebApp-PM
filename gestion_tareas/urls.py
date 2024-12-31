from django.urls import path
from . import views

app_name = "gestion_tareas"
urlpatterns = [
    path("", views.index, name="index"),
    path("crear-tarea/", views.crear_tarea, name="crear_tarea"),
    path("tareas_programadas/", views.tareas_programadas, name="tareas_programadas"),
    path("detalle-tarea/<int:id>/", views.detalle_tarea, name="detalle_tarea"),
    path("editar-tarea/<int:id>/", views.editar_tarea, name="editar_tarea"),
]
