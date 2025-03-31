"""
Este archivo define tareas asíncronas que pueden ejecutarse con Celery
o con procesos separados según la configuración.

Mejoras implementadas:
- Uso de procesos en lugar de hilos para superar limitaciones del GIL
- Mejor manejo de errores con registro detallado
- Sistema de seguimiento de tareas activas
- Compatibilidad con la interfaz de Celery para migración futura
- Soporte para cancelación y verificación de estado
"""

import os
import sys
import time
import uuid
import traceback
import logging
from multiprocessing import Process, Queue
from datetime import datetime

from django.utils import timezone
from django.core.cache import cache

# Configuración de logging
logger = logging.getLogger(__name__)

# Importar funciones de entrenamiento
from .entrenamiento_utils import ejecutar_entrenamiento

# Almacenamiento global para tareas activas
_ACTIVE_TASKS = {}

# Diccionario para rastrear procesos activos
active_processes = {}

def cleanup_processes():
    """Función para limpiar procesos al apagar el servidor"""
    for pid, process in list(active_processes.items()):
        if process.is_alive():
            try:
                os.kill(pid, signal.SIGTERM)
                print(f"Proceso {pid} terminado durante la limpieza")
            except:
                pass

# Registrar función de limpieza para ejecutarla al apagar
atexit.register(cleanup_processes)

