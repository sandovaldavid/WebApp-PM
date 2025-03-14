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

class TaskStatus:
    """Estados posibles de una tarea"""
    PENDING = 'pending'
    RUNNING = 'running'
    COMPLETED = 'completed'
    FAILED = 'failed'

class AsyncTask:
    """Implementación mejorada de tareas asíncronas usando procesos en lugar de hilos"""
    
    def __init__(self, target_func, name=None):
        """
        Inicializa una nueva tarea asíncrona
        
        Args:
            target_func: Función objetivo a ejecutar
            name: Nombre descriptivo para la tarea
        """
        self.target_func = target_func
        self.name = name or target_func.__name__
        
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
    
    def _process_wrapper(self, task_id, args, kwargs, result_queue):
        """Wrapper para ejecutar una función en un proceso separado y capturar excepciones"""
        try:
            # Registrar inicio
            if task_id in _ACTIVE_TASKS:
                _ACTIVE_TASKS[task_id]['status'] = TaskStatus.RUNNING
                _ACTIVE_TASKS[task_id]['start_time'] = datetime.now()
            
            # Ejecutar la función objetivo
            result = self.target_func(*args, **kwargs)
            
            # Registrar finalización exitosa
            if task_id in _ACTIVE_TASKS:
                _ACTIVE_TASKS[task_id]['status'] = TaskStatus.COMPLETED
                _ACTIVE_TASKS[task_id]['end_time'] = datetime.now()
            
            # Devolver resultado
            result_queue.put((True, result))
            
        except Exception as e:
            error_traceback = traceback.format_exc()
            self._error_handler(task_id, e, error_traceback)
            result_queue.put((False, str(e)))
    
    def delay(self, *args, **kwargs):
        """
        Ejecuta la tarea en un proceso separado
        Similar a la interfaz de Celery para facilitar migración futura
        
        Returns:
            AsyncResult: Objeto que simula AsyncResult de Celery
        """
        task_id = str(uuid.uuid4())
        result_queue = Queue()
        
        # Registrar la nueva tarea
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
            args=(task_id, args, kwargs, result_queue)
        )
        process.daemon = True
        
        # Almacenar proceso para posible cancelación
        _ACTIVE_TASKS[task_id]['process'] = process
        
        # Iniciar proceso
        process.start()
        
        # Retornar objeto similar a AsyncResult de Celery
        return AsyncResult(task_id, process, result_queue)

class AsyncResult:
    """Simulación simplificada de AsyncResult de Celery"""
    
    def __init__(self, task_id, process, result_queue):
        self.id = task_id
        self.process = process
        self.result_queue = result_queue
    
    def ready(self):
        """Verifica si la tarea ha terminado"""
        if not self.process.is_alive():
            return True
        return not self.result_queue.empty()
    
    def get(self, timeout=None, propagate=True):
        """Obtiene el resultado de la tarea, esperando si es necesario"""
        if not self.ready() and timeout:
            start_time = time.time()
            while not self.ready() and (time.time() - start_time < timeout):
                time.sleep(0.1)
                
        if not self.ready():
            raise TimeoutError("La tarea no ha terminado en el tiempo especificado")
            
        success, result = self.result_queue.get()
        if not success and propagate:
            raise RuntimeError(result)
        return result
    
    def cancel(self):
        """Cancela la tarea si sigue en ejecución"""
        if self.process.is_alive():
            self.process.terminate()
            if self.id in _ACTIVE_TASKS:
                _ACTIVE_TASKS[self.id]['status'] = 'cancelled'
                _ACTIVE_TASKS[self.id]['end_time'] = datetime.now()
            return True
        return False

# Crear objetos de tarea para las funciones que necesitan ejecutarse de forma asíncrona
start_training_process = AsyncTask(ejecutar_entrenamiento, name="entrenamiento_modelo")

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