from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.contrib.auth import get_user_model
import json
import ipaddress
import socket
import threading

# Importamos todos los modelos relevantes para auditoría
from dashboard.models import (
    Actividad, DetalleActividad, ConfiguracionAuditoria,
    Proyecto, Requerimiento, Tarea, Recurso, Equipo, Usuario, 
    Alerta, Fase, TareaComun, Notificacion
)

# Variable local para almacenar el usuario actual
_thread_local = threading.local()

def set_current_user(user):
    """Almacena el usuario actual para el hilo en ejecución"""
    _thread_local.user = user

def get_current_user():
    """Obtiene el usuario almacenado para el hilo actual"""
    return getattr(_thread_local, 'user', None)

def get_client_ip():
    """Obtener IP local cuando no hay request disponible"""
    try:
        hostname = socket.gethostname()
        return socket.gethostbyname(hostname)
    except:
        return "127.0.0.1"

def get_model_config(model_instance):
    """Obtener la configuración de auditoría para un modelo"""
    model_name = model_instance.__class__.__name__
    
    # No auditar la configuración de auditoría para evitar recursión infinita
    if model_name == 'ConfiguracionAuditoria':
        return None
    
    try:
        # Primero intentar encontrar una configuración existente
        configs = list(ConfiguracionAuditoria.objects.filter(modelo=model_name, campo__isnull=True))
        
        # Si hay configuraciones existentes
        if configs:
            if len(configs) > 1:
                # Si hay duplicados, usar la primera y programar una limpieza
                print(f"Encontradas {len(configs)} configuraciones para {model_name}. Usando la primera y programando limpieza.")
                # Programar la limpieza en segundo plano (para no afectar esta operación)
                from django.core.management import call_command
                import threading
                threading.Thread(target=lambda: call_command('cleanup_audit_configs')).start()
                return configs[0]
            else:
                # Solo hay una configuración, perfecto
                return configs[0]
        else:
            # No hay configuración, crear una nueva
            config = ConfiguracionAuditoria.objects.create(
                modelo=model_name,
                campo=None,  # Configuración para todo el modelo (no un campo específico)
                auditar_crear=True,
                auditar_modificar=True, 
                auditar_eliminar=True,
                nivel_detalle=2  # Nivel detallado por defecto
            )
            return config
    except Exception as e:
        print(f"Error al obtener/crear configuración de auditoría: {e}")
        # Si hay error, usar valores predeterminados
        return None

def get_model_name(instance):
    """Obtener un nombre legible y en español para el modelo"""
    model_names = {
        'Proyecto': 'Proyecto',
        'Tarea': 'Tarea',
        'Recurso': 'Recurso',
        'Equipo': 'Equipo',
        'Usuario': 'Usuario',
        'Fase': 'Fase',
        'TareaComun': 'Tarea Común',
        'Requerimiento': 'Requerimiento',
        'Alerta': 'Alerta',
        'Notificacion': 'Notificación'
    }
    
    model_name = instance.__class__.__name__
    return model_names.get(model_name, model_name)

def get_instance_name(instance):
    """Obtener un nombre identificativo para la instancia del modelo"""
    if hasattr(instance, 'nombre'):
        return instance.nombre
    elif hasattr(instance, 'nombreusuario'):
        return instance.nombreusuario
    elif hasattr(instance, 'nombretarea'):
        return instance.nombretarea
    elif hasattr(instance, 'nombreproyecto'):
        return instance.nombreproyecto
    elif hasattr(instance, 'nombreequipo'):
        return instance.nombreequipo
    elif hasattr(instance, 'nombrerecurso'):
        return instance.nombrerecurso
    elif hasattr(instance, 'descripcion') and instance.descripcion:
        return f"{instance.descripcion[:50]}..." if len(instance.descripcion) > 50 else instance.descripcion
    else:
        # Obtener el nombre del modelo y su ID
        return f"{get_model_name(instance)} ID: {instance.pk}"

from .model_relationships import is_child_model, get_parent_model, get_relation_field

# Agregar un registro temporal para evitar actividades duplicadas
_processed_instances = {}

