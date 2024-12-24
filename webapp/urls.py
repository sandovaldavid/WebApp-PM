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
    path('admin/', admin.site.urls),
    path('', include('usuarios.urls')),
    path('dashboard/gestion-equipos/', include('gestion_equipos.urls')),
    path('dashboard/gestion-tareas/', include('gestion_tareas.urls')),
    # path('gestion-proyectos/', include('gestion_proyectos.urls')),
    path('dashboard/gestion-recursos/', include('gestion_recursos.urls')),
    path('dashboard/gestion-usuarios/', include('gestion_usuarios.urls')),
    path('dashboard/integracion/', include('integracion.urls')),
    path('dashboard/notificaciones/', include('notificaciones.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('dashboard/reportes/', include('reporte.urls')),
    # path('redes-neuronales/', include('redes_neuronales.urls')),
    # path('usuarios/', include('usuarios.urls')),
]
