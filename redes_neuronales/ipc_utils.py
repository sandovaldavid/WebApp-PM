import os
import json
import time
import traceback
import sys
import platform
import queue as queue_module  # Importar el módulo queue explícitamente
from multiprocessing import freeze_support
import atexit
import gc
import weakref
import threading

# Aplicar freeze_support() si estamos en Windows
if platform.system() == 'Windows':
    freeze_support()

# Variable para usar sistema fallback
# CAMBIO IMPORTANTE: Siempre usar el modo fallback cuando se ejecuta en Django/Windows
USE_FALLBACK = True  # Forzar modo fallback por defecto para mayor compatibilidad

# Modo de depuración para ver información adicional
DEBUG_IPC = False

# Verificar entorno para determinar si debemos intentar usar Manager
try:
    # Verificar si estamos en un contexto donde podría funcionar multiprocessing
    is_main_process = sys.argv[0].endswith('manage.py') and 'runserver' not in sys.argv
    is_linux = platform.system() != 'Windows'
    
    # Solo intentar usar multiprocessing en condiciones específicas
    if (is_linux or is_main_process) and not USE_FALLBACK:
        if DEBUG_IPC:
            print("[IPC] Intentando inicializar Manager (modo multiprocessing)")
            
        from multiprocessing import Manager
        _manager = Manager()
        _queues = {}
        _queues_lock = threading.RLock()
        
        if DEBUG_IPC:
            print("[IPC] Manager inicializado correctamente")
            
        # Actualizar la bandera para indicar que no estamos usando fallback
        USE_FALLBACK = False
    else:
        raise ImportError("Usando modo fallback por configuración o entorno")
except Exception as e:
    if DEBUG_IPC:
        print(f"[IPC] No se pudo inicializar Manager: {e}")
        print("[IPC] Usando modo alternativo de comunicación (fallback)")
    
    # Configuración para modo fallback
    _manager = None
    _queues = {}
    _queues_lock = threading.RLock()
    USE_FALLBACK = True

# Lista para llevar registro de colas creadas
_all_queues = []
_all_queues_lock = threading.RLock()

# Si usamos fallback, crear un sistema basado en Queue de threading
if USE_FALLBACK:
    if DEBUG_IPC:
        print("[IPC] Inicializando sistema basado en threading.Queue")
    _fallback_queues = {}  # Usaremos Queue del módulo queue en lugar de multiprocessing.Queue
    
    # Función de limpieza para modo fallback
    def _cleanup_fallback_queues():
        if DEBUG_IPC:
            print("[IPC] Limpiando queues del modo fallback")
        for q_id in list(_fallback_queues.keys()):
            if q_id in _fallback_queues:
                _fallback_queues[q_id] = None  # Liberar la referencia
        _fallback_queues.clear()
    
    # Registrar limpieza para modo fallback
    atexit.register(_cleanup_fallback_queues)

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
    """Obtiene una cola para un entrenamiento específico, creándola si no existe"""
    global _queues, _all_queues, _fallback_queues
    
    # Si estamos en modo fallback, usar Queue de threading
    if USE_FALLBACK:
        if training_id in _fallback_queues:
            return _fallback_queues[training_id]
        
        # Crear nueva queue del módulo queue (threading-safe)
        try:
            q = queue_module.Queue()
            _fallback_queues[training_id] = q
            if DEBUG_IPC:
                print(f"[IPC-Fallback] Nueva cola creada para training_id={training_id}")
            return q
        except Exception as e:
            print(f"[IPC-Fallback] Error al crear cola: {str(e)}")
            traceback.print_exc()
            return None
    
    # Modo normal con multiprocessing (este camino rara vez se ejecutará)
    with _queues_lock:
        if training_id in _queues:
            queue = _queues[training_id]
            if queue is not None:
                return queue
    
    # Si llegamos aquí, necesitamos crear una nueva cola
    try:
        from multiprocessing import Queue
        queue = Queue()
        with _queues_lock:
            _queues[training_id] = queue
        
        # Registrar esta cola para limpieza posterior
        with _all_queues_lock:
            # Usar weakref para permitir que la cola sea recolectada cuando no hay referencias fuertes
            _all_queues.append(weakref.ref(queue))
        
        if DEBUG_IPC:
            print(f"[IPC] Nueva cola creada para training_id={training_id} ({id(queue)})")
        return queue
    except Exception as e:
        print(f"[IPC] Error al crear cola: {str(e)}")
        traceback.print_exc()
        return None

def clear_queue_for_training(training_id):
    """Limpia la cola de un entrenamiento para liberar recursos"""
    if training_id in _queues:
        debug_trace(f"Limpiando cola para training_id={training_id}")
        # Vaciar la cola primero para evitar bloqueos
        queue = _queues[training_id]
        items_removed = 0
        while not queue.empty():
            try:
                queue.get_nowait()
                items_removed += 1
            except:
                break
        debug_trace(f"Eliminados {items_removed} elementos de la cola para training_id={training_id}")
        del _queues[training_id]
        debug_trace(f"Cola eliminada para training_id={training_id}")
    else:
        debug_trace(f"No se encontró cola para limpiar: training_id={training_id}")

