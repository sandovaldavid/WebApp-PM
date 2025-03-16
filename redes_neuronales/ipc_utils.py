from multiprocessing import Queue
import time
import os
import json

# Diccionario global que almacenará las colas para cada entrenamiento
# Este diccionario es accesible desde el proceso principal y los procesos hijos
training_queues = {}

# Variable para habilitar logging detallado - CAMBIADO A FALSE para reducir verbosidad
DEBUG_MODE = False
TRACE_FILE = os.path.join('logs', 'ipc_trace.log')

# Asegurar que existe el directorio
os.makedirs(os.path.dirname(TRACE_FILE), exist_ok=True)

def debug_trace(message, training_id=None):
    """Función interna para registro de diagnóstico"""
    if not DEBUG_MODE:
        return
        
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    msg = f"[{timestamp}] [IPC] "
    if training_id:
        msg += f"[{training_id}] "
    msg += message
    
    # Solo imprimir a consola mensajes importantes (no verbose)
    if "ERROR" in message or "FALLIDO" in message or "❌" in message:
        print(msg)
    
    # Siempre guardar todos los mensajes a archivo
    try:
        with open(TRACE_FILE, 'a') as f:
            f.write(msg + "\n")
    except Exception as e:
        print(f"Error al guardar log IPC: {e}")

def get_queue_for_training(training_id):
    """Obtiene o crea una cola para un entrenamiento específico"""
    if training_id not in training_queues:
        debug_trace(f"Creando nueva cola para training_id={training_id}")
        training_queues[training_id] = Queue()
    else:
        # No loggear este mensaje a menos que sea necesario para debugging
        if DEBUG_MODE:
            debug_trace(f"Usando cola existente para training_id={training_id}")
        
    return training_queues[training_id]

def clear_queue_for_training(training_id):
    """Limpia la cola de un entrenamiento para liberar recursos"""
    if training_id in training_queues:
        debug_trace(f"Limpiando cola para training_id={training_id}")
        # Vaciar la cola primero para evitar bloqueos
        queue = training_queues[training_id]
        items_removed = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                items_removed += 1
            except:
                break
        debug_trace(f"Eliminados {items_removed} elementos de la cola para training_id={training_id}")
        del training_queues[training_id]
        debug_trace(f"Cola eliminada para training_id={training_id}")
    else:
        debug_trace(f"No se encontró cola para limpiar: training_id={training_id}")

def send_update(training_id, update_data):
    """Envía una actualización a la cola del entrenamiento"""
    queue = get_queue_for_training(training_id)
    
    # Registrar información detallada si es un log de época
    is_epoch_log = False
    epoch_info = ""
    if update_data.get('type') == 'log' and update_data.get('is_epoch_log'):
        is_epoch_log = True
        epoch_num = update_data.get('epoch_number', '?')
        total_epochs = update_data.get('total_epochs', '?')
        epoch_info = f" ÉPOCA {epoch_num}/{total_epochs}"
        
        debug_trace(f"ENVIANDO LOG DE ÉPOCA A COLA: {epoch_num}/{total_epochs} con message={update_data.get('message', '')[:50]}...", training_id)
    
    # Enviar a la cola
    try:
        queue.put(update_data)
        if is_epoch_log:
            debug_trace(f"✅✅ LOG DE ÉPOCA {epoch_info} AÑADIDO EXITOSAMENTE A COLA", training_id)
        else:
            # Solo registrar tipos importantes, no cada actualización
            if update_data.get('type') not in ['heartbeat']:
                debug_trace(f"Actualización enviada a cola: {update_data.get('type')}", training_id)
    except Exception as e:
        debug_trace(f"❌❌ ERROR al enviar a cola: {str(e)}", training_id)
    
    # Registrar para diagnóstico adicional
    try:
        from redes_neuronales.debug_utils import log_ipc_operation
        log_ipc_operation("send", training_id, update_data)
    except ImportError:
        # El módulo de diagnóstico puede no estar disponible aún
        pass

def get_updates(training_id, timeout=0.5):
    """Obtiene todas las actualizaciones disponibles para un entrenamiento"""
    queue = get_queue_for_training(training_id)
    updates = []
    
    # Intentar obtener todos los elementos disponibles sin bloquear
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            update = queue.get_nowait()
            updates.append(update)
            
            # Registrar si es un log de época
            if update.get('type') == 'log' and update.get('is_epoch_log'):
                epoch_num = update.get('epoch_number', '?')
                total_epochs = update.get('total_epochs', '?')
                debug_trace(f"✅ RECIBIDO LOG DE ÉPOCA {epoch_num}/{total_epochs} DE COLA", training_id)
        except:
            # No hay más elementos o ocurrió un error
            break
    
    count = len(updates)
    epoch_count = sum(1 for u in updates if u.get('type') == 'log' and u.get('is_epoch_log'))
    
    if count > 0:
        debug_trace(f"Se obtuvieron {count} actualizaciones de la cola ({epoch_count} logs de época)", training_id)
    
    # Registrar para diagnóstico adicional
    try:
        from redes_neuronales.debug_utils import log_ipc_operation
        if count > 0:
            log_ipc_operation("receive", training_id, {"count": count, "epoch_count": epoch_count})
    except ImportError:
        # El módulo de diagnóstico puede no estar disponible aún
        pass
            
    return updates

def dump_queue_status():
    """Devuelve un estado detallado de todas las colas para diagnóstico"""
    status = {}
    for training_id, queue in training_queues.items():
        try:
            status[training_id] = {
                "queue_id": id(queue),
                "size": queue.qsize() if hasattr(queue, 'qsize') else 'unknown',
                "empty": queue.empty() if hasattr(queue, 'empty') else 'unknown'
            }
        except Exception as e:
            status[training_id] = {"error": str(e)}
    
    debug_trace(f"Estado de todas las colas: {json.dumps(status)}")
    return status
