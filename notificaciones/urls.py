from django.urls import path
from . import views

app_name = "notificaciones"
urlpatterns = [
    path("", views.dashboard, name="index"),
    path("notificacion/crear/", views.crear_notificacion, name="crear_notificacion"),
    path("alerta/crear/", views.crear_alerta, name="crear_alerta"),
    path(
        "notificacion/<int:id>/",
        views.detalle_notificacion,
        name="detalle_notificacion",
    ),
    path("alerta/<int:id>/", views.detalle_alerta, name="detalle_alerta"),
    path(
        "notificacion/marcar-leida/<int:id>/", views.marcar_leida, name="marcar_leida"
    ),
    path("alerta/resolver/<int:id>/", views.resolver_alerta, name="resolver_alerta"),
]
