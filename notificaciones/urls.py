from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Dashboard y vistas principales
    path('', views.index, name='index'),
    
    # Notificaciones
    path('notificaciones/lista/', views.lista_notificaciones, name='lista_notificaciones'),
    path('notificaciones/crear/', views.crear_notificacion, name='crear_notificacion'),
    path('notificaciones/<int:id>/detalle/', views.detalle_notificacion, name='detalle_notificacion'),
    path('notificaciones/<int:id>/marcar_leida/', views.marcar_notificacion, name='marcar_leida'),
    path('notificaciones/<int:id>/archivar/', views.archivar_notificacion, name='archivar_notificacion'),
    path('notificaciones/<int:id>/eliminar/', views.eliminar_notificacion, name='eliminar_notificacion'),
    path('notificaciones/marcar_todas_leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('notificaciones/filtrar/', views.filtrar_notificaciones, name='filtrar_notificaciones'),
    path('notificaciones/vista_previa/', views.vista_previa_notificacion, name='vista_previa_notificacion'),
    path('notificaciones/estadisticas/', views.estadisticas_notificaciones, name='estadisticas_notificaciones'),
    
    # Alertas
    path('alertas/lista/', views.lista_alertas, name='lista_alertas'),
    path('alertas/crear/', views.crear_alerta, name='crear_alerta'),
    path('alertas/<int:id>/detalle/', views.detalle_alerta, name='detalle_alerta'),
    path('alertas/<int:id>/resolver/', views.resolver_alerta, name='resolver_alerta'),
    path('alertas/filtrar/', views.filtrar_alertas, name='filtrar_alertas'),
    path('alertas/vista_previa/', views.vista_previa_alerta, name='vista_previa_alerta'),
    path('alertas/generar/', views.generar_alertas, name='generar_alertas'),
    path('alertas/estadisticas/', views.estadisticas_alertas, name='estadisticas_alertas'),
]
