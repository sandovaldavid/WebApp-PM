from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_recursos, name='lista_recursos'),
    path('crear/', views.crear_recurso, name='crear_recurso'),
    path('editar/<int:id>/', views.editar_recurso, name='editar_recurso'),
    path('eliminar/<int:id>/', views.eliminar_recurso, name='eliminar_recurso'),
    path('asignar/', views.asignar_recurso, name='asignar_recurso'),
]