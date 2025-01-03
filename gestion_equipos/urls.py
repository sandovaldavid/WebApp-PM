from django.urls import path
from . import views

app_name = "gestion_equipos"
urlpatterns = [
    path("", views.index, name="index"),
    path(
        "<int:equipo_id>/miembros/", views.gestionar_miembros, name="gestionar_miembros"
    ),
    path(
        "equipo/<int:equipo_id>/miembros/", views.lista_miembros, name="lista_miembros"
    ),
    path("crear/equipo/", views.crear_equipo, name="crear_equipo"),
    path("editar/<int:equipo_id>/equipo/", views.editar_equipo, name="editar_equipo"),
    path(
        "eliminar/<int:equipo_id>/equipo/",
        views.eliminar_equipo,
        name="eliminar_equipo",
    ),
    path("lista-equipo/", views.lista_equipos, name="lista_equipos"),
    path(
        "detalle-equipo/<int:equipo_id>/", views.detalle_equipo, name="detalle_equipo"
    ),
    path(
        "equipo/<int:equipo_id>/agregar-miembro/",
        views.agregar_miembro,
        name="agregar_miembro",
    ),
    path(
        "equipo/<int:equipo_id>/crear-miembro/",
        views.crear_miembro,
        name="crear_miembro",
    ),
    path(
        "equipo/miembro/<int:miembro_id>/eliminar/",
        views.eliminar_miembro,
        name="eliminar_miembro",
    ),
    path("miembro/<int:miembro_id>/", views.detalle_miembro, name="detalle_miembro"),
]
