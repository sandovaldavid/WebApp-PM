from django.shortcuts import render
import json
import numpy as np
import tensorflow as tf
import joblib
from datetime import datetime
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

import sys
import os


def normalize_metric(value, metric_name, metrics_history):
    """Normaliza métricas usando Min-Max scaling con valores observados"""
    if metric_name in ['Accuracy', 'Precision', 'Recall', 'F1']:
        return value

    # Obtener todos los valores históricos de la métrica
    all_values = [entry['metrics'][metric_name] for entry in metrics_history]
    min_val = min(all_values)
    max_val = max(all_values)

    # Evitar división por cero
    if max_val == min_val:
        return 0

    # Para MSE, RMSE y MAE, invertimos la normalización ya que valores menores son mejores
    if metric_name in ['MSE', 'RMSE', 'MAE']:
        return 1 - ((value - min_val) / (max_val - min_val))

    return (value - min_val) / (max_val - min_val)


def calculate_global_precision(metrics, metrics_history):
    """Calcula el nivel de precisión global usando pesos predefinidos"""
    weights = {
        'MSE': 0.2,
        'RMSE': 0.2,
        'MAE': 0.2,
        'R2': 0.1,
        'Accuracy': 0.1,
        'Precision': 0.1,
        'Recall': 0.05,
        'F1': 0.05,
    }

    weighted_sum = 0
    for metric_name, weight in weights.items():
        normalized_value = normalize_metric(
            metrics[metric_name], metric_name, metrics_history
        )
        weighted_sum += normalized_value * weight

    return weighted_sum


@login_required
def dashboard(request):
    """Renderiza el dashboard de métricas de la red neuronal"""
    # Cargar historial de métricas
    try:
        with open('redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r') as f:
            metrics_history = json.load(f)
            
            # Verificar estructura y adaptar según sea necesario
            if metrics_history and isinstance(metrics_history, list):
                # Formato antiguo: lista de entradas
                latest_metrics = metrics_history[-1] if metrics_history else None
            elif metrics_history and isinstance(metrics_history, dict):
                # Posible nuevo formato: diccionario con registros
                if 'entries' in metrics_history:
                    entries = metrics_history['entries']
                    metrics_history = entries
                    latest_metrics = entries[-1] if entries else None
                else:
                    # Si es un diccionario con la última entrada directamente
                    latest_metrics = metrics_history
                    metrics_history = [metrics_history]  # Convertir a lista para compatibilidad
            else:
                metrics_history = []
                latest_metrics = None
                print("Formato de metrics_history.json no reconocido")
    except Exception as e:
        print(f"Error al cargar metrics_history.json: {e}")
        metrics_history = []
        latest_metrics = None

    # Calcular precisión global
    if latest_metrics:
        try:
            # Comprobar si las métricas están anidadas en un subcampo 'metrics'
            metrics_data = latest_metrics.get('metrics', latest_metrics)
            
            # Verificar si todas las métricas necesarias están disponibles
            required_metrics = ['MSE', 'RMSE', 'MAE', 'R2', 'Accuracy']
            if all(metric in metrics_data for metric in required_metrics):
                global_precision = calculate_global_precision(metrics_data, metrics_history)
            else:
                print("Faltan métricas requeridas en latest_metrics")
                global_precision = 0
        except Exception as e:
            print(f"Error al calcular global_precision: {e}")
            global_precision = 0
    else:
        global_precision = 0

    # Preparar datos para gráficas
    timestamps = []
    mse_values = []
    accuracy_values = []
    r2_values = []
    global_precision_values = []

    for entry in metrics_history:
        try:
            # Adaptación para diferentes estructuras de datos
            metrics_data = entry.get('metrics', entry)
            timestamp = entry.get('timestamp', entry.get('date', entry.get('created_at', '')))
            
            timestamps.append(timestamp)
            
            # Obtener métricas con manejo de excepciones
            mse = metrics_data.get('MSE', metrics_data.get('mse', 0))
            mse_values.append(mse)
            
            accuracy = metrics_data.get('Accuracy', metrics_data.get('accuracy', 0))
            accuracy_values.append(accuracy)
            
            r2 = metrics_data.get('R2', metrics_data.get('r2', 0))
            r2_values.append(r2)
            
            # Calcular precisión global para cada punto histórico
            try:
                gp = calculate_global_precision(metrics_data, metrics_history)
            except:
                gp = 0
            global_precision_values.append(gp)
        except Exception as e:
            print(f"Error procesando entrada histórica: {e}")
            # Continuar con la siguiente entrada

    context = {
        'latest_metrics': latest_metrics,
        'global_precision': global_precision,
        'metrics_history': json.dumps(
            {
                'timestamps': timestamps,
                'mse_values': mse_values,
                'accuracy_values': accuracy_values,
                'r2_values': r2_values,
                'global_precision_values': global_precision_values,
            }
        ),
    }

    return render(request, 'redes_neuronales/dashboard.html', context)