def add_update(training_id, update_data, timeout=0.5):
    """Añade una actualización a la cola IPC y además al cache"""
    # También guardar en cache para respaldo
    try:
        from django.core.cache import cache
        
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key)
        
        if config:
            if 'updates' not in config:
                config['updates'] = []
            
            # Añadir timestamp si no existe
            if 'timestamp' not in update_data:
                update_data['timestamp'] = time.time()
            
            config['updates'].append(update_data)
            # Limitar a 200 actualizaciones para no sobrecargar la caché
            if len(config['updates']) > 200:
                config['updates'] = config['updates'][-200:]
                
            cache.set(config_key, config, 7200)  # 2 horas
            
            # Guardar una copia separada para los logs de época
            if update_data.get('is_epoch_log') and update_data.get('epoch_number'):
                epoch_num = update_data.get('epoch_number')
                cache.set(
                    f'epoch_log_{training_id}_{epoch_num}', 
                    update_data,
                    3600  # 1 hora
                )
    except Exception as e:
        print(f"Error al guardar en cache: {e}")
        traceback.print_exc()
    
    # Intentar añadir a la cola IPC con timeout
    try:
        q = get_queue_for_training(training_id)
        if q:
            # Verificar que la cola no esté llena
            if q.qsize() < 100:  # Limitar tamaño de cola
                try:
                    q.put(update_data, timeout=timeout)
                    return True
                except queue.Full:
                    print(f"[IPC] Cola llena para training_id={training_id}")
                    return False
            else:
                # Cola demasiado grande, no añadir más elementos
                return False
    except Exception as e:
        print(f"Error al enviar a cola IPC: {e}")
        traceback.print_exc()
        
    return False

def send_update(training_id, data):
    """Envía una actualización a la cola de un entrenamiento específico"""
    try:
        queue = get_queue_for_training(training_id)
        if queue:
            # Asegurar que tenemos un timestamp si no está presente
            if isinstance(data, dict) and 'timestamp' not in data:
                data['timestamp'] = time.time()
            
            # Modo fallback o multiprocessing según corresponda
            if USE_FALLBACK:
                queue.put(data, block=False)  # No-blocking para Queue de threading
            else:
                queue.put(data)  # Blocking para multiprocessing.Queue
            return True
        return False
    except Exception as e:
        print(f"[IPC] Error al enviar actualización: {str(e)}")
        traceback.print_exc()
        return False

def get_updates(training_id, timeout=0.1, max_updates=10):
    """
    Obtiene actualizaciones de la cola, con un timeout para no bloquear
    y un límite máximo de actualizaciones para evitar sobrecargar
    """
    updates = []
    try:
        queue = get_queue_for_training(training_id)
        if not queue:
            return updates
            
        # Intentar obtener hasta max_updates o hasta que la cola esté vacía
        for _ in range(max_updates):
            try:
                if USE_FALLBACK:
                    # En modo fallback usar get_nowait de Queue de threading
                    try:
                        update = queue.get_nowait()
                        updates.append(update)
                    except queue_module.Empty:
                        break  # No hay más actualizaciones
                else:
                    # En modo normal usar get_nowait de multiprocessing.Queue
                    update = queue.get_nowait()
                    updates.append(update)
            except:
                # No hay más actualizaciones o timeout
                break
                
    except Exception as e:
        print(f"[IPC] Error al obtener actualizaciones: {str(e)}")
        traceback.print_exc()
    
    return updates

def dump_queue_status():
    """Devuelve un diccionario con el estado actual de las colas"""
    with _queues_lock:
        status = {}
        for training_id, queue in _queues.items():
            if queue:
                try:
                    status[training_id] = {
                        'id': id(queue),
                        'size': queue.qsize() if hasattr(queue, 'qsize') else 'unknown',
                        'empty': queue.empty() if hasattr(queue, 'empty') else 'unknown'
                    }
                except:
                    status[training_id] = {
                        'id': id(queue),
                        'error': 'Error al obtener información de la cola'
                    }
        return status

