"""
URL configuration for webapp project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("gestion-equipos/", include("gestion_equipos.urls")),
    path("gestion-tareas/", include("gestion_tareas.urls")),
    path("gestion-proyectos/", include("gestion_proyectos.urls")),
    path("gestion-recursos/", include("gestion_recursos.urls")),
    path("gestion-usuarios/", include("gestion_usuarios.urls")),
    path("integracion/", include("integracion.urls")),
    path("gestion-notificaciones/", include("notificaciones.urls")),
    path("dashboard/", include("dashboard.urls")),
    path("gestion-reportes/", include("reporte.urls")),
    path("gestion-auditoria/", include("auditoria.urls")),
    path("", include("usuarios.urls")),
    path("redes-neuronales/", include("redes_neuronales.urls")),
    path("api/v1/", include("api.urls")),
]
