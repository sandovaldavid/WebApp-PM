from django.urls import path

from . import views

app_name = "gestion_proyectos"
urlpatterns = [
    path('', views.index, name='index'),
    path('proyectos', views.lista_proyectos, name='lista_proyectos'),
    path('proyecto/<int:idproyecto>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('crear-proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path(
        'editar-proyecto/<int:idproyecto>/',
        views.editar_proyecto,
        name='editar_proyecto',
    ),
    path(
        'eliminar-proyecto/<int:idproyecto>/',
        views.eliminar_proyecto,
        name='eliminar_proyecto',
    ),
    path(
        'eliminar-requerimiento/<int:idrequerimiento>/',
        views.eliminar_requerimiento,
        name='eliminar_requerimiento',
    ),
    path(
        'estadisticas-proyecto/<int:idproyecto>/',
        views.estadisticas_proyecto,
        name='estadisticas_proyecto',
    ),
    path('filtrar-proyectos/', views.filtrar_proyectos, name='filtrar_proyectos'),
    path('panel-proyectos/', views.panel_proyectos, name='panel_proyectos'),
    path(
        'crear-requerimiento/<int:idproyecto>/',
        views.crear_requerimiento,
        name='crear_requerimiento',
    ),  # Nueva ruta
    path(
        'detalle-requerimiento/<int:idrequerimiento>/',
        views.detalle_requerimiento,
        name='detalle_requerimiento',
    ),  # Nueva ruta
    path(
        'editar-requerimiento/<int:idrequerimiento>/',
        views.editar_requerimiento,
        name='editar_requerimiento',
    ),  # Nueva ruta
    path(
        'eliminar-requerimiento/<int:idrequerimiento>/',
        views.eliminar_requerimiento,
        name='eliminar_requerimiento',
    ),  # Nueva ruta
    path(
        'ajustar_fechas/<int:proyecto_id>/', views.ajustar_fechas, name='ajustar_fechas'
    ),
    path(
        'ajustar_presupuesto/<int:proyecto_id>/',
        views.ajustar_presupuesto,
        name='ajustar_presupuesto',
    ),
]