class TaskStatus:
    """Estados posibles de una tarea"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

class AsyncTask:
    """Implementación mejorada de tareas asíncronas usando procesos en lugar de hilos"""
    
    def __init__(self, target_func=None, name=None):
        """
        Inicializa una nueva tarea asíncrona
        
        Args:
            target_func: Función objetivo a ejecutar
            name: Nombre descriptivo para la tarea
        """
        self.target_func = target_func
        self.name = name or (target_func.__name__ if target_func else "async_task")
        self.active_tasks = {}
        self.results = {}
        
    def _error_handler(self, task_id, error, traceback_str):
        """Maneja errores de tareas en procesos separados"""
        logger.error(f"Error en tarea {task_id} ({self.name}): {error}\n{traceback_str}")
        
        if task_id in _ACTIVE_TASKS:
            _ACTIVE_TASKS[task_id]['status'] = TaskStatus.FAILED
            _ACTIVE_TASKS[task_id]['error'] = str(error)
            _ACTIVE_TASKS[task_id]['traceback'] = traceback_str
            _ACTIVE_TASKS[task_id]['end_time'] = datetime.now()
            
        # Actualizar el estado en cache para la interfaz web
        config_key = f'training_config_{task_id}'
        config = cache.get(config_key)
        if config:
            config['status'] = 'failed'
            config['error'] = str(error)
            cache.set(config_key, config, 7200)  # 2 horas
    
    def _process_wrapper(self, task_id, args, kwargs):
        """Función wrapper que se ejecuta en el proceso hijo"""
        try:
            import os
            from .debug_utils import trace_log
            
            # Registrar inicio con diagnóstico detallado
            trace_log(f"Proceso hijo iniciado con PID={os.getpid()} para task_id={task_id}", 
                      category="PROCESS_START", include_stack=True)
                
            # Verificar el estado de registro
            if task_id in _ACTIVE_TASKS:
                _ACTIVE_TASKS[task_id]['status'] = TaskStatus.RUNNING
                _ACTIVE_TASKS[task_id]['start_time'] = datetime.now()
                trace_log(f"Task {task_id} marcada como RUNNING en _ACTIVE_TASKS", category="PROCESS_STATE")
            else:
                trace_log(f"¡ADVERTENCIA! Task {task_id} no encontrada en _ACTIVE_TASKS", category="PROCESS_WARNING")
                # Crearla si no existe
                _ACTIVE_TASKS[task_id] = {
                    'id': task_id,
                    'name': self.name,
                    'status': TaskStatus.RUNNING,
                    'create_time': datetime.now(),
                    'start_time': datetime.now()
                }
            
            # Verificar que tenemos la función objetivo
            if not self.target_func:
                raise ValueError(f"No se ha definido una función objetivo para la tarea {task_id}")
            
            trace_log(f"Ejecutando función {self.target_func.__name__} con args={args}", 
                      category="PROCESS_EXEC")
                
            # Ejecutar la función objetivo
            result = self.target_func(*args, **kwargs)
            
            # Registrar finalización exitosa
            if task_id in _ACTIVE_TASKS:
                _ACTIVE_TASKS[task_id]['status'] = TaskStatus.COMPLETED
                _ACTIVE_TASKS[task_id]['end_time'] = datetime.now()
            
            # Almacenar resultado y marcarlo como completado
            self.results[task_id] = {
                'status': 'completed',
                'result': result
            }
            
            # Señalizar que el proceso ha terminado
            send_update(task_id, {
                'type': 'process_complete',
                'task_id': task_id,
                'status': 'completed',
                'timestamp': time.time()
            })
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error en proceso {task_id}: {str(e)}\n{error_trace}")
            
            # Registrar el error con diagnóstico detallado
            trace_log(f"Error en proceso {task_id}: {str(e)}\n{error_trace}", 
                      category="PROCESS_ERROR", include_stack=True)
            
            # Registrar el error
            self.results[task_id] = {
                'status': 'error',
                'error': str(e),
                'traceback': error_trace
            }
            self._error_handler(task_id, e, error_trace)
            
            # Señalizar error
            send_update(task_id, {
                'type': 'process_error',
                'task_id': task_id,
                'error': str(e),
                'timestamp': time.time()
            })
    
    def delay(self, *args, **kwargs):
        """
        Ejecuta la tarea en un proceso separado
        Similar a la interfaz de Celery para facilitar migración futura
        
        Returns:
            AsyncResult: Objeto que simula AsyncResult de Celery
        """
        task_id = str(uuid.uuid4())
        
        # Registrar la nueva tarea con mejor diagnóstico
        from .debug_utils import trace_log
        trace_log(f"Creando nueva tarea asíncrona: id={task_id}, nombre={self.name}, función={self.target_func.__name__}", 
                category="TASK_CREATE")
        
        _ACTIVE_TASKS[task_id] = {
            'id': task_id,
            'name': self.name,
            'status': TaskStatus.PENDING,
            'create_time': datetime.now(),
            'start_time': None,
            'end_time': None,
            'args': args,
            'kwargs': kwargs
        }
        
        # Crear y iniciar el proceso
        process = Process(
            target=self._process_wrapper,
            args=(task_id, args, kwargs)
        )
        process.daemon = True
        
        # Almacenar proceso para posible cancelación
        _ACTIVE_TASKS[task_id]['process'] = process
        
        # Iniciar proceso con diagnóstico
        trace_log(f"Iniciando proceso para task_id={task_id}", category="TASK_START")
        process.start()
        
        # Verificar que realmente se inició
        if process.is_alive():
            trace_log(f"Proceso iniciado con éxito para task_id={task_id}, PID={process.pid}", 
                     category="TASK_START_SUCCESS")
        else:
            trace_log(f"ADVERTENCIA: El proceso parece no haber iniciado para task_id={task_id}", 
                     category="TASK_START_FAIL")
        
        # Registrar en el diccionario global para limpieza
        pid = process.pid
        active_processes[pid] = process
        
        # Retornar objeto similar a AsyncResult de Celery
        return AsyncResult(task_id, process)

    def start_task(self, func, *args, **kwargs):
        """Inicia una tarea asíncrona"""
        # Establecer la función objetivo si no está definida
        if not self.target_func and func:
            self.target_func = func
            
        # Generar ID único para la tarea (usar como training_id)
        task_id = str(uuid.uuid4())
        
        # Crear proceso
        process = Process(target=self._process_wrapper, 
                         args=(task_id, args, kwargs))
        process.daemon = True
        
        # Iniciar proceso
        process.start()
        
        # Registrar proceso
        self.active_tasks[task_id] = {
            'process': process,
            'pid': process.pid,
            'start_time': time.time(),
            'status': 'running'
        }
        
        # Registrar en el diccionario global para limpieza
        active_processes[process.pid] = process
        
        return task_id
    
    def get_task_status(self, task_id):
        """Obtiene el estado de una tarea"""
        if task_id in self.active_tasks:
            # Verificar si el proceso sigue vivo
            process = self.active_tasks[task_id]['process']
            if process.is_alive():
                return 'running'
            else:
                return self.results.get(task_id, {}).get('status', 'unknown')
        else:
            return 'not_found'
    
    def stop_task(self, task_id):
        """Detiene una tarea en ejecución"""
        if task_id in self.active_tasks:
            process = self.active_tasks[task_id]['process']
            pid = self.active_tasks[task_id]['pid']
            
            if process.is_alive():
                # Intentar terminar el proceso limpiamente
                try:
                    os.kill(pid, signal.SIGTERM)
                    process.join(5)  # Esperar 5 segundos
                    
                    # Si sigue vivo, forzar terminación
                    if process.is_alive():
                        os.kill(pid, signal.SIGKILL)
                        process.terminate()
                    
                    # Limpiar recursos
                    if pid in active_processes:
                        del active_processes[pid]
                    
                    # Limpiar cola de este entrenamiento
                    clear_queue_for_training(task_id)
                    
                    return True
                except Exception as e:
                    print(f"Error al detener tarea {task_id}: {str(e)}")
                    return False
            else:
                # El proceso ya terminó
                return True
        return False

class AsyncResult:
    """Simulación simplificada de AsyncResult de Celery"""
    
    def __init__(self, task_id, process):
        self.id = task_id
        self.process = process
    
    def ready(self):
        """Verifica si la tarea ha terminado"""
        if not self.process.is_alive():
            return True
        return False
    
    def get(self, timeout=None, propagate=True):
        """Obtiene el resultado de la tarea, esperando si es necesario"""
        if not self.ready() and timeout:
            start_time = time.time()
            while not self.ready() and (time.time() - start_time < timeout):
                time.sleep(0.1)
                
        if not self.ready():
            raise TimeoutError("La tarea no ha terminado en el tiempo especificado")
            
        if self.process.exitcode != 0 and propagate:
            raise RuntimeError(f"La tarea falló con código de salida {self.process.exitcode}")
        
        # Buscar el resultado en el diccionario global
        for task_manager in [task_manager]:
            if self.id in task_manager.results:
                result_data = task_manager.results[self.id]
                if result_data.get('status') == 'error' and propagate:
                    raise RuntimeError(result_data.get('error', 'Error desconocido'))
                return result_data.get('result')
        
        return None

# Crear instancia singleton para ser usada en toda la aplicación
task_manager = AsyncTask()

# Inicializar las tareas principales - importamos la función aquí para evitar la importación circular
def create_training_task():
    # Importar la función de entrenamiento aquí para evitar importación circular
    from .entrenamiento_utils import ejecutar_entrenamiento
    return AsyncTask(ejecutar_entrenamiento, name="entrenamiento_modelo")

# Crear la tarea para el entrenamiento
start_training_process = create_training_task()

# Funciones de utilidad para gestión de tareas
def get_task_status(task_id):
    """Obtiene el estado actual de una tarea"""
    return _ACTIVE_TASKS.get(task_id, {'status': 'unknown'})

def get_active_tasks():
    """Obtiene lista de tareas activas"""
    return {k: v for k, v in _ACTIVE_TASKS.items() 
            if v.get('status') in [TaskStatus.PENDING, TaskStatus.RUNNING]}

def cleanup_completed_tasks(max_age_hours=24):
    """Limpia tareas completadas antiguas"""
    current_time = datetime.now()
    keys_to_remove = []
    
    for task_id, task_info in _ACTIVE_TASKS.items():
        if task_info.get('status') in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
            end_time = task_info.get('end_time')
            if end_time and (current_time - end_time).total_seconds() > max_age_hours * 3600:
                keys_to_remove.append(task_id)
    
    for task_id in keys_to_remove:
        del _ACTIVE_TASKS[task_id]
    
    return len(keys_to_remove)