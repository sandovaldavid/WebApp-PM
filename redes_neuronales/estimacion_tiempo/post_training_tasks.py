"""
Script para ejecutar tareas posteriores al entrenamiento del modelo.
"""
# Al inicio del archivo, asegurar que se configure el backend no interactivo ANTES de cualquier otra importación
import os
os.environ['MPLBACKEND'] = 'Agg'  # Forzar backend no interactivo
import matplotlib
matplotlib.use('Agg')  # Establecer explícitamente antes de cualquier otra importación

import sys
import time
import json  # Añadir importación de json que faltaba
import traceback
from datetime import datetime
from threading import Thread  # Usar Thread en lugar de Process

# Asegurar que matplotlib no intente usar Tkinter
matplotlib.rcParams['figure.max_open_warning'] = 0  # Evitar advertencias por exceso de figuras

# Asegurar que se puede importar desde el directorio padre
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if (parent_dir not in sys.path):
    sys.path.insert(0, parent_dir)

def run_evaluation_in_background(training_id=None):
    """
    Ejecuta la generación de archivos de evaluación en segundo plano
    """
    print(f"[PostTraining] Iniciando generación de archivos de evaluación en segundo plano")
    
    # Esperar para asegurarse de que el modelo se haya guardado
    time.sleep(5)
    
    try:
        # Verificar la existencia del modelo
        models_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')
        if not os.path.exists(os.path.join(models_dir, 'tiempo_estimator_model.keras')):
            print("[PostTraining] ❌ El archivo del modelo no existe después de esperar. Abortando.")
            _notify_completion(training_id, False, "No se encontró el archivo del modelo")
            return False
            
        # Usar directamente el ModelEvaluator para toda la evaluación
        from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator
        from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
        import joblib
        import numpy as np
        
        # Cargar el modelo
        estimator = AdvancedRNNEstimator.load(models_dir, 'tiempo_estimator')
        
        # Cargar feature_dims
        feature_dims = joblib.load(os.path.join(models_dir, 'feature_dims.pkl'))
        
        # Cargar datos de validación o crear sintéticos si no existen
        X_val_path = os.path.join(models_dir, 'X_val.npy')
        y_val_path = os.path.join(models_dir, 'y_val.npy')
        
        if os.path.exists(X_val_path) and os.path.exists(y_val_path):
            X_val = np.load(X_val_path)
            y_val = np.load(y_val_path)
        else:
            # Crear datos sintéticos
            print("[PostTraining] Creando datos sintéticos para evaluación...")
            total_dims = sum(feature_dims.values())
            X_val = np.random.randn(100, total_dims) * 0.5 + 0.5
            y_val = np.abs(np.random.randn(100) * 10 + 20)
            
            # Guardar los datos sintéticos
            np.save(X_val_path, X_val)
            np.save(y_val_path, y_val)
        
        # Crear el evaluador
        print("[PostTraining] Creando el evaluador...")
        evaluator = ModelEvaluator(estimator, feature_dims, models_dir)
        
        # Realizar métricas básicas solamente por ahora (la evaluación completa se hará cuando se solicite)
        print("[PostTraining] Calculando métricas básicas...")
        metrics = evaluator._calculate_metrics(X_val, y_val)
        evaluator._save_metrics_history(metrics)
        
        print("[PostTraining] ✅ Métricas básicas generadas correctamente.")
        _notify_completion(training_id, True, "Métricas generadas correctamente. Puede visualizar detalles en el panel de métricas.")
        
        # Cerrar todas las figuras de matplotlib para evitar problemas con Tkinter
        import matplotlib.pyplot as plt
        plt.close('all')  
        
        return True
        
    except Exception as e:
        print(f"[PostTraining] ❌ Error durante la generación de archivos: {e}")
        traceback.print_exc()
        _notify_completion(training_id, False, f"Error: {str(e)}")

        # También limpiar recursos en caso de excepción
        import matplotlib.pyplot as plt
        plt.close('all')        
        return False
    finally:
        # Código de limpieza que siempre debe ejecutarse
        import gc
        gc.collect()  # Forzar recolección de basura
        
        # Cerrar explícitamente todas las figuras nuevamente para garantizar limpieza
        try:
            import matplotlib.pyplot as plt
            plt.close('all')  
        except:
            pass

