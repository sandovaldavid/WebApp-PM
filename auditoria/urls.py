from django.urls import path

from dashboard.views import verificar_rol_administrador
from . import views

app_name = 'auditoria'
urlpatterns = [
    path(
        'registro-actividades/',
        verificar_rol_administrador(views.registro_actividades),
        name='registro_actividades',
    ),
    path('intentos-acceso/', views.intentos_acceso, name='intentos_acceso'),
    path('gestion-roles/', views.gestion_roles, name='gestion_roles'),
    path('crear-actividad/', views.crear_actividad, name='crear_actividad'),
    path('editar-actividad/<int:id>/', views.editar_actividad, name='editar_actividad'),
    path(
        'eliminar-actividad/<int:id>/',
        views.eliminar_actividad,
        name='eliminar_actividad',
    ),
]
