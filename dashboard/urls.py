from django.urls import path
from . import views
from .views import verificar_rol_administrador

app_name = 'dashboard'
urlpatterns = [
    path('', views.dashboard, name='index'),
    path('api/requerimientos/<int:proyecto_id>/', views.api_requerimientos, name='api_requerimientos'),
    path('api/tareas/<int:requerimiento_id>/', views.api_tareas, name='api_tareas'),
]
