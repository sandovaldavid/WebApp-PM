# usuarios/urls.py
from django.urls import path
from . import views

app_name = 'gestionUsuarios'
urlpatterns = [
    path('', views.lista_usuarios, name='lista_usuarios'),
    path('crear/', views.crear_usuario, name='crear_usuario'),
]