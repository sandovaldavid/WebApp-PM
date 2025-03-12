from django.urls import resolve
from django.utils import timezone
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver
from django.conf import settings
from dashboard.models import Actividad, Usuario
from .signals import set_current_user, get_current_user
import ipaddress
import socket
import platform

class AuditoriaMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Establecer el usuario actual para este request
        if hasattr(request, 'user') and request.user.is_authenticated:
            set_current_user(request.user)
            # Guardar el ID del usuario en la sesión para uso futuro (e.g., logout)
            if hasattr(request, 'session'):
                request.session['last_user_id'] = request.user.pk
        
        # Captura información antes de procesar la solicitud
        tiempo_inicio = timezone.now()
        ip_cliente = self.get_client_ip(request)
        url_path = request.path
        
        # Continuar con el flujo normal de la solicitud
        response = self.get_response(request)
        
        # No auditar solicitudes a recursos estáticos o del admin
        if self.should_skip_audit(request):
            return response
        
        # Registrar información después de procesar
        tiempo_respuesta = timezone.now() - tiempo_inicio
        codigo_respuesta = response.status_code
        
        # Verificar si el usuario está autenticado
        usuario = None
        if hasattr(request, 'user') and request.user.is_authenticated:
            usuario = request.user
            
            # Registrar la actividad de navegación solo para rutas importantes
            if self.should_audit_navigation(request) and self.is_navigation_audit_enabled():
                self.registrar_actividad_navegacion(
                    usuario, 
                    url_path, 
                    request.method,
                    tiempo_respuesta,
                    codigo_respuesta,
                    ip_cliente
                )
        
        return response
    
    def get_client_ip(self, request):
        """Obtener la IP del cliente desde la solicitud con mejor manejo para desarrollo local"""
        # Primero intentar obtener la IP desde proxies y headers comunes
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            # Headers alternativos comunes usados por proxies
            for header in ['HTTP_X_REAL_IP', 'HTTP_CLIENT_IP', 'REMOTE_ADDR']:
                ip = request.META.get(header)
                if ip:
                    break
            
            # Si no se encuentra ninguna IP o es localhost
            if not ip or ip == '127.0.0.1' or ip == 'localhost':
                # Intentar obtener la IP local real de la máquina
                try:
                    # Obtener el nombre del host
                    hostname = socket.gethostname()
                    # Obtener la dirección IP local (solo la IP, sin información adicional)
                    local_ip = socket.gethostbyname(hostname)
                    return local_ip
                except Exception:
                    # Si todo falla, devolver una IP válida
                    return '127.0.0.1'
        
        return ip
    
    def get_system_info(self):
        """Obtener información adicional del sistema para enriquecer los registros"""
        try:
            hostname = socket.gethostname()
            return f"{hostname} - {platform.system()} {platform.release()}"
        except:
            return "Unknown system"
    
    def should_skip_audit(self, request):
        """Determinar si se debe omitir la auditoría para esta solicitud"""
        # No auditar solicitudes a archivos estáticos o admin
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        # No auditar favicon, robots.txt y similares
        if request.path in ['/favicon.ico', '/robots.txt', '/sitemap.xml']:
            return True
        
        return False
    
    def should_audit_navigation(self, request):
        """Determinar si se debe auditar esta navegación específica"""
        # Rutas importantes a auditar (operaciones principales)
        important_prefixes = [
            '/gestion-proyectos/',
            '/gestion-tareas/',
            '/gestion-recursos/',
            '/gestion-equipos/',
            '/gestion-auditoria/',
            '/gestion-usuarios/',
            '/gestion-reportes/',
            '/dashboard/',
            '/integracion/',
            '/redes-neuronales/',
            '/gestion-notificaciones/',
        ]
        
        # Verificar si la ruta actual coincide con alguna importante
        for prefix in important_prefixes:
            if request.path.startswith(prefix):
                return True
        
        return False
    
    def registrar_actividad_navegacion(self, usuario, url, metodo, tiempo_respuesta, codigo, ip):
        """Registrar actividad de navegación en la base de datos"""
        try:
            # Resolver la URL para obtener más información
            resolver_match = resolve(url)
            vista_nombre = f"{resolver_match.app_name}:{resolver_match.url_name}" if resolver_match.url_name else url
            
            # Obtener información adicional del sistema
            sistema_info = self.get_system_info()
            
            Actividad.objects.create(
                nombre=f"Acceso a {vista_nombre}",
                descripcion=f"Usuario accedió a la ruta {url} mediante método {metodo}. Sistema: {sistema_info}",
                idusuario=usuario,
                accion="NAVEGACION",
                entidad_tipo="Sistema",
                ip_address=ip,  # Ahora solo contiene la IP válida
                es_automatica=True
            )
        except Exception as e:
            # Manejar cualquier error sin interrumpir la respuesta
            print(f"Error al registrar actividad de navegación: {e}")

    def is_navigation_audit_enabled(self):
        """Verifica si el registro de navegación está habilitado globalmente"""
        from dashboard.models import ConfiguracionGeneralAuditoria
        try:
            config = ConfiguracionGeneralAuditoria.objects.filter(nombre="registrar_navegacion").first()
            if config:
                return config.valor.lower() in ('true', '1', 'yes', 'si')
            return True  # Por defecto habilitado si no existe configuración
        except:
            return True  # En caso de error, habilitarlo por defecto

