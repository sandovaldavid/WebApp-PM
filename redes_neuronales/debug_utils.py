"""
Utilidades para diagnóstico y depuración del flujo de comunicación en el entrenamiento de modelos
"""
import os
import time
import json
import inspect
import traceback
from datetime import datetime

# Constantes de configuración
DEBUG_ENABLED = True
DEBUG_FILE = os.path.join('logs', 'training_debug.log')
DEBUG_CONSOLE = True

# Asegurar que el directorio de logs existe
os.makedirs(os.path.dirname(DEBUG_FILE), exist_ok=True)

def trace_log(message, category="INFO", include_stack=False):
    """Registrar mensaje de diagnóstico con información detallada"""
    if not DEBUG_ENABLED:
        return
        
    # Obtener información de la llamada
    caller_frame = inspect.currentframe().f_back
    caller_file = os.path.basename(caller_frame.f_code.co_filename)
    caller_func = caller_frame.f_code.co_name
    caller_line = caller_frame.f_lineno
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Formatear mensaje de log
    log_message = f"[{timestamp}] [{category}] [{caller_file}:{caller_func}:{caller_line}] {message}"
    
    # Añadir stack trace si se solicita
    if include_stack:
        stack = traceback.format_stack()[:-1]  # Excluir esta función
        stack_info = "\n".join(stack)
        log_message += f"\nSTACK:\n{stack_info}"
    
    # Imprimir en consola si está habilitado
    if DEBUG_CONSOLE:
        print(log_message)
    
    # Guardar en archivo
    try:
        with open(DEBUG_FILE, 'a', encoding='utf-8') as f:
            f.write(log_message + "\n")
    except Exception as e:
        print(f"Error al guardar log: {e}")

def log_epoch_event(training_id, epoch_number, total_epochs, message, source):
    """Registrar eventos específicos de época para diagnóstico"""
    trace_log(
        f"LOG ÉPOCA {epoch_number}/{total_epochs} en training_id={training_id} | Fuente: {source} | {message}",
        category="EPOCH_EVENT"
    )

def inspect_queue(training_id):
    """Inspeccionar estado actual de la cola IPC para un entrenamiento"""
    from .ipc_utils import get_queue_for_training
    
    try:
        queue = get_queue_for_training(training_id)
        queue_size = queue.qsize() if hasattr(queue, 'qsize') else 'unknown'
        queue_empty = queue.empty() if hasattr(queue, 'empty') else 'unknown'
        
        trace_log(f"Estado de cola para training_id={training_id}: size={queue_size}, empty={queue_empty}", 
                 category="QUEUE_STATUS")
        
        return {
            'size': queue_size,
            'empty': queue_empty,
            'queue_id': str(id(queue))
        }
    except Exception as e:
        trace_log(f"Error al inspeccionar cola: {e}", category="ERROR", include_stack=True)
        return {
            'error': str(e),
            'status': 'error'
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
    """Verificar estado actual del caché para un entrenamiento"""
    from django.core.cache import cache
    
    try:
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key)
        
        if config:
            updates_count = len(config.get('updates', []))
            last_epochs = []
            
            # Buscar últimos 3 logs de época en updates
            for update in reversed(config.get('updates', [])):
                if update.get('type') == 'log' and update.get('is_epoch_log'):
                    epoch_num = update.get('epoch_number')
                    if epoch_num:
                        last_epochs.append(epoch_num)
                    if len(last_epochs) >= 3:
                        break
            
            trace_log(
                f"Estado caché para training_id={training_id}: {updates_count} updates, últimas épocas={last_epochs}",
                category="CACHE_STATUS"
            )
            
            return {
                'updates_count': updates_count,
                'last_epochs': last_epochs,
                'status': config.get('status')
            }
        else:
            trace_log(f"No se encontró configuración en caché para training_id={training_id}", category="CACHE_STATUS")
            return {
                'status': 'not_found'
            }
    except Exception as e:
        trace_log(f"Error al verificar caché: {e}", category="ERROR", include_stack=True)
        return {
            'error': str(e),
            'status': 'error'
        }

# Diagnósticos adicionales
def verify_connections(training_id):
    """Verificar todas las conexiones para un entrenamiento específico"""
    # Verificación de la cola IPC y caché (sin Redis)
    cache_state = check_cache_state(training_id)
    queue_state = inspect_queue(training_id)
    
    # Verificar si tenemos proceso activo para este entrenamiento
    has_active_process = False
    try:
        from redes_neuronales.tasks import _ACTIVE_TASKS, active_processes
        has_active_process = training_id in _ACTIVE_TASKS or any(
            pid for pid, process in active_processes.items() if process.is_alive()
        )
    except Exception as e:
        trace_log(f"Error al verificar procesos activos: {e}", category="ERROR")
    
    results = {
        'cache': cache_state,
        'queue': queue_state,
        'process': {'active': has_active_process},
        'ipc_queue': queue_state['size'] != 'unknown'  # Indica si la cola IPC está disponible
    }
    
    trace_log(f"Verificación de conexiones para training_id={training_id}: {json.dumps(results)}", 
             category="DIAGNOSTIC")
    
    return results
