# usuarios/views.py
from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Usuario
from django.contrib import messages
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.hashers import make_password, check_password
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
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
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
    usuarios = usuarios.order_by(
        'idusuario'
    )  # Ordenar por idusuario para evitar advertencia
    paginator = Paginator(usuarios, 9)  # 9 usuarios por página
    try:
        usuarios_paginados = paginator.page(page)
    except PageNotAnInteger:
        usuarios_paginados = paginator.page(1)
    except EmptyPage:
        usuarios_paginados = paginator.page(paginator.num_pages)

    return render(
        request,
        "gestion_usuarios/lista_usuarios.html",
        {
            "usuarios": usuarios_paginados,
            "estadisticas": estadisticas,
            "vista": vista,
            "filtros": {"busqueda": busqueda, "rol": rol},
        },
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

                messages.success(
                    request,
                    "Usuario creado exitosamente. Esperando confirmación por correo electrónico.",
                )
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
            return redirect("dashboard:panel_control")
        else:
            messages.error(request, "Nombre de usuario o contraseña incorrectos")

    return render(request, "registration/login.html")


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "Has cerrado sesión correctamente")
        return redirect("gestionUsuarios:login")
    return redirect("dashboard:panel_control")


@login_required
def perfil_view(request):
    return render(request, "gestion_usuarios/perfil.html", {"usuario": request.user})


@login_required
def configuracion_view(request):
    # Recuperar preferencias de notificación o establecer valores predeterminados
    try:
        # Intentar obtener las preferencias de notificación del usuario
        notificaciones = {
            "notif_email": getattr(request.user, "notif_email", True),
            "notif_sistema": getattr(request.user, "notif_sistema", True),
            "notif_tareas": getattr(request.user, "notif_tareas", True),
        }
        request.user.notif_email = notificaciones["notif_email"]
        request.user.notif_sistema = notificaciones["notif_sistema"]
        request.user.notif_tareas = notificaciones["notif_tareas"]
    except:
        # Si hay un error, establecer valores predeterminados
        request.user.notif_email = True
        request.user.notif_sistema = True
        request.user.notif_tareas = True

    return render(request, "gestion_usuarios/configuracion.html")


@login_required
def actualizar_perfil(request):
    if request.method == "POST":
        nombreusuario = request.POST.get("nombreusuario")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()

        # Validaciones de campos obligatorios
        if not nombreusuario or not email:
            messages.error(
                request,
                "El nombre de usuario y el correo electrónico son obligatorios.",
            )
            return redirect("gestionUsuarios:configuracion")

        # Verificar si el nombre de usuario ya existe (excluyendo al usuario actual)
        usuarios_con_mismo_nombre = Usuario.objects.filter(
            nombreusuario=nombreusuario
        ).exclude(idusuario=request.user.idusuario)
        if usuarios_con_mismo_nombre.exists():
            messages.error(
                request, "El nombre de usuario ya está en uso por otro usuario."
            )
            return redirect("gestionUsuarios:configuracion")

        # Verificar si el email ya existe (excluyendo al usuario actual)
        usuarios_con_mismo_email = Usuario.objects.filter(email=email).exclude(
            idusuario=request.user.idusuario
        )
        if usuarios_con_mismo_email.exists():
            messages.error(
                request, "El correo electrónico ya está registrado para otro usuario."
            )
            return redirect("gestionUsuarios:configuracion")

        # Actualizar usuario
        request.user.nombreusuario = nombreusuario
        request.user.username = (
            nombreusuario  # Mantener sincronizado username con nombreusuario
        )
        request.user.email = email
        request.user.first_name = first_name
        request.user.last_name = last_name
        request.user.fechamodificacion = timezone.now()
        request.user.save()

        messages.success(request, "Perfil actualizado exitosamente.")

    return redirect("gestionUsuarios:configuracion")