def registrar_cambios(instance, changes, action_type, user=None):
    """Registrar los cambios en una instancia de modelo"""
    model_name = instance.__class__.__name__
    
    # Verificar si acabamos de procesar esta instancia (prevenir duplicados)
    instance_key = f"{model_name}_{instance.pk}_{action_type}"
    current_time = timezone.now()
    if instance_key in _processed_instances:
        last_processed_time = _processed_instances[instance_key]
        # Si la última vez que procesamos esta instancia fue hace menos de 1 segundo, ignorarla
        if (current_time - last_processed_time).total_seconds() < 1:
            print(f"Ignorando actividad duplicada: {instance_key}")
            return

    # Marcar esta instancia como procesada ahora
    _processed_instances[instance_key] = current_time
    
    # Limpiar entradas antiguas del registro (más de 10 segundos)
    for key in list(_processed_instances.keys()):
        if (current_time - _processed_instances[key]).total_seconds() > 10:
            del _processed_instances[key]

    # Primero verificamos si es un modelo hijo
    if is_child_model(model_name):
        parent_model_name = get_parent_model(model_name)
        relation_field = get_relation_field(model_name)
        
        # Solo si tiene la relación con el padre y hay cambios que propagar
        if hasattr(instance, relation_field) and changes:
            parent_instance = getattr(instance, relation_field)
            
            # Prefijamos los campos para distinguir que vienen del hijo
            prefixed_changes = {}
            for field, values in changes.items():
                prefixed_field = f"{model_name}.{field}"
                prefixed_changes[prefixed_field] = values
            
            # Si el padre ya tiene cambios, los extendemos
            if hasattr(parent_instance, '_changes'):
                parent_changes = getattr(parent_instance, '_changes', {})
                parent_changes.update(prefixed_changes)
                setattr(parent_instance, '_changes', parent_changes)
            else:
                # Si no tiene cambios previos, asignamos los nuevos
                setattr(parent_instance, '_changes', prefixed_changes)
                
        # No continuamos la auditoría para el hijo
        return
    
    # Obtener configuración de auditoría para este modelo (o crear si no existe)
    config = get_model_config(instance)
    
    # Si no hay configuración o está desactivada para esta acción
    if not config:
        return
    
    # Verificar si este tipo de acción debe ser auditada según la configuración
    if (action_type == 'CREACION' and not config.auditar_crear) or \
       (action_type == 'MODIFICACION' and not config.auditar_modificar) or \
       (action_type == 'ELIMINACION' and not config.auditar_eliminar):
        return
    
    # Detectar usuario actual
    if not user:
        user = get_current_user()
        if not user:
            # Si no hay usuario en contexto, intentamos buscar un superusuario como fallback
            try:
                User = get_user_model()
                user = User.objects.filter(is_superuser=True).first()
            except:
                pass
    
    # Obtener nombre amigable para el usuario
    instance_name = get_instance_name(instance)
    model_display = get_model_name(instance)
    
    # Información básica para todos los niveles
    descripcion_basica = ""
    if action_type == 'CREACION':
        descripcion_basica = f"Se ha creado {model_display.lower()}: {instance_name}"
    elif action_type == 'MODIFICACION':
        descripcion_basica = f"Se ha modificado {model_display.lower()}: {instance_name}"
    elif action_type == 'ELIMINACION':
        descripcion_basica = f"Se ha eliminado {model_display.lower()}: {instance_name}"
    
    # Crear la actividad principal según el nivel de detalle
    ip = get_client_ip()
    actividad = None
    
    # NIVEL 1: Registro básico - solo información esencial
    if config.nivel_detalle == 1:
        actividad = Actividad(
            nombre=f"{action_type} de {model_display}",
            descripcion=descripcion_basica,
            idusuario=user,
            accion=action_type,
            entidad_tipo=model_name,
            entidad_id=instance.pk,
            ip_address=ip,
            es_automatica=True
        )
        
    # NIVEL 2 y NIVEL 3: Registro detallado
    else:
        # Añadir resumen de cambios
        num_cambios = len(changes) if changes else 0
        host = socket.gethostname()
        
        if action_type == 'MODIFICACION' and num_cambios > 0:
            campos_modificados = [field.replace('_', ' ').title() for field in changes.keys()]
            campos_str = ", ".join(campos_modificados) if len(campos_modificados) <= 5 else f"{len(campos_modificados)} campos"
            descripcion_detallada = f"{descripcion_basica} ({campos_str}) desde {host}"
        else:
            descripcion_detallada = descripcion_basica
        
        actividad = Actividad(
            nombre=f"{action_type} de {model_display}",
            descripcion=descripcion_detallada,
            idusuario=user,
            accion=action_type,
            entidad_tipo=model_name,
            entidad_id=instance.pk,
            ip_address=ip,
            es_automatica=True
        )
    
    # Guardar la actividad
    actividad.save()
    
    # No registrar detalles en nivel 1
    if config.nivel_detalle == 1:
        return
        
    # Registrar detalles si hay cambios
    if changes and isinstance(changes, dict):
        for field, values in changes.items():
            # Verificar si el campo debe ser auditado específicamente
            field_config = ConfiguracionAuditoria.objects.filter(modelo=model_name, campo=field).first()
            if field_config and not field_config.auditar_modificar:
                continue
                
            # Para nivel 2 y 3, registrar todos los campos
            field_name = field.replace('_', ' ').title()
            
            DetalleActividad.objects.create(
                idactividad=actividad,
                nombre_campo=field_name,
                valor_anterior=values.get('old', None),
                valor_nuevo=values.get('new', None)
            )
            
