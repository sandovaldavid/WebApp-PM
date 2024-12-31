# usuarios/urls.py
from django.urls import path
from . import views
from dashboard.views import verificar_rol_administrador

app_name = 'gestionUsuarios'
urlpatterns = [
    path('', verificar_rol_administrador(views.lista_usuarios), name='lista_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
]
