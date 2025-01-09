# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Usuario
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password
from django.core.exceptions import ValidationError
from dashboard.models import (
    Usuario,
    Administrador,
    Jefeproyecto,
    Cliente,
    Tester,
    Desarrollador,
)
from django.utils import timezone
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q
from django.core.mail import EmailMultiAlternatives
import uuid
from django.conf import settings
from django.db import transaction

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

@login_required
def lista_usuarios(request):
    vista = request.GET.get("vista", "grid")
    busqueda = request.GET.get("busqueda", "")
    rol = request.GET.get("rol", "")
    page = request.GET.get("page", 1)

    usuarios = Usuario.objects.all()

    if busqueda:
        usuarios = usuarios.filter(
            Q(nombreusuario__icontains=busqueda) | Q(email__icontains=busqueda)
        )

    if rol:
        usuarios = usuarios.filter(rol=rol)

    for usuario in usuarios:
        if usuario.last_login is None:
            usuario.last_login = "No ha iniciado sesión"

    # Estadísticas
    estadisticas = {
        "total_usuarios": Usuario.objects.count(),
        "desarrolladores": Usuario.objects.filter(rol="Desarrollador").count(),
        "clientes": Usuario.objects.filter(rol="Cliente").count(),
        "testers": Usuario.objects.filter(rol="Tester").count(),
        "jefes_proyecto": Usuario.objects.filter(rol="Jefe de Proyecto").count(),
        "administradores": Usuario.objects.filter(rol="Administrador").count(),
    }

    # Paginación
    usuarios = usuarios.order_by('idusuario')  # Ordenar por idusuario para evitar advertencia
    paginator = Paginator(usuarios, 9)  # 9 usuarios por página
    try:
        usuarios_paginados = paginator.page(page)
    except PageNotAnInteger:
        usuarios_paginados = paginator.page(1)
    except EmptyPage:
        usuarios_paginados = paginator.page(paginator.num_pages)

    return render(
        request, "gestion_usuarios/lista_usuarios.html", {"usuarios": usuarios_paginados, "estadisticas": estadisticas, "vista": vista, "filtros": {"busqueda": busqueda, "rol": rol}}
    )


def crear_usuario(request):
    if request.method == "POST":
        try:
            with transaction.atomic():
                nombre = request.POST.get("nombreUsuario")
                email = request.POST.get("email")
                contrasena = request.POST.get("contrasena")
                confirmar_contrasena = request.POST.get("confirmar_contrasena")
                rol = request.POST.get("rol")

                # Validaciones
                if not all([nombre, email, contrasena, confirmar_contrasena, rol]):
                    messages.error(request, "Todos los campos son requeridos")
                    return redirect("gestionUsuarios:crear_usuario")

                if Usuario.objects.filter(nombreusuario=nombre).exists():
                    messages.error(request, "El nombre de usuario ya está en uso")
                    return redirect("gestionUsuarios:crear_usuario")

                if Usuario.objects.filter(email=email).exists():
                    messages.error(request, "El correo electrónico ya está registrado")
                    return redirect("gestionUsuarios:crear_usuario")

                if contrasena != confirmar_contrasena:
                    messages.error(request, "Las contraseñas no coinciden")
                    return redirect("gestionUsuarios:crear_usuario")

                # Validar contraseña usando validadores de Django
                try:
                    validate_password(contrasena)
                except ValidationError as e:
                    messages.error(request, "\n".join(e.messages))
                    return redirect("gestionUsuarios:crear_usuario")

                # Generar token para confirmación
                token = str(uuid.uuid4())

                # Crear usuario
                usuario = Usuario.objects.create(
                    nombreusuario=nombre,
                    email=email,
                    contrasena=make_password(contrasena),
                    rol=rol,
                    token=token,
                    confirmado=False,
                    fechacreacion=timezone.now(),
                    fechamodificacion=timezone.now(),
                    username=nombre,  # Llenar campo username
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

                messages.success(request, "Usuario creado exitosamente. Esperando confirmación por correo electrónico.")
                return redirect("gestionUsuarios:lista_usuarios")

        except Exception as e:
            messages.error(request, f"Error al crear el usuario: {str(e)}")
            return redirect("gestionUsuarios:crear_usuario")

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
    return render(request, "gestion_usuarios/perfil.html", {"usuario": request.user})


@login_required
def configuracion_view(request):
    return render(request, "gestion_usuarios/configuracion.html")

@login_required
def editar_usuario(request, usuario_id):
    usuario = get_object_or_404(Usuario, idusuario=usuario_id)

    if request.method == "POST":
        try:
            with transaction.atomic():
                nombre = request.POST.get("nombreUsuario")
                email = request.POST.get("email")
                rol = request.POST.get("rol")

                # Validaciones
                if not all([nombre, email, rol]):
                    messages.error(request, "Todos los campos son requeridos")
                    return redirect("gestionUsuarios:editar_usuario", usuario_id=usuario_id)

                if Usuario.objects.filter(nombreusuario=nombre).exclude(idusuario=usuario_id).exists():
                    messages.error(request, "El nombre de usuario ya está en uso")
                    return redirect("gestionUsuarios:editar_usuario", usuario_id=usuario_id)

                if Usuario.objects.filter(email=email).exclude(idusuario=usuario_id).exists():
                    messages.error(request, "El correo electrónico ya está registrado")
                    return redirect("gestionUsuarios:editar_usuario", usuario_id=usuario_id)

                # Actualizar usuario
                usuario.nombreusuario = nombre
                usuario.email = email
                usuario.rol = rol
                usuario.fechamodificacion = timezone.now()
                usuario.save()

                messages.success(request, "Usuario actualizado exitosamente")
                return redirect("gestionUsuarios:lista_usuarios")

        except Exception as e:
            messages.error(request, f"Error al actualizar el usuario: {str(e)}")
            return redirect("gestionUsuarios:editar_usuario", usuario_id=usuario_id)

    return render(request, "gestion_usuarios/editar_usuario.html", {"usuario": usuario})