# FUNCION NO UTILIZADA SE PUEDE ELIMINAR
def get_entity_details(instance):
    """Obtener información detallada de la entidad según su tipo"""
    model_name = instance.__class__.__name__
    details = []
    
    if model_name == 'Proyecto':
        details.append(f"Nombre: {instance.nombreproyecto}")
        if hasattr(instance, 'estado') and instance.estado:
            details.append(f"Estado: {instance.estado}")
        if hasattr(instance, 'presupuesto') and instance.presupuesto:
            details.append(f"Presupuesto: {instance.presupuesto}")
        if hasattr(instance, 'idequipo') and instance.idequipo:
            details.append(f"Equipo: {instance.idequipo.nombreequipo}")
    
    elif model_name == 'Tarea':
        details.append(f"Nombre: {instance.nombretarea}")
        if hasattr(instance, 'estado') and instance.estado:
            details.append(f"Estado: {instance.estado}")
        if hasattr(instance, 'prioridad') and instance.prioridad:
            details.append(f"Prioridad: {instance.prioridad}")
        if hasattr(instance, 'fechainicio') and instance.fechainicio:
            details.append(f"Inicio: {instance.fechainicio}")
        if hasattr(instance, 'fechafin') and instance.fechafin:
            details.append(f"Fin: {instance.fechafin}")
    
    elif model_name == 'Usuario':
        details.append(f"Usuario: {instance.nombreusuario}")
        if hasattr(instance, 'email') and instance.email:
            details.append(f"Email: {instance.email}")
        if hasattr(instance, 'rol') and instance.rol:
            details.append(f"Rol: {instance.rol}")
    
    elif model_name == 'Recurso':
        details.append(f"Nombre: {instance.nombrerecurso}")
        if hasattr(instance, 'disponibilidad'):
            disp = "Disponible" if instance.disponibilidad else "No disponible"
            details.append(f"Disponibilidad: {disp}")
        if hasattr(instance, 'carga_trabajo') and instance.carga_trabajo:
            details.append(f"Carga: {instance.carga_trabajo}%")
    
    # Añadir más entidades según sea necesario...
    
    if not details:  # Si no se encontró ningún detalle específico
        # Obtener algunos atributos generales
        for attr in ['nombre', 'descripcion', 'estado', 'fecha', 'id']:
            if hasattr(instance, attr):
                val = getattr(instance, attr)
                if val:
                    details.append(f"{attr.capitalize()}: {val}")
    
    if details:
        return " | ".join(details)
    else:
        return f"ID: {instance.pk}"

