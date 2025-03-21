from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.dashboard, name="index"),
    path("panel-control/", views.panel_control, name="panel_control"),
    path(
        "api/requerimientos/<int:proyecto_id>/",
        views.api_requerimientos,
        name="api_requerimientos",
    ),
    path("api/tareas/<int:requerimiento_id>/", views.api_tareas, name="api_tareas"),
]
