from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.views import (
    usuario_views,
    proyecto_views,
    tarea_views,
    equipo_views,
    requerimiento_views,
    recurso_views,
)
from api.views.auth_views import LoginView
from api.views.health_views import health_check
from rest_framework.authtoken import views as token_views

# Create a router and register our viewsets with it
router = DefaultRouter()
router.register(r"usuarios", usuario_views.UsuarioViewSet)
router.register(r"proyectos", proyecto_views.ProyectoViewSet)
router.register(r"tareas", tarea_views.TareaViewSet)
router.register(r"equipos", equipo_views.EquipoViewSet)
router.register(r"requerimientos", requerimiento_views.RequerimientoViewSet)
router.register(r"recursos", recurso_views.RecursoViewSet)

# The API URLs are determined automatically by the router
urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),
    path("login/", LoginView.as_view(), name="api-login"),
    path("token-auth/", token_views.obtain_auth_token, name="api-token-auth"),
    path("health/", health_check, name="api-health-check"),
]
