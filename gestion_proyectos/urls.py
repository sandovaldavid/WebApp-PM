from django.urls import path
from . import views

app_name = 'gestion_proyectos'
urlpatterns = [
    path('', views.index, name='index'),
    path('proyectos', views.lista_proyectos, name='lista_proyectos'),
    path('proyecto/<int:idproyecto>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('crear-proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path('editar-proyecto/<int:idproyecto>/', views.editar_proyecto, name='editar_proyecto'),
    path('eliminar-requerimiento/<int:idrequerimiento>/', views.eliminar_requerimiento, name='eliminar_requerimiento'),
    path('estadisticas-proyecto/<int:idproyecto>/', views.estadisticas_proyecto, name='estadisticas_proyecto'),
    path('filtrar-proyectos/', views.filtrar_proyectos, name='filtrar_proyectos'),
    path('panel-proyectos/', views.panel_proyectos, name='panel_proyectos'),
]
