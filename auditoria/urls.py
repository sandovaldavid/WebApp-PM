from django.urls import path
from . import views
from dashboard.views import verificar_rol_administrador

app_name = 'auditoria'
urlpatterns = [
    path('registro-actividades/', verificar_rol_administrador(views.registro_actividades), name='registro_actividades'),
    path('intentos-acceso/', views.intentos_acceso, name='intentos_acceso'),
    path('gestion-roles/', views.gestion_roles, name='gestion_roles'),
]
