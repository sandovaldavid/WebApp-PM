# usuarios/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from dashboard.views import verificar_rol_administrador

app_name = "gestionUsuarios"
urlpatterns = [
    path("", views.lista_usuarios, name="lista_usuarios"),
    path("crear/", views.crear_usuario, name="crear_usuario"),
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("perfil/", views.perfil_view, name="perfil"),
    path("configuracion/", views.configuracion_view, name="configuracion"),
    path("configuracion/perfil/", views.actualizar_perfil, name="actualizar_perfil"),
    path("configuracion/contrasena/", views.cambiar_contrasena, name="cambiar_contrasena"),
    path("configuracion/notificaciones/", views.actualizar_notificaciones, name="actualizar_notificaciones"),
    path("editar/<int:usuario_id>/", views.editar_usuario, name="editar_usuario"),
]
