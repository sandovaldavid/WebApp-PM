from django.urls import path

from dashboard.views import verificar_rol_administrador
from . import views

app_name = "gestionRecursos"
urlpatterns = [
    path("", verificar_rol_administrador(views.lista_recursos), name="lista_recursos"),
    path(
        "crear/", verificar_rol_administrador(views.crear_recurso), name="crear_recurso"
    ),
    path(
        "editar/<int:id>/",
        verificar_rol_administrador(views.editar_recurso),
        name="editar_recurso",
    ),
    path(
        "eliminar/<int:id>/",
        verificar_rol_administrador(views.eliminar_recurso),
        name="eliminar_recurso",
    ),
    path(
        "asignar/",
        verificar_rol_administrador(views.asignar_recurso),
        name="asignar_recurso",
    ),
]
