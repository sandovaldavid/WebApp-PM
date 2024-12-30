from django.urls import path
from . import views

app_name = 'auditoria'
urlpatterns = [
    path('registro-actividades/', views.registro_actividades, name='registro_actividades'),
    path('intentos-acceso/', views.intentos_acceso, name='intentos_acceso'),
    path('gestion-roles/', views.gestion_roles, name='gestion_roles'),
]
