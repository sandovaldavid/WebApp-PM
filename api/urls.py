from django.urls import path, include
from rest_framework import routers
from .views import proyecto_views, usuario_views

router = routers.DefaultRouter()
router.register(r"usuarios", usuario_views.UsuarioViewSet)
router.register(r"proyectos", proyecto_views.ProyectoViewSet)
# Añade más viewsets según necesites

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls", namespace="rest_framework")),
]