# Registrar eventos de autenticación usando señales
@receiver(user_logged_in)
def usuario_login(sender, request, user, **kwargs):
    # Establecer el usuario para el contexto actual
    set_current_user(user)
    
    ip = AuditoriaMiddleware(None).get_client_ip(request)
    sistema_info = AuditoriaMiddleware(None).get_system_info()
    
    Actividad.objects.create(
        nombre="Inicio de sesión",
        descripcion=f"Usuario {user.nombreusuario} inició sesión exitosamente. Sistema: {sistema_info}",
        idusuario=user,
        accion="LOGIN",
        entidad_tipo="Autenticación",
        ip_address=ip,
        es_automatica=True
    )

@receiver(user_logged_out)
def usuario_logout(sender, request, user, **kwargs):
    """
    Registra actividades de cierre de sesión.
    Verifica si el cierre de sesión ya fue registrado manualmente.
    """
    try:
        # Verificar si el cierre de sesión ya fue registrado manualmente
        if request and hasattr(request, 'session') and request.session.get('logout_registered'):
            # Si ya fue registrado, no hacemos nada
            return
            
        # Si user es None, intentar obtenerlo del contexto actual
        if not user:
            user = get_current_user()
            
        # Si aún es None, verificar si hay información en la sesión
        if not user and request and hasattr(request, 'session') and 'last_user_id' in request.session:
            try:
                user_id = request.session.get('last_user_id')
                user = Usuario.objects.get(pk=user_id)
            except Usuario.DoesNotExist:
                pass
        
        # Solo si tenemos un usuario válido, registrar la actividad
        if user:
            ip = AuditoriaMiddleware(None).get_client_ip(request)
            sistema_info = AuditoriaMiddleware(None).get_system_info()
            
            Actividad.objects.create(
                nombre="Cierre de sesión",
                descripcion=f"Usuario {user.nombreusuario} cerró sesión. Sistema: {sistema_info}",
                idusuario=user,
                accion="LOGOUT",
                entidad_tipo="Autenticación",
                ip_address=ip,
                es_automatica=True
            )
        else:
            # Registrar actividad sin usuario si todo lo anterior falló
            ip = AuditoriaMiddleware(None).get_client_ip(request) if request else '127.0.0.1'
            Actividad.objects.create(
                nombre="Cierre de sesión",
                descripcion="Usuario desconocido cerró sesión",
                idusuario=None,
                accion="LOGOUT",
                entidad_tipo="Autenticación",
                ip_address=ip,
                es_automatica=True
            )
    except Exception as e:
        print(f"Error al registrar cierre de sesión: {e}")

@receiver(user_login_failed)
def usuario_login_fallido(sender, credentials, request, **kwargs):
    """
    Registra intentos fallidos de inicio de sesión con información detallada.
    """
    try:
        middleware = AuditoriaMiddleware(None)
        
        # Obtener la dirección IP y la información del sistema
        if request:
            ip = middleware.get_client_ip(request)
            system_info = middleware.get_system_info()
        else:
            # Si no hay request (caso raro), usamos valores predeterminados
            ip = '127.0.0.1'
            system_info = 'Sistema desconocido'
        
        # Intentar obtener el nombre de usuario de diferentes formas
        username = None
        if credentials and 'username' in credentials:
            username = credentials.get('username')
        elif request and request.POST and 'email' in request.POST:  # Si usa email como login
            username = request.POST.get('email')
        
        if not username:
            username = 'desconocido'
        
        # Buscar un usuario relacionado con el nombre de usuario o email
        usuario = None
        try:
            # Intentar buscar por nombre de usuario
            usuario = Usuario.objects.filter(nombreusuario=username).first()
            
            # Si no se encuentra, intentar buscar por email
            if not usuario and '@' in username:
                usuario = Usuario.objects.filter(email=username).first()
        except Exception as e:
            print(f"Error al buscar usuario para login fallido: {e}")
        
        # Registrar la información detallada del intento fallido
        detalles = f"Usuario: {username}"
        if request and hasattr(request, 'META'):
            detalles += f" | User-Agent: {request.META.get('HTTP_USER_AGENT', 'Desconocido')}"
        
        # Registramos la actividad con información detallada
        Actividad.objects.create(
            nombre="Intento de inicio de sesión fallido",
            descripcion=f"Intento fallido de inicio de sesión para el usuario: {username}. Sistema: {system_info}. {detalles}",
            idusuario=usuario,  # Puede ser None
            accion="LOGIN_FALLIDO",
            entidad_tipo="Autenticación",
            ip_address=ip,
            es_automatica=True
        )
    except Exception as e:
        # Capturar cualquier error para evitar que interrumpa el flujo de la aplicación
        print(f"Error al registrar intento de login fallido: {e}")