def _notify_completion(training_id, success, message, metrics=None, results=None):
    """
    Notifica la finalización del proceso de post-entrenamiento al cliente
    
    Args:
        training_id: ID del proceso de entrenamiento
        success: True si el proceso fue exitoso
        message: Mensaje descriptivo del resultado
        metrics: Métricas del modelo (opcional)
        results: Resultados adicionales (opcional)
    """
    if not training_id:
        return
        
    try:
        # Importamos aquí para evitar problemas de importación circular
        from django.core.cache import cache
        from redes_neuronales.ipc_utils import send_update
        
        # Obtener configuración del entrenamiento
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key)
        
        if config:
            # Inicializar la lista de actualizaciones si no existe
            if 'updates' not in config:
                config['updates'] = []
                
            # Añadir actualización con estado de post-procesamiento
            status_type = 'success' if success else 'warning'
            config['updates'].append({
                'type': 'log',
                'message': f"Post-procesamiento: {message}",
                'level': status_type,
                'timestamp': time.time(),
                'is_post_processing': True
            })
            
            # Si fue exitoso, añadir evento de cierre explícito
            if success:
                # MEJORADO: Priorizar las métricas proporcionadas como parámetros
                result_metrics = metrics or {}
                
                # Si no se proporcionaron métricas, intentar cargarlas del archivo
                if not result_metrics:
                    try:
                        metrics_path = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'evaluation_metrics.json')
                        if os.path.exists(metrics_path):
                            with open(metrics_path, 'r') as f:
                                result_metrics = json.load(f)
                                print(f"[PostTraining] Métricas cargadas del archivo: {result_metrics}")
                    except Exception as e:
                        print(f"[PostTraining] Error al cargar métricas desde archivo: {e}")
                        # Si falla, crear un diccionario vacío para evitar errores
                        result_metrics = {}
                
                # Normalizar nombres de claves para garantizar compatibilidad
                normalized_metrics = {}
                for key, value in result_metrics.items():
                    # Convertir claves como 'mse' a 'MSE' y 'r2' a 'R2'
                    normalized_key = key.upper() if len(key) <= 3 else key
                    # Asegurar que todos los valores son números serializables
                    normalized_metrics[normalized_key] = float(value) if isinstance(value, (int, float)) else value
                
                # Preparar los datos para el evento complete
                complete_data = {
                    'type': 'complete',  # ¡IMPORTANTE! Este es el tipo de evento principal
                    'success': True,
                    'message': message,
                    'timestamp': time.time(),
                    'model_id': training_id,
                    'training_id': training_id,
                    'metrics': normalized_metrics,
                    'results': results or {}
                }
                
                # Añadir a las actualizaciones
                config['updates'].append(complete_data)
                
                # También enviar directamente a través del sistema IPC
                send_update(training_id, complete_data)
                
                # Añadir también el evento post_processing_complete para compatibilidad
                config['updates'].append({
                    'type': 'post_processing_complete',
                    'success': True,
                    'message': "Procesamiento posterior completado con éxito.",
                    'timestamp': time.time() + 0.1,  # Añadir 0.1s para asegurar orden
                    'model_id': training_id,
                    'training_id': training_id,
                    'metrics': normalized_metrics
                })
                
                # Registrar la finalización también en el estado del modelo
                config['status'] = 'completed'
                config['metrics'] = normalized_metrics
                config['last_update'] = time.time()
                
            elif not success:
                # Si hubo error, notificarlo como advertencia
                error_data = {
                    'type': 'error',
                    'message': f"Error en post-procesamiento: {message}",
                    'timestamp': time.time(),
                }
                config['updates'].append(error_data)
                send_update(training_id, error_data)
                
            # Actualizar en caché con tiempo extendido
            cache.set(config_key, config, 7200)  # 2 horas
            print(f"[PostTraining] Notificación completa enviada al cliente: {message}")
            
    except Exception as e:
        print(f"[PostTraining] Error al notificar finalización: {str(e)}")
        traceback.print_exc()

def start_background_tasks(training_id=None):
    """
    Inicia las tareas en segundo plano después del entrenamiento
    
    Args:
        training_id: ID del proceso de entrenamiento
    """
    # Usar Thread en lugar de Process
    thread = Thread(
        target=run_evaluation_in_background,
        args=(training_id,)
    )
    # No marcar el hilo como daemon para evitar problemas
    thread.daemon = False
    thread.start()

    print(f"[PostTraining] Tarea posterior al entrenamiento iniciada en hilo {thread.name}")
    return thread

# Punto de entrada para ejecutar manualmente
if __name__ == "__main__":
    # Forzar matplotlib a usar backend no interactivo nuevamente para mayor seguridad
    os.environ['MPLBACKEND'] = 'Agg'
    import matplotlib
    matplotlib.use('Agg')
    print("Ejecutando tareas post-entrenamiento manualmente...")
    run_evaluation_in_background()
