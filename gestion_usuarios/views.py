# usuarios/views.py
from django.shortcuts import render, redirect
from dashboard.models import Usuario
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from dashboard.models import Usuario
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required

@login_required
def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    for usuario in usuarios:
        if usuario.last_login is None:
            usuario.last_login = "No ha iniciado sesión"
    return render(
        request, "gestion_usuarios/lista_usuarios.html", {"usuarios": usuarios}
    )


def crear_usuario(request):
    if request.method == "POST":
        # Captura los datos enviados desde el formulario
        nombre = request.POST.get("nombreUsuario")
        email = request.POST.get("email")
        contrasena = request.POST.get("contrasena")
        rol = request.POST.get("rol")

        # Crea el usuario
        Usuario.objects.create(
            nombreUsuario=nombre, email=email, contrasena=contrasena, rol=rol
        )
        return redirect("gestionUsuarios:lista_usuarios")
    return render(request, "gestion_usuarios/crear_usuario.html")


def register(request):
    if request.method == "POST":
        nombreusuario = request.POST.get("nombreusuario")
        email = request.POST.get("email")
        contrasena = request.POST.get("contrasena")
        confirmar_contrasena = request.POST.get("confirmar_contrasena")
        rol = request.POST.get("rol")

        # Validaciones
        if Usuario.objects.filter(nombreusuario=nombreusuario).exists():
            messages.error(request, "El nombre de usuario ya está en uso")
            return redirect("register")

        if Usuario.objects.filter(email=email).exists():
            messages.error(request, "El correo electrónico ya está registrado")
            return redirect("register")

        if contrasena != confirmar_contrasena:
            messages.error(request, "Las contraseñas no coinciden")
            return redirect("register")

        try:
            # Validar contraseña usando validadores de Django
            validate_password(contrasena)
        except ValidationError as e:
            messages.error(request, "\n".join(e.messages))
            return redirect("gestionUsuarios:register")

        try:
            # Crear usuario
            usuario = Usuario.objects.create_user(
                nombreusuario=nombreusuario,
                username=nombreusuario,  # Django requiere username
                email=email,
                contrasena=contrasena,
                password=contrasena,  # Django requiere password
                rol=rol,
                fechacreacion=timezone.now(),
                fechamodificacion=timezone.now(),
            )

            # Crear registro específico según el rol
            if rol == "Desarrollador":
                from dashboard.models import Desarrollador

                Desarrollador.objects.create(idusuario=usuario)
            elif rol == "JefeProyecto":
                from dashboard.models import Jefeproyecto

                Jefeproyecto.objects.create(idusuario=usuario)
            elif rol == "Tester":
                from dashboard.models import Tester

                Tester.objects.create(idusuario=usuario)

            messages.success(request, "Usuario registrado exitosamente")
            return redirect("gestionUsuarios:login")

        except Exception as e:
            messages.error(request, f"Error al crear el usuario: {str(e)}")
            return redirect("gestionUsuarios:register")

    return render(request, "registration/register.html")


@csrf_protect
def login_view(request):
    if request.method == "POST":
        nombreusuario = request.POST.get("nombreusuario")
        contrasena = request.POST.get("contrasena")
        remember_me = request.POST.get("remember_me")

        # Autenticar usuario
        user = authenticate(request, username=nombreusuario, password=contrasena)

        if user is not None:
            login(request, user)

            # Configurar la sesión si "recordarme" está marcado
            if not remember_me:
                request.session.set_expiry(0)

            # Redireccionar al dashboard después del login exitoso
            messages.success(request, f"¡Bienvenido {user.nombreusuario}!")
            return redirect("dashboard:index")
        else:
            messages.error(request, "Nombre de usuario o contraseña incorrectos")

    return render(request, "registration/login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente")
        return redirect("gestionUsuarios:login")
    return redirect("dashboard:index")


@login_required
def perfil_view(request):
    return render(request, "gestion_usuarios/perfil.html")


@login_required
def configuracion_view(request):
    return render(request, "gestion_usuarios/configuracion.html")
