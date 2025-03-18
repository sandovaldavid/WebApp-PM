"""
Utilidades para diagnóstico y depuración de problemas con IPC y entrenamiento
"""

import os
import traceback
import time
import json
from datetime import datetime

# Constantes de configuración
DEBUG_ENABLED = True
DEBUG_FILE = os.path.join('logs', 'training_debug.log')
DEBUG_CONSOLE = True

# Asegurar que el directorio de logs existe
os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)

def trace_log(message, category="DEBUG", include_stack=False):
    """Escribe un mensaje de diagnóstico en el archivo de log con formato consistente"""
    try:
        timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S.%f")[:-3] + "]"
        log_msg = f"{timestamp} [{category}] {message}"
        print(log_msg)  # También mostrar en consola
        
        # Si se solicita, incluir stack trace
        if include_stack:
            stack = traceback.format_stack()[:-1]  # Excluir esta función
            stack_str = "STACK:\n  " + "\n  ".join([line.strip() for line in stack])
            log_msg += "\n" + stack_str
        
        # Crear directorio logs si no existe
        os.makedirs('logs', exist_ok=True)
        
        # Escribir en archivo de log general
        log_file = os.path.join('logs', 'debug.log')
        with open(log_file, 'a') as f:
            f.write(log_msg + "\n")
        
        # Si es un error, también escribir en log específico
        if category in ["ERROR", "WARNING", "CRITICAL"]:
            error_log = os.path.join('logs', 'errors.log')
            with open(error_log, 'a') as f:
                f.write(log_msg + "\n")
        
        return True
    
    except Exception as e:
        # Si fallamos al escribir el log, al menos intentar mostrar en consola
        print(f"[ERROR] Error al escribir log: {str(e)}")
        print(f"Mensaje original: {message}")
        return False

def log_epoch_event(training_id, epoch_number, total_epochs, message, source):
    """Registrar eventos específicos de época para diagnóstico"""
    trace_log(
        f"LOG ÉPOCA {epoch_number}/{total_epochs} en training_id={training_id} | Fuente: {source} | {message}",
        category="EPOCH_EVENT"
    )

def inspect_queue(training_id):
    """Inspecciona el estado actual de la cola IPC para un training_id
    
    Args:
        training_id: ID del entrenamiento a verificar
        
    Returns:
        dict: Información sobre la cola
    """
    try:
        from redes_neuronales.ipc_utils import get_queue_for_training
        
        queue = get_queue_for_training(training_id)
        if not queue:
            return {
                'present': False,
                'message': 'No se pudo obtener una cola para el training_id'
            }
        
        result = {
            'present': True,
            'type': str(type(queue)),
        }
        
        # Verificar el tamaño de la cola
        if hasattr(queue, 'qsize'):
            result['size'] = queue.qsize()
            result['empty'] = queue.empty()
        else:
            result['size'] = 'unknown'
            result['empty'] = 'unknown'
        
        # Intentar obtener información adicional
        if hasattr(queue, '_maxsize'):
            result['max_size'] = queue._maxsize
        
        return result
    
    except Exception as e:
        return {
            'error': str(e),
            'trace': traceback.format_exc()
        }

def log_ipc_operation(operation_type, training_id, data=None):
    """Registrar operaciones IPC para diagnóstico"""
    if data and isinstance(data, dict) and data.get('type') == 'log' and data.get('is_epoch_log'):
        epoch_num = data.get('epoch_number', 'unknown')
        total_epochs = data.get('total_epochs', 'unknown')
        trace_log(
            f"IPC {operation_type.upper()}: training_id={training_id}, ÉPOCA={epoch_num}/{total_epochs}", 
            category="IPC_EPOCH"
        )
    else:
        trace_log(f"IPC {operation_type.upper()}: training_id={training_id}", category="IPC")

def check_cache_state(training_id):
    """Inspecciona el estado de la caché para un training_id
    
    Args:
        training_id: ID del entrenamiento a verificar
        
    Returns:
        dict: Estado de la caché
    """
    try:
        from django.core.cache import cache
        
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key)
        
        if not config:
            return {
                'present': False,
                'message': 'La configuración no está en caché'
            }
        
        # Estadísticas básicas de la configuración
        result = {
            'present': True,
            'status': config.get('status', 'unknown'),
            'has_updates': 'updates' in config,
            'updates_count': len(config.get('updates', [])),
        }
        
        # Estadísticas sobre logs de época
        if result['has_updates']:
            updates = config.get('updates', [])
            epoch_logs = [u for u in updates if u.get('type') == 'log' and u.get('is_epoch_log')]
            result['epoch_logs_count'] = len(epoch_logs)
            
            # Extraer números de época
            epoch_numbers = []
            for log in epoch_logs:
                epoch = log.get('epoch_number') or log.get('epoch')
                if epoch and isinstance(epoch, (int, str)) and str(epoch).isdigit():
                    epoch_numbers.append(int(epoch))
            
            result['epochs_present'] = sorted(list(set(epoch_numbers)))
            result['max_epoch'] = max(epoch_numbers) if epoch_numbers else 0
            
            # Verificar si hay huecos en la secuencia de épocas
            if epoch_numbers:
                expected_sequence = set(range(1, max(epoch_numbers) + 1))
                missing_epochs = expected_sequence - set(epoch_numbers)
                result['missing_epochs'] = sorted(list(missing_epochs))
                result['has_gaps'] = len(missing_epochs) > 0
        
        return result
    
    except Exception as e:
        return {
            'error': str(e),
            'trace': traceback.format_exc()
        }

# Diagnósticos adicionales
def verify_connections(training_id):
    """Verifica el estado de conexiones Redis y cola IPC para un training_id
    
    Args:
        training_id: ID del entrenamiento a verificar
        
    Returns:
        dict: Estado de las conexiones
    """
    result = {
        'redis_ok': False,
        'ipc_ok': False,
        'cache_present': False,
        'issues': []
    }
    
    try:
        # Verificar conexión Redis
        try:
            from django_redis import get_redis_connection
            conn = get_redis_connection("default")
            # Prueba simple para verificar que Redis responde
            conn.ping()
            result['redis_ok'] = True
        except Exception as e:
            result['redis_ok'] = False
            result['issues'].append(f"Error al verificar Redis: {str(e)}")
    
        # Verificar caché de Django
        try:
            from django.core.cache import cache
            config_key = f'training_config_{training_id}'
            config = cache.get(config_key)
            if config:
                result['cache_present'] = True
            else:
                result['issues'].append("No se encontró configuración en caché para este entrenamiento")
        except Exception as e:
            result['issues'].append(f"Error al verificar caché: {str(e)}")
    
        # Verificar cola IPC
        try:
            from redes_neuronales.ipc_utils import get_queue_for_training
            queue = get_queue_for_training(training_id)
            if queue:
                result['ipc_ok'] = True
                # Verificar tamaño de cola
                if hasattr(queue, 'qsize'):
                    queue_size = queue.qsize()
                    result['queue_size'] = queue_size
                    if queue_size > 100:
                        result['issues'].append(f"Cola IPC es muy grande ({queue_size} elementos)")
                else:
                    result['issues'].append("Cola no tiene método qsize() - posible tipo incorrecto")
            else:
                result['issues'].append("No se pudo obtener una cola IPC válida")
        except Exception as e:
            result['issues'].append(f"Error al verificar cola IPC: {str(e)}")
    
    except Exception as e:
        result['issues'].append(f"Error general en verificación: {str(e)}")
    
    return result