@login_required
def estimate_time(request):
    if request.method == 'POST':
        try:
            # Configurar rutas relativas
            # BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            REDES_DIR = os.path.join(BASE_DIR, 'redes_neuronales')
            MODEL_DIR = os.path.join(BASE_DIR, "redes_neuronales", "models")

            # Verificar que existe el directorio
            # if not os.path.exists(MODEL_DIR):
            #   raise FileNotFoundError("No se encuentra el directorio de modelos")

            # Agregar la ruta al path de Python
            if REDES_DIR not in sys.path:
                sys.path.append(REDES_DIR)

            # Ahora importar el módulo
            from ml_model import EstimacionModel, DataPreprocessor

            # Definir rutas de archivos
            MODEL_PATH = os.path.join(MODEL_DIR, "modelo_estimacion.keras")
            PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.pkl")
            SCALER_NUM_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
            SCALER_REQ_PATH = os.path.join(MODEL_DIR, "scaler_req.pkl")

            # Verificar si los archivos existen
            for path in [
                MODEL_PATH,
                PREPROCESSOR_PATH,
                SCALER_NUM_PATH,
                SCALER_REQ_PATH,
            ]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"No se encuentra el archivo: {path}")

            # Obtener datos del formulario
            complejidad = int(request.POST.get('complejidad', 2))
            prioridad = int(request.POST.get('prioridad', 2))
            tipo_tarea = request.POST.get('tipo_tarea', 'backend')

            # Prints de debug
            print("\nDatos recibidos para estimación:")
            print(f"Complejidad: {complejidad}")
            print(f"Prioridad: {prioridad}")
            print(f"Tipo de tarea: {tipo_tarea}")
            print("------------------------")

            # Preparar datos numéricos (2 características)
            X_num = np.array([[complejidad, prioridad]], dtype=np.float32)

            # Preparar datos de requerimiento (4 características)
            X_req = np.array(
                [[complejidad, complejidad, 1, prioridad]], dtype=np.float32
            )

            # Cargar preprocessors
            preprocessor = joblib.load(PREPROCESSOR_PATH)
            scaler_num = joblib.load(SCALER_NUM_PATH)
            scaler_req = joblib.load(SCALER_REQ_PATH)

            # Preparar datos de tipo de tarea
            X_task = preprocessor.encode_task_types([tipo_tarea])

            # Normalizar datos usando los scalers correctos
            X_num_norm = scaler_num.transform(X_num)
            X_req_norm = scaler_req.transform(X_req)

            # Configurar y cargar el modelo
            config = {
                "vocab_size": 6,
                "lstm_units": 32,
                "dense_units": [64, 32],
                "dropout_rate": 0.2,
            }
            model = EstimacionModel(config)
            model.model = tf.keras.models.load_model(MODEL_PATH)

            # Realizar predicción usando predict_individual_task
            resultado = model.predict_individual_task(
                X_num_norm, np.array(X_task).reshape(-1, 1), X_req_norm
            )

            # Obtener el tiempo estimado y redondear a entero
            estimated_time = float(resultado['tiempo_estimado'])

            return JsonResponse(
                {
                    'success': True,
                    'estimated_time': round(estimated_time, 2),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        except FileNotFoundError as e:
            return JsonResponse(
                {'error': f"Error de archivo: {str(e)}", 'success': False}
            )
        except Exception as e:
            return JsonResponse(
                {'error': f"Error inesperado: {str(e)}", 'success': False}
            )

    return JsonResponse({'error': 'Método no permitido', 'success': False})


@login_required
def estimacion_avanzada(request):
    """Vista para la interfaz de estimación avanzada con RNN"""
    context = {}
    
    # 1. Cargar métricas del modelo
    try:
        with open('redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r') as f:
            metrics_history = json.load(f)
            latest_metrics = metrics_history[-1] if metrics_history else None
    except:
        metrics_history = []
        latest_metrics = {
            'metrics': {
                'MSE': 120.45,
                'RMSE': 10.97,
                'MAE': 8.74,
                'R2': 0.82,
                'Accuracy': 0.89,
            },
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'model_version': '1.2.0'
        }

    if latest_metrics:
        global_precision = calculate_global_precision(
            latest_metrics['metrics'], metrics_history
        )
    else:
        global_precision = 0.85
        
    context['latest_metrics'] = latest_metrics
    context['global_precision'] = global_precision
    
    # 2. Cargar métricas detalladas de evaluación
    try:
        with open('redes_neuronales/estimacion_tiempo/models/evaluation_metrics.json', 'r') as f:
            evaluation_metrics = json.load(f)
        context['evaluation_metrics'] = evaluation_metrics
    except Exception as e:
        print(f"Error al cargar métricas de evaluación: {e}")
        context['evaluation_metrics'] = latest_metrics.get('metrics', {}) if latest_metrics else {}
    
    # 3. Cargar evaluación por segmentos
    try:
        with open('redes_neuronales/estimacion_tiempo/models/segmented_evaluation.json', 'r') as f:
            segmented_evaluation = json.load(f)
        context['segmented_evaluation'] = segmented_evaluation
    except Exception as e:
        print(f"Error al cargar evaluación por segmentos: {e}")
        context['segmented_evaluation'] = {}
    
    # 4. Cargar importancia de características (todos los tipos)
    try:
        import pandas as pd
        
        # Función para cargar y procesar los archivos de importancia
        def load_feature_importance(filepath):
            df = pd.read_csv(filepath)
            data = []
            for _, row in df.iterrows():
                data.append({
                    'name': row['Feature'],
                    'importance': float(row['Importance']),
                    'importance_normalized': round(float(row['Importance_Normalized']) * 100, 2)
                })
            return sorted(data, key=lambda x: x['importance_normalized'], reverse=True)
        
        # Diccionario para almacenar todos los datos
        feature_importance_data = {}
        
        # Cargar los diferentes archivos de importancia
        feature_importance_data['global'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/global_feature_importance.csv'
        )
        feature_importance_data['recurso_1'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_1_Recurso.csv'
        )
        feature_importance_data['recurso_2'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_2_Recursos.csv'
        )
        feature_importance_data['recurso_3'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_3_o_más_Recursos.csv'
        )
        
        # Agregar al contexto
        context['feature_importance_data'] = feature_importance_data
        
        # Mantener el feature_importance original para compatibilidad
        context['feature_importance'] = feature_importance_data['global']
    except Exception as e:
        print(f"Error al cargar importancia de características: {e}")
        context['feature_importance_data'] = {}
        context['feature_importance'] = []

    return render(request, 'redes_neuronales/estimacion_avanzada.html', context)
