from dashboard.models import Tarea, Proyecto, Recurso, Alerta, Notificacion, Usuario, Monitoreotarea, Jefeproyecto
from django.utils import timezone
from datetime import timedelta
from django.db.models import F, ExpressionWrapper, fields, Q
from django.core.mail import send_mail
from django.conf import settings
import logging

class MonitoreoService:
    @staticmethod
    def verificar_tareas_retrasadas():
        """Verifica tareas que están retrasadas según su fecha de fin"""
        hoy = timezone.now().date()
        
        # Buscar tareas que deberían haber terminado pero no están completadas
        # Buscar tareas que deberían haber terminado pero no están completadas
        tareas_retrasadas = Tarea.objects.filter(
            fechafin__lt=hoy,
            estado__in=['Pendiente', 'En Progreso']
        ).exclude(
            alerta__tipoalerta='retraso',
            alerta__activa=True
        )
        
        alertas_creadas = 0
        for tarea in tareas_retrasadas:
            # Crear alerta de retraso
            Alerta.objects.create(
                idtarea=tarea,
                tipoalerta='retraso',
                mensaje=f"La tarea '{tarea.nombretarea}' está retrasada. Debía finalizar el {tarea.fechafin}.",
                activa=True,
                fechacreacion=timezone.now()
            )
            alertas_creadas += 1
            
        return alertas_creadas
    
    @staticmethod
    def verificar_presupuesto_excedido():
        """Verifica tareas que han excedido su presupuesto estimado"""
        tareas_presupuesto_excedido = Tarea.objects.filter(
            costoactual__gt=F('costoestimado') * 1.1  # 10% más que lo estimado
        ).exclude(
            alerta__tipoalerta='presupuesto',
            alerta__activa=True
        )
        alertas_creadas = 0
        for tarea in tareas_presupuesto_excedido:
            Alerta.objects.create(
                idtarea=tarea,
                tipoalerta='presupuesto',
                mensaje=f"La tarea '{tarea.nombretarea}' ha excedido su presupuesto estimado en un {((tarea.costoactual/tarea.costoestimado)-1)*100:.1f}%.",
                activa=True,
                fechacreacion=timezone.now()
            )
            alertas_creadas += 1
            
        return alertas_creadas
        
    @staticmethod
    def verificar_tareas_bloqueadas():
        """Verifica tareas que están bloqueadas por alguna dependencia"""
        # Esta verificación puede ser específica a tu lógica de negocio
        tareas_bloqueadas = Monitoreotarea.objects.filter(
            porcentajecompletado__lt=10,  # Tareas con poco avance
            fechainicioreal__lt=timezone.now().date() - timedelta(days=7),  # Iniciaron hace más de una semana
            fechafinreal__isnull=True  # No han terminado
        ).exclude(
            idtarea__alerta__tipoalerta='bloqueo',
            idtarea__alerta__activa=True
        )
        
        alertas_creadas = 0
        for monitoreo in tareas_bloqueadas:
            Alerta.objects.create(
                idtarea=monitoreo.idtarea,
                tipoalerta='bloqueo',
                mensaje=f"La tarea '{monitoreo.idtarea.nombretarea}' parece estar bloqueada. Avance menor al 10% después de una semana.",
                activa=True,
                fechacreacion=timezone.now()
            )
            alertas_creadas += 1
        
        return alertas_creadas


# Configurar el logger
logger = logging.getLogger(__name__)

class NotificacionService:
    @staticmethod
    def notificar_alerta_a_usuarios(alerta):
        """Notifica a los usuarios relevantes sobre una alerta"""
        try:
            tarea = alerta.idtarea
            logger.info(f"Procesando alerta: {alerta.idalerta}, tipo: {alerta.tipoalerta}, tarea: {tarea.nombretarea}")
            
            proyecto = tarea.idrequerimiento.idproyecto
            logger.info(f"Proyecto relacionado: {proyecto.nombreproyecto}, equipo: {proyecto.idequipo}")
            
            # Buscar usuarios relacionados con el equipo del proyecto
            usuarios_equipo = Usuario.objects.filter(
                recursohumano__idrecurso__in=Recurso.objects.filter(
                    miembro__idequipo=proyecto.idequipo
                )
            ).distinct()
            logger.info(f"Usuarios del equipo encontrados: {usuarios_equipo.count()}")
            
            # Obtener los recursos asignados a la tarea
            recursos_tarea = Recurso.objects.filter(
                tarearecurso__idtarea=tarea.idtarea
            )
            
            # Luego obtener los usuarios asociados a esos recursos
            usuarios_tarea = Usuario.objects.filter(
                recursohumano__idrecurso__in=recursos_tarea
            ).distinct()
            logger.info(f"Usuarios asignados a tarea encontrados: {usuarios_tarea.count()}")
            
            
            # Crear notificaciones para cada usuario relevante
            notificaciones_creadas = 0
            for usuario in usuarios_tarea:
                # Solo enviar notificación si el usuario tiene habilitadas las notificaciones
                logger.info(f"Verificando usuario: {usuario.nombreusuario}, notif_sistema: {usuario.notif_sistema}")
                if usuario.notif_sistema:
                    Notificacion.objects.create(
                        idusuario=usuario,
                        mensaje=f"[ALERTA] {alerta.tipoalerta.upper()}: {alerta.mensaje}",
                        leido=False,
                        fechacreacion=timezone.now(),
                        prioridad="alta" if alerta.tipoalerta in ['bloqueo', 'retraso'] else "media",
                        categoria="Backend" if tarea.tipo_tarea and tarea.tipo_tarea.nombre == "Backend" else "Otro",
                        archivada=False
                    )
                    notificaciones_creadas += 1
                    logger.info(f"Notificación creada para: {usuario.nombreusuario}")
                
                # Enviar email si está habilitado
                if usuario.notif_email:
                    resultado = NotificacionService.enviar_correo_notificacion(usuario, alerta)
                    logger.info(f"Envío de correo a {usuario.email}: {'éxito' if resultado else 'fallido'}")
            
            logger.info(f"Total notificaciones creadas: {notificaciones_creadas}")
            return notificaciones_creadas
        except Exception as e:
            logger.error(f"Error al notificar alerta {alerta.idalerta}: {str(e)}")
            return 0

    @staticmethod
    def enviar_correo_notificacion(usuario, alerta):
        """Envía notificación por correo si el usuario tiene habilitada esta opción"""
        if not usuario.notif_email:
            return False
        
        tarea = alerta.idtarea
        proyecto = tarea.idrequerimiento.idproyecto
        
        asunto = f"[WebApp-PM] Alerta: {alerta.tipoalerta.upper()} en {tarea.nombretarea}"
        mensaje = f"""
        Hola {usuario.nombreusuario},
        
        Se ha generado una alerta en el sistema:
        
        Tipo: {alerta.tipoalerta.upper()}
        Tarea: {tarea.nombretarea}
        Proyecto: {proyecto.nombreproyecto}
        Mensaje: {alerta.mensaje}
        
        Por favor, ingrese al sistema para más detalles.
        
        Saludos,
        WebApp-PM
        """
        
        try:
            send_mail(
                asunto,
                mensaje,
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
            return True
        except Exception as e:
            print(f"Error enviando correo: {str(e)}")
            return False
