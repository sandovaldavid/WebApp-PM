from django.urls import path

from dashboard.views import verificar_rol_administrador
from . import views

app_name = "notificaciones"
urlpatterns = [
    path("", verificar_rol_administrador(views.dashboard), name="index"),
    path("notificacion/crear/", views.crear_notificacion, name="crear_notificacion"),
    path("notificacion/ver/<int:id>/", views.ver_notificacion, name="ver_notificacion"),
    path(
        "notificacion/<int:id>/",
        views.detalle_notificacion,
        name="detalle_notificacion",
    ),
    path(
        "notificacion/marcar-leida/<int:id>/", views.marcar_leida, name="marcar_leida"
    ),
    path(
        "notificaciones/marcar-todas-leidas/",
        views.marcar_todas_leidas,
        name="marcar_todas_leidas",
    ),
    path(
        "filtrar-notificaciones/",
        views.filtrar_notificaciones,
        name="filtrar_notificaciones",
    ),
    path(
        "archivar-notificacion/<int:id>/",
        views.archivar_notificacion,
        name="archivar_notificacion",
    ),
    path(
        "notificaciones-archivadas/",
        views.notificaciones_archivadas,
        name="notificaciones_archivadas",
    ),
    path(
        "notificaciones/estadisticas/",
        views.estadisticas_notificaciones,
        name="estadisticas_notificaciones",
    ),
    path(
        "eliminar-notificacion/<int:id>/",
        views.eliminar_notificacion,
        name="eliminar_notificacion",
    ),
    path(
        "notificaciones/estadisticas/",
        views.estadisticas_notificaciones,
        name="estadisticas_notificaciones",
    ),
    path("alertas/", views.lista_alertas, name="lista_alertas"),
    path("alerta/crear/", views.crear_alerta, name="crear_alerta"),
    path("detalle-alerta/<int:id>/", views.detalle_alerta, name="detalle_alerta"),
    path("alerta/resolver/<int:id>/", views.resolver_alerta, name="resolver_alerta"),
    path(
        "estadisticas/alertas/", views.estadisticas_alertas, name="estadisticas_alertas"
    ),
    path("filtrar-alertas/", views.filtrar_alertas, name="filtrar_alertas"),
    path(
        "vista-previa-notificacion/",
        views.vista_previa_notificacion,
        name="vista_previa_notificacion",
    ),
    path("vista-previa-alerta/", views.vista_previa_alerta, name="vista_previa_alerta"),
]
