import uuid

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect

# Renombrar la función de logout de Django para evitar la colisión de nombres
from django.contrib.auth import logout as auth_logout

# Importar la señal para login fallido
from django.contrib.auth.signals import user_login_failed

from dashboard.models import (
    Usuario,
    Administrador,
    Jefeproyecto,
    Cliente,
    Tester,
    Desarrollador,
    Actividad,
)
from auditoria.middleware import AuditoriaMiddleware


# Vista para la página de inicio
def index(request):
    return render(request, "usuarios/index.html")


# Vista para registro de usuarios
def crear_cuenta(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                nombre_usuario = request.POST["nombreUsuario"]
                email = request.POST["email"]
                contrasena = request.POST["contrasena"]
                repetir_contrasena = request.POST["repetirContrasena"]
                rol = request.POST["rol"]

                # Validar campos vacíos
                if not all(
                    [nombre_usuario, email, contrasena, repetir_contrasena, rol]
                ):
                    raise ValueError("Todos los campos son requeridos")

                # Verificar si el nombre de usuario ya existe
                if Usuario.objects.filter(nombreusuario=nombre_usuario).exists():
                    return render(
                        request,
                        "usuarios/register.html",
                        {
                            "error": "El nombre de usuario ya está en uso",
                            "email": email,
                        },
                    )

                # Verificar si el email ya está registrado
                if Usuario.objects.filter(email=email).exists():
                    return render(
                        request,
                        "usuarios/register.html",
                        {
                            "error": "El correo electrónico ya está registrado",
                            "nombreUsuario": nombre_usuario,
                        },
                    )

                # Verificar si las contraseñas coinciden
                if contrasena != repetir_contrasena:
                    return render(
                        request,
                        "usuarios/register.html",
                        {
                            "error": "Las contraseñas no coinciden",
                            "nombreUsuario": nombre_usuario,
                            "email": email,
                        },
                    )

                # Generar token para confirmación
                token = str(uuid.uuid4())

                # Crear usuario
                usuario = Usuario.objects.create(
                    nombreusuario=nombre_usuario,
                    email=email,
                    contrasena=make_password(contrasena),
                    rol=rol,
                    token=token,
                    confirmado=False,
                    fechacreacion=timezone.now(),
                    fechamodificacion=timezone.now(),
                    username=nombre_usuario,  # Llenar campo username
                    password=make_password(contrasena),  # Llenar campo password
                )

                # Insertar en la tabla correspondiente según el rol

                if rol == "Administrador":
                    Administrador.objects.create(idusuario=usuario)
                elif rol == "Jefe de Proyecto":
                    Jefeproyecto.objects.create(idusuario=usuario)
                elif rol == "Cliente":
                    Cliente.objects.create(idusuario=usuario)
                elif rol == "Tester":
                    Tester.objects.create(idusuario=usuario)
                elif rol == "Desarrollador":
                    Desarrollador.objects.create(idusuario=usuario)

                # Enviar correo de confirmación
                enviar_correo_confirmacion(email, token)

                return render(
                    request,
                    "usuarios/index.html",
                    {
                        "mensaje": "Cuenta creada. Por favor revisa tu correo para confirmar tu cuenta."
                    },
                )

        except Exception as e:
            return render(
                request,
                "usuarios/register.html",
                {
                    "error": f"Error al crear la cuenta: {str(e)}",
                    "nombreUsuario": nombre_usuario,
                    "email": email,
                },
            )

    # Si es GET, mostrar el formulario vacío
    return render(request, "usuarios/register.html")


# Vista para confirmar cuenta
def confirmar_cuenta(request, token):
    try:
        usuario = Usuario.objects.get(token=token)
        usuario.confirmado = True
        usuario.token = None  # Limpiar token después de confirmación
        usuario.save()
        return render(
            request,
            "usuarios/index.html",
            {"mensaje": "Cuenta confirmada exitosamente."},
        )
    except Usuario.DoesNotExist:
        return render(
            request,
            "usuarios/index.html",
            {"error": "Token inválido o cuenta ya confirmada."},
        )


# Vista para iniciar sesión
@csrf_protect
def login(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        email = request.POST.get("email")
        contrasena = request.POST.get("contrasena")

        if not email or not contrasena:
            # Emitir señal de login fallido por campos faltantes
            user_login_failed.send(
                sender=__name__, credentials={"username": email or ""}, request=request
            )
            return render(
                request,
                "usuarios/login.html",
                {"error": "Email y contraseña son requeridos.", "email": email},
            )

        try:
            usuario = Usuario.objects.get(email=email)

            if not usuario.confirmado:
                # Emitir señal de login fallido por cuenta no confirmada
                user_login_failed.send(
                    sender=__name__, credentials={"username": email}, request=request
                )
                return render(
                    request,
                    "usuarios/login.html",
                    {
                        "error": "Debes confirmar tu cuenta antes de iniciar sesión.",
                        "email": email,
                    },
                )

            # Usar authenticate y login de Django
            if check_password(contrasena, usuario.contrasena):
                # Autenticar el usuario usando el backend explícitamente
                from django.contrib.auth import authenticate, login as auth_login

                # Obtener el backend que usaremos
                from django.contrib.auth import get_backends
                for backend in get_backends():
                    # Usar el primer backend disponible
                    usuario.backend = f"{backend.__module__}.{backend.__class__.__name__}"
                    break

                # Ahora podemos hacer login pasando el usuario con el atributo backend
                auth_login(request, usuario)

                # Actualizar el campo last_login
                usuario.last_login = timezone.now()
                usuario.save()

                # Guardar información adicional en la sesión
                request.session["usuario_id"] = usuario.idusuario
                request.session["usuario_nombre"] = usuario.nombreusuario
                request.session["usuario_rol"] = usuario.rol

                # Redireccionar al dashboard después del login exitoso
                messages.success(request, f"¡Bienvenido {usuario.nombreusuario}!")

                return redirect("dashboard:index")
            else:
                # Emitir señal de login fallido por contraseña incorrecta
                user_login_failed.send(
                    sender=__name__, credentials={"username": email}, request=request
                )
                return render(
                    request,
                    "usuarios/login.html",
                    {"error": "Contraseña incorrecta.", "email": email},
                )
        except Usuario.DoesNotExist:
            # Emitir señal de login fallido por usuario no encontrado
            user_login_failed.send(
                sender=__name__, credentials={"username": email}, request=request
            )
            return render(
                request,
                "usuarios/login.html",
                {"error": "Usuario no encontrado.", "email": email},
            )

    return render(request, "usuarios/login.html")


# Vista para cerrar sesión
# @login_required
# def logout(request):
#     request.session.flush()  # Eliminar todas las variables de sesión
#     messages.success(request, "Has cerrado sesión correctamente")
#     return redirect("usuarios:login")


# Vista para cerrar sesión
@login_required
def logout(request):
    # Ahora podemos cerrar la sesión usando la función de Django renombrada
    auth_logout(request)
    messages.success(request, "Has cerrado sesión correctamente")
    # Redirigir a la página de inicio o página de login
    return redirect("usuarios:login")  # Ajusta esta URL según tu configuración


# Vista para recuperar contraseña
def olvide_password(request):
    if request.method == "POST":
        email = request.POST["email"]
        try:
            usuario = Usuario.objects.get(email=email)
            token = str(uuid.uuid4())
            usuario.token = token
            usuario.save()
            enviar_correo_recuperacion(usuario.email, token)
            return render(
                request,
                "usuarios/index.html",
                {"mensaje": "Correo de recuperación enviado."},
            )
        except Usuario.DoesNotExist:
            return render(
                request,
                "usuarios/olvide_password.html",
                {"error": "Usuario no encontrado.", "email": email},
            )
    return render(request, "usuarios/olvide_password.html")


# Vista para recuperar contraseña
def recuperar(request, token):
    if request.method == "POST":
        contrasena = request.POST["contrasena"]
        repetir_contrasena = request.POST["repetirContrasena"]

        # Verificar si las contraseñas coinciden
        if contrasena != repetir_contrasena:
            return render(
                request,
                "usuarios/recuperar.html",
                {"error": "Las contraseñas no coinciden."},
            )

        try:
            usuario = Usuario.objects.get(token=token)
            usuario.contrasena = make_password(contrasena)
            usuario.password = make_password(contrasena)
            usuario.token = None  # Limpiar token después de la recuperación
            usuario.save()
            return render(
                request,
                "usuarios/index.html",
                {"mensaje": "Contraseña actualizada exitosamente."},
            )
        except Usuario.DoesNotExist:
            return render(
                request,
                "usuarios/recuperar.html",
                {"error": "Token inválido o expirado."},
            )
    return render(request, "usuarios/recuperar.html")


# Función para enviar correo de confirmación
def enviar_correo_confirmacion(email, token):
    asunto = "Confirma tu cuenta"
    mensaje_texto = f"Por favor, confirma tu cuenta haciendo clic en el siguiente enlace: \nhttp://localhost:8000/confirmar/{token}"
    mensaje_html = f"""
    <html>
    <body>
        <h2>Confirma tu cuenta</h2>
        <p>Por favor, confirma tu cuenta haciendo clic en el siguiente enlace:</p>
        <a href="http://localhost:8000/confirmar/{token}" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 5px;">Confirmar Cuenta</a>
        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
        <p>http://localhost:8000/confirmar/{token}</p>
    </body>
    </html>
    """
    remitente = settings.EMAIL_HOST_USER
    correo = EmailMultiAlternatives(asunto, mensaje_texto, remitente, [email])
    correo.attach_alternative(mensaje_html, "text/html")
    correo.send()


# Función para enviar correo de recuperación de contraseña
def enviar_correo_recuperacion(email, token):
    asunto = "Recuperación de contraseña"
    mensaje_texto = f"Para recuperar tu contraseña, haz clic en el siguiente enlace: \nhttp://localhost:8000/recuperar/{token}"
    mensaje_html = f"""
    <html>
    <body>
        <h2>Recuperación de contraseña</h2>
        <p>Para recuperar tu contraseña, haz clic en el siguiente enlace:</p>
        <a href="http://localhost:8000/recuperar/{token}" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 5px;">Recuperar Contraseña</a>
        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
        <p>http://localhost:8000/recuperar/{token}</p>
    </body>
    </html>
    """
    remitente = settings.EMAIL_HOST_USER
    correo = EmailMultiAlternatives(asunto, mensaje_texto, remitente, [email])
    correo.attach_alternative(mensaje_html, "text/html")
    correo.send()
