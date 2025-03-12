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
    # Nueva ruta para filtrado HTMX
    path('filtrar-actividades/', views.filtrar_actividades, name='filtrar_actividades'),
    # API para paginación AJAX
    path('lista-actividades/', views.lista_actividades, name='lista_actividades'),
    path('intentos-acceso/', views.intentos_acceso, name='intentos_acceso'),
    path('gestion-roles/', views.gestion_roles, name='gestion_roles'),
    path('crear-actividad/', views.crear_actividad, name='crear_actividad'),
    path('editar-actividad/<int:id>/', views.editar_actividad, name='editar_actividad'),
    path(
        'eliminar-actividad/<int:id>/',
        views.eliminar_actividad,
        name='eliminar_actividad',
    ),
    # Nuevas rutas para la configuración de auditoría
    path('configuracion/', verificar_rol_administrador(views.configuracion_auditoria), name='configuracion_auditoria'),
    path('crear-configuracion/', views.crear_configuracion, name='crear_configuracion'),
    path('editar-configuracion/<int:id>/', views.editar_configuracion, name='editar_configuracion'),
    path('eliminar-configuracion/<int:id>/', views.eliminar_configuracion, name='eliminar_configuracion'),
    # Ver detalles de actividad
    path('detalle-actividad/<int:id>/', views.detalle_actividad, name='detalle_actividad'),
    path('actualizar-config-navegacion/', views.actualizar_config_navegacion, name='actualizar_config_navegacion'),
    # Nueva ruta para configuración global
    path('configuracion-global/', verificar_rol_administrador(views.configuracion_global_auditoria), name='configuracion_global_auditoria'),
    path('crear-configuracion-global/', views.crear_configuracion_global, name='crear_configuracion_global'),
    path('eliminar-configuracion-global/<int:id>/', views.eliminar_configuracion_global, name='eliminar_configuracion_global'),
    path('editar-configuracion-global/<int:id>/', views.editar_configuracion_global, name='editar_configuracion_global'),
]