# Para capturar diferencias entre estado anterior y nuevo
@receiver(pre_save)
def pre_save_handler(sender, instance, **kwargs):
    """Almacena temporalmente los valores anteriores para comparar después"""
    # Excluir modelos que no queremos auditar
    excluded_models = ['Session', 'LogEntry', 'ContentType', 'Permission', 
                       'Actividad', 'DetalleActividad', 'ConfiguracionAuditoria']
    if sender.__name__ in excluded_models:
        return
    
    # Verificar si el modelo debe ser auditado
    config = get_model_config(instance)
    if not config or not config.auditar_modificar:
        return
        
    if instance.pk:
        # Si la instancia ya existe, es una actualización
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            changes = {}
            
            # Comparar cada campo
            for field in instance._meta.fields:
                field_name = field.name
                
                # Ignorar campos que típicamente no se deberían auditar
                if field_name in ['updated_at', 'fechamodificacion', 'last_login']:
                    continue
                    
                # Obtener valores antiguos y nuevos
                old_value = getattr(old_instance, field_name)
                new_value = getattr(instance, field_name)
                
                # Si son diferentes, registrar el cambio
                if old_value != new_value:
                    changes[field_name] = {'old': str(old_value), 'new': str(new_value)}
            
            # Guardar cambios temporalmente en la instancia
            if changes:
                instance._changes = changes
        except Exception as e:
            print(f"Error en pre_save_handler: {e}")

@receiver(post_save)
def audit_post_save(sender, instance, created, **kwargs):
    """Registra creaciones y modificaciones automáticamente"""
    # Excluir modelos que no queremos auditar
    excluded_models = ['Session', 'LogEntry', 'ContentType', 'Permission', 
                      'Actividad', 'DetalleActividad', 'ConfiguracionAuditoria']
    if sender.__name__ in excluded_models:
        return
    
    # Verificar si este es un modelo hijo que debe ser ignorado para auditoría directa
    if is_child_model(sender.__name__):
        # Si es hijo, no continuamos con la auditoría directa
        # Ya que los cambios se registrarán a través del padre
        return
    
    # Obtener configuración de auditoría para el modelo
    config = get_model_config(instance)
    if not config:
        return
        
    # Determinar tipo de acción y cambios
    action_type = 'CREACION' if created else 'MODIFICACION'
    changes = getattr(instance, '_changes', {}) if hasattr(instance, '_changes') else {}
    
    # Si no hay cambios y es una modificación, no auditar
    if not created and not changes:
        return
    
    # Obtener usuario actual
    user = get_current_user()
    
    # Registrar la actividad
    if (created and config.auditar_crear) or (not created and config.auditar_modificar and changes):
        registrar_cambios(instance, changes, action_type, user)

@receiver(post_delete)
def audit_post_delete(sender, instance, **kwargs):
    """Registra eliminaciones automáticamente"""
    # Excluir modelos que no queremos auditar
    excluded_models = ['Session', 'LogEntry', 'ContentType', 'Permission', 
                      'Actividad', 'DetalleActividad', 'ConfiguracionAuditoria']
    if sender.__name__ in excluded_models:
        return
    
    # Obtener configuración de auditoría
    config = get_model_config(instance)
    if not config or not config.auditar_eliminar:
        return
    
    # Obtener usuario actual
    user = get_current_user()
    
    # Registrar la eliminación
    registrar_cambios(instance, {}, 'ELIMINACION', user)

# Lista completa de modelos a auditar
models_to_audit = [
    # Modelos principales
    Proyecto, Requerimiento, Tarea, Recurso, Equipo, Usuario, 
    # Modelos secundarios
    Alerta, Fase, TareaComun, Notificacion
]

# Esta función se debe llamar en el archivo apps.py del módulo auditoria para registrar todas las señales
def register_signals():
    for model in models_to_audit:
        post_save.connect(audit_post_save, sender=model)
        post_delete.connect(audit_post_delete, sender=model)
        pre_save.connect(pre_save_handler, sender=model)