def close_queue(training_id):
    """Cierra una cola específica y la elimina del diccionario"""
    global _queues
    
    with _queues_lock:
        if training_id in _queues and _queues[training_id]:
            try:
                queue = _queues[training_id]
                
                # Verificar si la cola ya está cerrada antes de intentar vaciarla
                try:
                    # Intento controlado para detectar si la cola ya está cerrada
                    is_closed = False
                    try:
                        is_empty = queue.empty()  # Esto fallará si ya está cerrada
                    except (OSError, IOError, ValueError) as e:
                        if "handle is closed" in str(e) or "Bad file descriptor" in str(e):
                            is_closed = True
                        else:
                            raise  # Re-lanzar si es otro tipo de error
                    
                    # Solo intentar vaciar si la cola no está cerrada
                    if not is_closed:
                        # Vaciar la cola con timeout para evitar bloqueos
                        timeout_counter = 0
                        max_timeout = 2.0  # Máximo 2 segundos intentando vaciar
                        start_time = time.time()
                        
                        while not queue.empty() and (time.time() - start_time) < max_timeout:
                            try:
                                queue.get_nowait()
                            except Exception as e:
                                print(f"[IPC] Advertencia al vaciar cola: {str(e)}")
                                # Si hay un error al obtener, mejor salir del bucle
                                break
                except Exception as empty_error:
                    print(f"[IPC] No se pudo verificar/vaciar la cola: {str(empty_error)}")
                
                # Cerrar la cola de manera segura
                try:
                    # Primero intenta join_thread que es más seguro
                    if hasattr(queue, 'join_thread') and callable(getattr(queue, 'join_thread')):
                        try:
                            queue.join_thread()
                            print(f"[IPC] join_thread() ejecutado para cola {training_id}")
                        except Exception as join_error:
                            print(f"[IPC] Error en join_thread: {str(join_error)}")
                    
                    # Luego intenta close que podría fallar si ya está cerrada
                    if hasattr(queue, 'close') and callable(getattr(queue, 'close')):
                        try:
                            queue.close()
                            print(f"[IPC] close() ejecutado para cola {training_id}")
                        except Exception as close_error:
                            if "handle is closed" in str(close_error):
                                print(f"[IPC] La cola ya estaba cerrada: {training_id}")
                            else:
                                print(f"[IPC] Error en close: {str(close_error)}")
                    
                    # Finalmente _close como último recurso
                    if hasattr(queue, '_close') and callable(getattr(queue, '_close')):
                        try:
                            queue._close()
                            print(f"[IPC] _close() ejecutado para cola {training_id}")
                        except Exception as _close_error:
                            print(f"[IPC] Error en _close: {str(_close_error)}")
                except Exception as close_process_error:
                    print(f"[IPC] Error durante el proceso de cierre: {str(close_process_error)}")
                
                # Asegurar que la referencia se elimine del diccionario en cualquier caso
                try:
                    del _queues[training_id]
                    print(f"[IPC] Cola para training_id={training_id} eliminada del diccionario")
                    return True
                except Exception as del_error:
                    print(f"[IPC] Error al eliminar cola del diccionario: {str(del_error)}")
                    return False
            except Exception as e:
                print(f"[IPC] Error general al cerrar cola: {str(e)}")
                traceback.print_exc()
                
                # Aún intentamos eliminarla del diccionario como último recurso
                try:
                    del _queues[training_id]
                    print(f"[IPC] Cola para {training_id} eliminada después de error")
                except:
                    pass
                    
                return False
    return False

def clean_up_queues():
    """Limpia todas las colas y libera recursos"""
    global _queues, _all_queues
    
    print("[IPC] Limpiando colas y recursos...")
    
    # Si estamos en modo fallback, simplemente limpiar el diccionario
    if USE_FALLBACK:
        if '_fallback_queues' in globals():
            _fallback_queues.clear()
            print("[IPC] Limpieza de queues fallback completada")
        return
    
    # Modo normal con multiprocessing
    # Cerrar todas las colas en el diccionario
    with _queues_lock:
        training_ids = list(_queues.keys())  # Crear copia para evitar modificar durante iteración
        for training_id in training_ids:
            try:
                close_queue(training_id)
            except Exception as e:
                print(f"[IPC] Error al cerrar cola {training_id}: {str(e)}")
    
    # Limpiar referencias débiles a las colas
    try:
        with _all_queues_lock:
            alive_queues = []
            for queue_ref in _all_queues:
                queue = queue_ref()
                if queue is not None:
                    try:
                        # Evitamos operaciones potencialmente peligrosas
                        # Solo conservar la referencia si aún es válida
                        alive_queues.append(queue_ref)
                    except Exception as e:
                        print(f"[IPC] Error al procesar referencia débil: {str(e)}")
            
            # Actualizar la lista con solo las colas que aún existen
            _all_queues = alive_queues
            
        # Forzar la recolección de basura
        gc.collect()
    except Exception as e:
        print(f"[IPC] Error durante la limpieza de referencias débiles: {str(e)}")
    
    # Verificar estado final
    queue_count = 0
    with _queues_lock:
        queue_count = len(_queues)
    
    print(f"[IPC] Limpieza completa. Quedan {queue_count} colas en el diccionario y {len(_all_queues)} en la lista de colas.")

# Registrar la función de limpieza para que se ejecute al finalizar
atexit.register(clean_up_queues)

# También registrar limpieza de Manager si está activo
if _manager and not USE_FALLBACK:
    atexit.register(_manager.shutdown)
