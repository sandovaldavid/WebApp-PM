from django.urls import path
from . import views

app_name = 'gestion_proyectos'
urlpatterns = [
    path('', views.lista_proyectos, name='lista_proyectos'),
    path('proyecto/<int:idproyecto>/', views.detalle_proyecto, name='detalle_proyecto'),
    path('crear-proyecto/', views.crear_proyecto, name='crear_proyecto'),
    path('editar-proyecto/<int:idproyecto>/', views.editar_proyecto, name='editar_proyecto'),
    path('eliminar-requerimiento/<int:idrequerimiento>/', views.eliminar_requerimiento, name='eliminar_requerimiento'),
]
