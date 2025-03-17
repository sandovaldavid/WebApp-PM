import os
import sys
import json
import glob
import numpy as np
import joblib
import traceback
from datetime import datetime

# Añadir la importación faltante
from django.contrib.auth.decorators import login_required

def generate_evaluation_files(request):
    """Genera archivos de evaluación para un modelo existente"""
    model_status = check_model_files()
    
    if not model_status['all_present']:
        return {
            'success': False,
            'message': f'Faltan archivos necesarios: {", ".join(model_status["missing_files"])}'
        }
    
    try:
        # Importar el evaluador
        from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator
        from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
        import joblib
        import numpy as np
        
        # Rutas de archivos
        models_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')
        
        # Cargar el modelo
        estimator = AdvancedRNNEstimator.load(models_dir, 'tiempo_estimator')
        
        # Cargar feature_dims
        feature_dims = joblib.load(os.path.join(models_dir, 'feature_dims.pkl'))
        
        # Cargar datos de validación
        X_val = np.load(os.path.join(models_dir, 'X_val.npy'))
        y_val = np.load(os.path.join(models_dir, 'y_val.npy'))
        
        # Crear el evaluador
        evaluator = ModelEvaluator(estimator, feature_dims, models_dir)
        
        # Realizar evaluación completa
        metrics, _ = evaluator.evaluate_model(X_val, y_val)
        
        # Generar gráficos de evaluación
        evaluator.plot_predictions(y_val, estimator.predict(X_val, feature_dims))
        
        # Generar análisis de importancia de características
        feature_names = [
            'Complejidad', 'Cantidad_Recursos', 'Carga_Trabajo_R1', 
            'Experiencia_R1', 'Carga_Trabajo_R2', 'Experiencia_R2', 
            'Carga_Trabajo_R3', 'Experiencia_R3', 'Experiencia_Equipo', 
            'Claridad_Requisitos', 'Tamaño_Tarea'
        ]
        
        # Añadir nombres para características categóricas
        for i in range(feature_dims['tipo_tarea']):
            feature_names.append(f'Tipo_Tarea_{i+1}')
        for i in range(feature_dims['fase']):
            feature_names.append(f'Fase_{i+1}')
            
        evaluator.analyze_feature_importance(X_val, y_val, feature_names)
        
        # Realizar evaluación segmentada
        segments = {
            'pequeñas': lambda y: y <= 10,
            'medianas': lambda y: (y > 10) & (y <= 30),
            'grandes': lambda y: y > 30
        }
        evaluator.segmented_evaluation(X_val, y_val, segments)
        
        return {
            'success': True,
            'message': 'Archivos de evaluación generados correctamente.'
        }
        
    except Exception as e:
        import traceback
        return {
            'success': False,
            'message': f'Error: {str(e)}',
            'traceback': traceback.format_exc()
        }

def check_model_files():
    """Verifica si existen todos los archivos necesarios del modelo"""
    required_files = [
        os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'tiempo_estimator_model.keras'),
        os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'metrics_history.json'),
        os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'feature_dims.pkl')
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    return {
        'all_present': len(missing_files) == 0,
        'missing_files': missing_files
    }

def run_manual_evaluation():
    """Ejecuta evaluación manual del modelo y genera todos los archivos necesarios"""
    try:
        # Configurar backend no interactivo
        import matplotlib
        matplotlib.use('Agg')
        os.environ['MPLBACKEND'] = 'Agg'
        
        # Ejecutar la generación de archivos
        from .estimacion_tiempo.run_evaluation import run_manual_evaluation as run_eval
        success = run_eval()
        
        return {
            'success': success,
            'message': 'Evaluación manual completada exitosamente' if success else 'Error durante la evaluación manual'
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error durante la evaluación manual: {str(e)}'
        }
    finally:
        import matplotlib.pyplot as plt
        import gc
        plt.close('all')
        gc.collect()  # Opcional: forzar recolección de basura

def get_model_status():
    """Obtiene el estado actual del modelo y sus métricas"""
    result = {
        'status': 'error',
        'message': 'No se pudo determinar el estado del modelo'
    }
    
    try:
        # Verificar si existe el modelo
        model_path = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'tiempo_estimator_model.keras')
        metrics_path = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models', 'metrics_history.json')
        
        if not os.path.exists(model_path):
            return {
                'status': 'warning',
                'message': 'Modelo no encontrado'
            }
        
        # Obtener fecha de modificación del modelo
        model_modified = os.path.getmtime(model_path)
        
        # Obtener métricas más recientes
        metrics = None
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                try:
                    metrics_data = json.load(f)
                    if isinstance(metrics_data, list) and metrics_data:
                        latest_metrics = metrics_data[-1]
                        metrics = latest_metrics.get('metrics', latest_metrics)
                    elif isinstance(metrics_data, dict):
                        metrics = metrics_data.get('metrics', metrics_data)
                except json.JSONDecodeError:
                    pass
        
        result = {
            'status': 'success',
            'model_exists': True,
            'last_modified': model_modified,
            'last_modified_date': os.path.getmtime(model_path),
            'metrics': metrics
        }
        
    except Exception as e:
        import traceback
        result['message'] = str(e)
        result['traceback'] = traceback.format_exc()
    
    return result

@login_required
def generar_archivos_evaluacion(request):
    """Vista para generar archivos de evaluación para un modelo existente"""
    if request.method == 'POST':
        try:
            # Usar la función utilitaria para generar los archivos
            from .views_utils import generate_evaluation_files, check_model_files
            
            # Primero verificar si existen los archivos necesarios
            model_check = check_model_files()
            if not model_check['all_present']:
                return JsonResponse({
                    'success': False,
                    'message': f'Faltan archivos necesarios: {", ".join(model_check["missing_files"][:3])}'
                })
            
            # Generar archivos
            result = generate_evaluation_files(request)
            return JsonResponse(result)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error al generar archivos de evaluación: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Método no permitido.'
    })

def send_log_event(message, level="info"):
    """Formatea un evento SSE de tipo 'log'"""
    data = json.dumps({"message": message, "level": level})
    return f"event: log\ndata: {data}\n\n"

def send_epoch_event(message, level="info", epoch_num=None):
    """Formatea un evento SSE específico para épocas"""
    data = json.dumps({"message": message, "level": level, "epoch": epoch_num})
    event_id = f"epoch_{epoch_num}" if epoch_num else None
    if event_id:
        return f"event: epoch\nid: {event_id}\ndata: {data}\n\n"
    else:
        return f"event: epoch\ndata: {data}\n\n"
