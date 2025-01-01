# usuarios/urls.py
from django.urls import path
from . import views
from dashboard.views import verificar_rol_administrador

app_name = 'gestionUsuarios'
urlpatterns = [
    path("", views.lista_usuarios, name="lista_usuarios"),
    path("crear/", views.crear_usuario, name="crear_usuario"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/", views.perfil_view, name="perfil"),
    path("configuracion/", views.configuracion_view, name="configuracion"),
]
