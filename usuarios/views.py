from django.shortcuts import render, redirect
from django.contrib.auth.hashers import make_password, check_password
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.http import JsonResponse
from django.db import transaction
from dashboard.models import Usuario
import uuid
from django.utils import timezone

# Configuración de Mailtrap en settings.py
settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
settings.EMAIL_HOST = 'smtp.mailtrap.io'
settings.EMAIL_PORT = 2525
settings.EMAIL_HOST_USER = 'c80a4723a23860'
settings.EMAIL_HOST_PASSWORD = '58bc6052674eba'
settings.EMAIL_USE_TLS = True


# Vista para la página de inicio
def index(request):
    return render(request, 'usuarios/index.html')

# Vista para registro de usuarios
def crear_cuenta(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                nombre_usuario = request.POST['nombreUsuario']
                email = request.POST['email']
                contrasena = request.POST['contrasena']
                repetir_contrasena = request.POST['repetirContrasena']
                rol = request.POST['rol']

                # Verificar si las contraseñas coinciden
                if contrasena != repetir_contrasena:
                    return render(request, 'usuarios/register.html', {
                        'error': 'Las contraseñas no coinciden.',
                        'nombreUsuario': nombre_usuario,
                        'email': email
                    })

                # Verificar si el email ya está registrado
                if Usuario.objects.filter(email=email).exists():
                    return render(request, 'usuarios/register.html', {
                        'error': 'El correo electrónico ya está registrado.',
                        'nombreUsuario': nombre_usuario,
                        'email': email
                    })

                # Generar token para confirmación
                token = str(uuid.uuid4())

                # Encriptar contraseña
                contrasena_hash = make_password(contrasena)

                # Crear usuario
                usuario = Usuario.objects.create(
                    nombreusuario=nombre_usuario,
                    email=email,
                    contrasena=contrasena_hash,
                    rol=rol,
                    token=token,
                    confirmado=False,
                    fechacreacion=timezone.now()  # Agregar fecha de creación
                )

                # Enviar correo de confirmación
                enviar_correo_confirmacion(usuario.email, token)
                return render(request, 'usuarios/index.html', {'mensaje': 'Cuenta creada. Por favor revisa tu correo para confirmar tu cuenta.'})                
        except Exception as e:
            return render(request, 'usuarios/register.html', {
                'error': str(e),
                'nombreUsuario': nombre_usuario,
                'email': email
            })
    return render(request, 'usuarios/register.html')

# Vista para confirmar cuenta
def confirmar_cuenta(request, token):
    try:
        usuario = Usuario.objects.get(token=token)
        usuario.confirmado = True
        usuario.token = None  # Limpiar token después de confirmación
        usuario.save()
        return render(request, 'usuarios/index.html', {'mensaje': 'Cuenta confirmada exitosamente.'})
    except Usuario.DoesNotExist:
        return render(request, 'usuarios/index.html', {'error': 'Token inválido o cuenta ya confirmada.'})

# Vista para iniciar sesión
def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        contrasena = request.POST.get('contrasena')
        if not email or not contrasena:
            return render(request, 'usuarios/login.html', {'error': 'Email y contraseña son requeridos.', 'email': email})
        try:
            usuario = Usuario.objects.get(email=email)
            if not usuario.confirmado:
                return render(request, 'usuarios/login.html', {'error': 'Debes confirmar tu cuenta antes de iniciar sesión.', 'email': email})
            if check_password(contrasena, usuario.contrasena):
                request.session['usuario_id'] = usuario.idusuario
                request.session['usuario_nombre'] = usuario.nombreusuario  # Guardar nombre del usuario en la sesión
                request.session['usuario_rol'] = usuario.rol  # Guardar rol del usuario en la sesión
                return redirect('dashboard:index')  # Redirigir a la página principal después del inicio de sesión exitoso
            else:
                return render(request, 'usuarios/login.html', {'error': 'Contraseña incorrecta.', 'email': email})
        except Usuario.DoesNotExist:
            return render(request, 'usuarios/login.html', {'error': 'Usuario no encontrado.', 'email': email})
    return render(request, 'usuarios/login.html')

# Vista para cerrar sesión
def logout(request):
    request.session.flush()  # Eliminar todas las variables de sesión
    return redirect('usuarios:login')

# Vista para recuperar contraseña
def olvide_password(request):
    if request.method == 'POST':
        email = request.POST['email']
        try:
            usuario = Usuario.objects.get(email=email)
            token = str(uuid.uuid4())
            usuario.token = token
            usuario.save()
            enviar_correo_recuperacion(usuario.email, token)
            return render(request, 'usuarios/index.html', {'mensaje': 'Correo de recuperación enviado.'})
        except Usuario.DoesNotExist:
            return render(request, 'usuarios/olvide_password.html', {'error': 'Usuario no encontrado.', 'email': email})
    return render(request, 'usuarios/olvide_password.html')

# Vista para recuperar contraseña
def recuperar(request, token):
    if request.method == 'POST':
        contrasena = request.POST['contrasena']
        repetir_contrasena = request.POST['repetirContrasena']
        
        # Verificar si las contraseñas coinciden
        if contrasena != repetir_contrasena:
            return render(request, 'usuarios/recuperar.html', {
                'error': 'Las contraseñas no coinciden.'
            })
        
        try:
            usuario = Usuario.objects.get(token=token)
            usuario.contrasena = make_password(contrasena)
            usuario.token = None  # Limpiar token después de la recuperación
            usuario.save()
            return render(request, 'usuarios/index.html', {'mensaje': 'Contraseña actualizada exitosamente.'})
        except Usuario.DoesNotExist:
            return render(request, 'usuarios/recuperar.html', {'error': 'Token inválido o expirado.'})
    return render(request, 'usuarios/recuperar.html')

# Función para enviar correo de confirmación
def enviar_correo_confirmacion(email, token):
    asunto = 'Confirma tu cuenta'
    mensaje_texto = f'Por favor, confirma tu cuenta haciendo clic en el siguiente enlace: \nhttp://localhost:8000/confirmar/{token}'
    mensaje_html = f'''
    <html>
    <body>
        <h2>Confirma tu cuenta</h2>
        <p>Por favor, confirma tu cuenta haciendo clic en el siguiente enlace:</p>
        <a href="http://localhost:8000/confirmar/{token}" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 5px;">Confirmar Cuenta</a>
        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
        <p>http://localhost:8000/confirmar/{token}</p>
    </body>
    </html>
    '''
    remitente = settings.EMAIL_HOST_USER
    correo = EmailMultiAlternatives(asunto, mensaje_texto, remitente, [email])
    correo.attach_alternative(mensaje_html, "text/html")
    correo.send()

# Función para enviar correo de recuperación de contraseña
def enviar_correo_recuperacion(email, token):
    asunto = 'Recuperación de contraseña'
    mensaje_texto = f'Para recuperar tu contraseña, haz clic en el siguiente enlace: \nhttp://localhost:8000/recuperar/{token}'
    mensaje_html = f'''
    <html>
    <body>
        <h2>Recuperación de contraseña</h2>
        <p>Para recuperar tu contraseña, haz clic en el siguiente enlace:</p>
        <a href="http://localhost:8000/recuperar/{token}" style="display: inline-block; padding: 10px 20px; font-size: 16px; color: #ffffff; background-color: #007bff; text-decoration: none; border-radius: 5px;">Recuperar Contraseña</a>
        <p>Si no puedes hacer clic en el enlace, copia y pega la siguiente URL en tu navegador:</p>
        <p>http://localhost:8000/recuperar/{token}</p>
    </body>
    </html>
    '''
    remitente = settings.EMAIL_HOST_USER
    correo = EmailMultiAlternatives(asunto, mensaje_texto, remitente, [email])
    correo.attach_alternative(mensaje_html, "text/html")
    correo.send()

