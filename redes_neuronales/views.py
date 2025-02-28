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
    # Cargar historial de métricas
    try:
        with open('redes_neuronales/models/metrics_history.json', 'r') as f:
            metrics_history = json.load(f)
            latest_metrics = metrics_history[-1] if metrics_history else None
    except:
        metrics_history = []
        latest_metrics = None

    if latest_metrics:
        global_precision = calculate_global_precision(
            latest_metrics['metrics'], metrics_history
        )
    else:
        global_precision = 0

    # Preparar datos para gráficas
    timestamps = []
    mse_values = []
    accuracy_values = []
    r2_values = []
    global_precision_values = []

    for entry in metrics_history:
        timestamps.append(entry['timestamp'])
        mse_values.append(entry['metrics']['MSE'])
        accuracy_values.append(entry['metrics']['Accuracy'])
        r2_values.append(entry['metrics']['R2'])
        global_precision_values.append(
            calculate_global_precision(entry['metrics'], metrics_history)
        )

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