@login_required
def cambiar_contrasena(request):
    if request.method == "POST":
        contrasena_actual = request.POST.get("contrasena_actual")
        nueva_contrasena = request.POST.get("nueva_contrasena")
        confirmar_contrasena = request.POST.get("confirmar_contrasena")

        # Validaciones básicas
        if not contrasena_actual or not nueva_contrasena or not confirmar_contrasena:
            messages.error(request, "Todos los campos son obligatorios.")
            return redirect("gestionUsuarios:configuracion")

        # Verificar si la contraseña actual es correcta usando check_password
        if not check_password(contrasena_actual, request.user.contrasena):
            messages.error(request, "La contraseña actual no es correcta.")
            return redirect("gestionUsuarios:configuracion")

        # Verificar si las contraseñas nuevas coinciden
        if nueva_contrasena != confirmar_contrasena:
            messages.error(request, "Las nuevas contraseñas no coinciden.")
            return redirect("gestionUsuarios:configuracion")

        # Validar la nueva contraseña
        try:
            validate_password(nueva_contrasena, user=request.user)
        except ValidationError as e:
            for error in e.messages:
                messages.error(request, error)
            return redirect("gestionUsuarios:configuracion")

        # Actualizar contraseña
        request.user.contrasena = make_password(nueva_contrasena)
        request.user.password = make_password(
            nueva_contrasena
        )  # Actualizar también el campo password para mantener sincronización
        request.user.fechamodificacion = timezone.now()
        request.user.save()

        # Actualizar sesión para evitar cierre de sesión por cambio de contraseña
        update_session_auth_hash(request, request.user)

        messages.success(request, "Contraseña actualizada exitosamente.")

    return redirect("gestionUsuarios:configuracion")


@login_required
def actualizar_notificaciones(request):
    if request.method == "POST":
        # Obtener valores del formulario
        notif_email = request.POST.get("notif_email") == "on"
        notif_sistema = request.POST.get("notif_sistema") == "on"
        notif_tareas = request.POST.get("notif_tareas") == "on"

        # Actualizar preferencias
        try:
            usuario = request.user

            # Utilizamos getattr para verificar si los campos existen
            # Si no existen, los agregamos mediante un diccionario de extra_fields
            usuario_dict = usuario.__dict__

            # Comprobamos si necesitamos añadir alguno de los campos
            campos_actualizados = []

            # Si el campo no existe en el usuario, lo añadimos al diccionario
            if "notif_email" not in usuario_dict:
                campos_actualizados.append("notif_email")
            usuario.notif_email = notif_email

            if "notif_sistema" not in usuario_dict:
                campos_actualizados.append("notif_sistema")
            usuario.notif_sistema = notif_sistema

            if "notif_tareas" not in usuario_dict:
                campos_actualizados.append("notif_tareas")
            usuario.notif_tareas = notif_tareas

            # Actualizar fecha de modificación
            usuario.fechamodificacion = timezone.now()

            # Guardar el usuario con los cambios
            usuario.save()

            # Mensaje de éxito con información sobre campos añadidos
            if campos_actualizados:
                message = f"Preferencias de notificación actualizadas exitosamente. Se han añadido los siguientes campos: {', '.join(campos_actualizados)}."
                messages.success(request, message)
            else:
                messages.success(
                    request, "Preferencias de notificación actualizadas exitosamente."
                )

        except Exception as e:
            messages.error(request, f"Error al actualizar preferencias: {str(e)}")

    return redirect("gestionUsuarios:configuracion")


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
                    return redirect(
                        "gestionUsuarios:editar_usuario", usuario_id=usuario_id
                    )

                if (
                    Usuario.objects.filter(nombreusuario=nombre)
                    .exclude(idusuario=usuario_id)
                    .exists()
                ):
                    messages.error(request, "El nombre de usuario ya está en uso")
                    return redirect(
                        "gestionUsuarios:editar_usuario", usuario_id=usuario_id
                    )

                if (
                    Usuario.objects.filter(email=email)
                    .exclude(idusuario=usuario_id)
                    .exists()
                ):
                    messages.error(request, "El correo electrónico ya está registrado")
                    return redirect(
                        "gestionUsuarios:editar_usuario", usuario_id=usuario_id
                    )

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
