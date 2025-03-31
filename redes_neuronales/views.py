from django.shortcuts import render
import json
import numpy as np
import tensorflow as tf
import joblib
from datetime import datetime
from django.http import JsonResponse, StreamingHttpResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import sys
import os
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

import traceback

def normalize_metric(value, metric_name, metrics_history):
    """Normaliza métricas usando Min-Max scaling con valores observados"""
    try:
        # Recopilar todos los valores de esta métrica en el historial
        all_values = []
        for entry in metrics_history:
            # Manejar diferentes estructuras de datos
            if 'metrics' in entry and metric_name in entry['metrics']:
                # Formato anidado: {'metrics': {'MSE': value}}
                all_values.append(entry['metrics'][metric_name])
            elif metric_name in entry:
                # Formato plano: {'MSE': value}
                all_values.append(entry[metric_name])
        
        if not all_values:
            return 0.5  # Valor predeterminado si no hay datos
        
        # Ignorar valores no numéricos o faltantes
        all_values = [v for v in all_values if isinstance(v, (int, float))]
        
        # Aplicar diferentes escalas según la métrica
        if metric_name in ('MSE', 'RMSE', 'MAE', 'MAPE'):
            # Menor es mejor, invertir la escala
            min_val, max_val = min(all_values), max(all_values)
            if min_val == max_val:
                return 0.5
            return 1 - ((value - min_val) / (max_val - min_val))
        else:
            # Mayor es mejor (R2, Accuracy, etc.)
            min_val, max_val = min(all_values), max(all_values)
            if min_val == max_val:
                return 0.5
            return (value - min_val) / (max_val - min_val)
    
    except Exception as e:
        print(f"Error en normalize_metric para {metric_name}: {e}")
        return 0.5  # Valor predeterminado en caso de error


def calculate_global_precision(current_metrics, metrics_history):
    """Calcula la precisión global del modelo actual en comparación con el historial"""
    try:
        # Normalizar cada métrica relevante
        normalized_mse = normalize_metric(current_metrics.get('MSE', 0), 'MSE', metrics_history)
        normalized_mae = normalize_metric(current_metrics.get('MAE', 0), 'MAE', metrics_history)
        normalized_r2 = normalize_metric(current_metrics.get('R2', 0), 'R2', metrics_history)
        normalized_acc = normalize_metric(current_metrics.get('Accuracy', 0), 'Accuracy', metrics_history)
        
        # Ponderación de métricas (ajustar según la importancia relativa)
        weights = {
            'mse': 0.25,
            'mae': 0.25,
            'r2': 0.25,
            'acc': 0.25
        }
        
        # Calcular precisión global ponderada
        global_precision = (
            normalized_mse * weights['mse'] +
            normalized_mae * weights['mae'] +
            normalized_r2 * weights['r2'] +
            normalized_acc * weights['acc']
        )
        
        return float(global_precision)
    except Exception as e:
        print(f"Error al calcular precisión global: {e}")
        return 0.5  # Valor predeterminado en caso de error


@login_required
def dashboard(request):
    """Renderiza el dashboard de métricas de la red neuronal"""
    try:
        with open('redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r') as f:
            metrics_history = json.load(f)
            
            if metrics_history and isinstance(metrics_history, list):
                latest_metrics = metrics_history[-1] if metrics_history else None
            elif metrics_history and isinstance(metrics_history, dict):
                if 'entries' in metrics_history:
                    entries = metrics_history['entries']
                    metrics_history = entries
                    latest_metrics = entries[-1] if entries else None
                else:
                    latest_metrics = metrics_history
                    metrics_history = [metrics_history]
            else:
                metrics_history = []
                latest_metrics = None
                print("Formato de metrics_history.json no reconocido")
    except Exception as e:
        print(f"Error al cargar metrics_history.json: {e}")
        metrics_history = []
        latest_metrics = None

    if latest_metrics:
        try:
            metrics_data = latest_metrics.get('metrics', latest_metrics)
            
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

    timestamps = []
    mse_values = []
    accuracy_values = []
    r2_values = []
    global_precision_values = []

    for entry in metrics_history:
        try:
            metrics_data = entry.get('metrics', entry)
            timestamp = entry.get('timestamp', entry.get('date', entry.get('created_at', '')))
            
            timestamps.append(timestamp)
            
            mse = metrics_data.get('MSE', metrics_data.get('mse', 0))
            mse_values.append(mse)
            
            accuracy = metrics_data.get('Accuracy', metrics_data.get('accuracy', 0))
            accuracy_values.append(accuracy)
            
            r2 = metrics_data.get('R2', metrics_data.get('r2', 0))
            r2_values.append(r2)
            
            try:
                gp = calculate_global_precision(metrics_data, metrics_history)
            except:
                gp = 0
            global_precision_values.append(gp)
        except Exception as e:
            print(f"Error procesando entrada histórica: {e}")

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


#falta adaptar al nuevo modelo
@login_required
def estimate_time(request):
    if request.method == 'POST':
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            REDES_DIR = os.path.join(BASE_DIR, 'redes_neuronales')
            MODEL_DIR = os.path.join(BASE_DIR, "redes_neuronales", "models")

            if (REDES_DIR not in sys.path):
                sys.path.append(REDES_DIR)

            from ml_model import EstimacionModel, DataPreprocessor

            MODEL_PATH = os.path.join(MODEL_DIR, "modelo_estimacion.keras")
            PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.pkl")
            SCALER_NUM_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
            SCALER_REQ_PATH = os.path.join(MODEL_DIR, "scaler_req.pkl")

            for path in [
                MODEL_PATH,
                PREPROCESSOR_PATH,
                SCALER_NUM_PATH,
                SCALER_REQ_PATH,
            ]:
                if not os.path.exists(path):
                    raise FileNotFoundError(f"No se encuentra el archivo: {path}")

            complejidad = int(request.POST.get('complejidad', 2))
            prioridad = int(request.POST.get('prioridad', 2))
            tipo_tarea = request.POST.get('tipo_tarea', 'backend')

            print("\nDatos recibidos para estimación:")
            print(f"Complejidad: {complejidad}")
            print(f"Prioridad: {prioridad}")
            print(f"Tipo de tarea: {tipo_tarea}")
            print("------------------------")

            X_num = np.array([[complejidad, prioridad]], dtype=np.float32)

            X_req = np.array(
                [[complejidad, complejidad, 1, prioridad]], dtype=np.float32
            )

            preprocessor = joblib.load(PREPROCESSOR_PATH)
            scaler_num = joblib.load(SCALER_NUM_PATH)
            scaler_req = joblib.load(SCALER_REQ_PATH)

            X_task = preprocessor.encode_task_types([tipo_tarea])

            X_num_norm = scaler_num.transform(X_num)
            X_req_norm = scaler_req.transform(X_req)

            config = {
                "vocab_size": 6,
                "lstm_units": 32,
                "dense_units": [64, 32],
                "dropout_rate": 0.2,
            }
            model = EstimacionModel(config)
            model.model = tf.keras.models.load_model(MODEL_PATH)

            resultado = model.predict_individual_task(
                X_num_norm, np.array(X_task).reshape(-1, 1), X_req_norm
            )

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
    
    try:
        with open('redes_neuronales/estimacion_tiempo/models/evaluation_metrics.json', 'r') as f:
            evaluation_metrics = json.load(f)
        context['evaluation_metrics'] = evaluation_metrics
    except Exception as e:
        print(f"Error al cargar métricas de evaluación: {e}")
        context['evaluation_metrics'] = latest_metrics.get('metrics', {}) if latest_metrics else {}
    
    try:
        with open('redes_neuronales/estimacion_tiempo/models/segmented_evaluation.json', 'r') as f:
            segmented_evaluation = json.load(f)
        context['segmented_evaluation'] = segmented_evaluation
    except Exception as e:
        print(f"Error al cargar evaluación por segmentos: {e}")
        context['segmented_evaluation'] = {}
    
    try:
        import pandas as pd
        
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
        
        feature_importance_data = {}
        
        feature_importance_data['global'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/global_feature_importance_detailed.csv'
        )
        feature_importance_data['recurso_1'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_1_Recurso.csv'
        )
        feature_importance_data['recurso_2'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_2_Recursos.csv'
        )
        feature_importance_data['recurso_3'] = load_feature_importance(
            'redes_neuronales/estimacion_tiempo/models/feature_importance_3_Recursos.csv'
        )
        
        context['feature_importance_data'] = feature_importance_data
        
        context['feature_importance'] = feature_importance_data['global']
    except Exception as e:
        print(f"Error al cargar importancia de características: {e}")
        context['feature_importance_data'] = {}
        context['feature_importance'] = []

    return render(request, 'redes_neuronales/estimacion_avanzada.html', context)


#endpoints para entrenar modelo
@login_required
def entrenar_modelo(request):
    """Renderiza la interfaz de entrenamiento de red neuronal"""
    try:
        with open('redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r') as f:
            metrics_history = json.load(f)
            
            if metrics_history and isinstance(metrics_history, list):
                latest_metrics = metrics_history[-1] if metrics_history else None
            elif metrics_history and isinstance(metrics_history, dict):
                if 'entries' in metrics_history:
                    entries = metrics_history['entries']
                    latest_metrics = entries[-1] if entries else None
                else:
                    latest_metrics = metrics_history
            else:
                metrics_history = []
                latest_metrics = None
    except Exception as e:
        metrics_history = []
        latest_metrics = None
        print(f"Error al cargar metrics_history.json: {e}")

    if latest_metrics:
        metrics_data = latest_metrics.get('metrics', latest_metrics)
        required_metrics = ['MSE', 'RMSE', 'MAE', 'R2', 'Accuracy']
        if all(metric in metrics_data for metric in required_metrics):
            global_precision = calculate_global_precision(metrics_data, metrics_history)
        else:
            global_precision = 0.8
    else:
        global_precision = 0.8

    context = {
        'latest_metrics': latest_metrics,
        'global_precision': global_precision,
    }
    
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'img')
    neural_bg_path = os.path.join(static_dir, 'neural-bg.svg')
    
    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)
        
    if not os.path.exists(neural_bg_path):
        with open(neural_bg_path, 'w') as f:
            f.write('''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
            <defs>
                <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                    <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#8080ff" stroke-width="0.5"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" />
            <g fill="none" stroke="#4040ff">
                <circle cx="150" cy="150" r="20" stroke-width="2"/>
                <circle cx="400" cy="100" r="20" stroke-width="2"/>
                <circle cx="650" cy="150" r="20" stroke-width="2"/>
                <circle cx="150" cy="300" r="20" stroke-width="2"/>
                <circle cx="400" cy="300" r="20" stroke-width="2"/>
                <circle cx="650" cy="300" r="20" stroke-width="2"/>
                <circle cx="150" cy="450" r="20" stroke-width="2"/>
                <circle cx="400" cy="500" r="20" stroke-width="2"/>
                <circle cx="650" cy="450" r="20" stroke-width="2"/>
                
                <path d="M 150 150 L 400 100 L 650 150" stroke-width="1"/>
                <path d="M 150 300 L 400 300 L 650 300" stroke-width="1"/>
                <path d="M 150 450 L 400 500 L 650 450" stroke-width="1"/>
                <path d="M 150 150 L 400 300 L 650 450" stroke-width="1"/>
                <path d="M 150 450 L 400 300 L 650 150" stroke-width="1"/>
                <path d="M 150 150 L 400 500" stroke-width="1"/>
                <path d="M 150 450 L 400 100" stroke-width="1"/>
                <path d="M 400 100 L 650 300" stroke-width="1"/>
                <path d="M 400 500 L 650 300" stroke-width="1"/>
            </g>
            </svg>''')
    
    return render(request, 'redes_neuronales/entrenar_modelo.html', context)


def safe_cache_set(key, value, timeout=None):
    """Función para almacenar datos en caché de manera segura con manejo de errores"""
    from django.core.cache import cache
    try:
        cache.set(key, value, timeout)
        return True
    except Exception as e:
        import traceback
        print(f"Error al almacenar en caché: {str(e)}")
        print(traceback.format_exc())
        return False


def safe_cache_get(key):
    """Función para recuperar datos de caché de manera segura"""
    from django.core.cache import cache
    try:
        return cache.get(key)
    except Exception as e:
        import traceback
        print(f"Error al leer de caché: {str(e)}")
        print(traceback.format_exc())
        return None


@login_required
def iniciar_entrenamiento(request):
    """API para iniciar el proceso de entrenamiento"""
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        import uuid
        import time
        training_id = str(uuid.uuid4())
        
        training_method = request.POST.get('training_method', 'csv')
        
        data_path = None
        if training_method == 'csv' and 'csv_file' in request.FILES:
            import tempfile
            import os
            
            temp_dir = os.path.join(tempfile.gettempdir(), 'rnn_training')
            os.makedirs(temp_dir, exist_ok=True)
            
            csv_file = request.FILES['csv_file']
            data_path = os.path.join(temp_dir, f'training_data_{training_id}.csv')
            with open(data_path, 'wb+') as destination:
                for chunk in csv_file.chunks():
                    destination.write(chunk)
        
        # Configuración del entrenamiento - MEJORADO: Inicializar lista de actualizaciones vacía
        config = {
            'training_method': training_method,
            'data_path': data_path,
            'use_synthetic': request.POST.get('use_synthetic') == 'on',
            'rnn_type': request.POST.get('rnn_type', 'GRU'),
            'bidirectional': request.POST.get('bidirectional') == '1',
            'rnn_units': int(request.POST.get('rnn_units', 64)),
            'dropout_rate': float(request.POST.get('dropout_rate', 0.3)),
            'learning_rate': float(request.POST.get('learning_rate', 0.001)),
            'epochs': int(request.POST.get('epochs', 100)),
            'batch_size': int(request.POST.get('batch_size', 32)),
            'test_size': int(request.POST.get('test_size', 20)) / 100,
            'validation_size': int(request.POST.get('validation_size', 15)) / 100,
            'model_name': request.POST.get('model_name', 'tiempo_estimator'),
            'save_as_main': request.POST.get('save_as_main') == 'on',
            'status': 'pending',
            'optimizer': request.POST.get('optimizer', 'adam'),
            'use_layer_norm': request.POST.get('use_layer_norm') is not None,
            'use_residual': request.POST.get('use_residual') is not None,
            'early_stopping_patience': int(request.POST.get('early_stopping_patience', '30')),
            'updates': [],  # IMPORTANTE: Inicializar array de actualizaciones vacío
            'timestamp': timezone.now().isoformat()  # Usar timezone para consistencia
        }

        # Mostrar la configuración en la terminal
        print("\nConfiguración del entrenamiento:")
        for key, value in config.items():
            print(f"{key}: {value}")
        print("------------------------")
        
        # Guardar configuración en la sesión (primer método de respaldo)
        request.session[f'training_config_{training_id}'] = config
        
        # Intentar guardar en caché - si falla, continuamos usando la sesión
        cache_success = safe_cache_set(f'training_config_{training_id}', config, 7200)  # 2 horas de vida
        
        try:
            usuario_id = request.user.idusuario
            
            # También almacenar usuario_id en la sesión como respaldo
            request.session[f'training_user_{training_id}'] = usuario_id
            
            # Intentar almacenar usuario_id en caché
            if cache_success:
                safe_cache_set(f'training_user_{training_id}', usuario_id, 7200)
            
            # Importar la tarea definida en tasks.py
            from .tasks import start_training_process
            
            try:
                # MEJORA: Enviar mensaje inicial directo a la cola y caché
                from .ipc_utils import send_update
                initial_message = {
                    'type': 'log',
                    'message': 'Proceso de entrenamiento iniciándose...',
                    'level': 'info',
                    'timestamp': time.time()
                }
                send_update(training_id, initial_message)
                
                # Añadir también al array en config directamente
                config['updates'].append(initial_message)
                safe_cache_set(f'training_config_{training_id}', config, 7200)
                
                # Iniciar el proceso asíncrono usando .delay() que ahora funciona correctamente
                print(f"Iniciando entrenamiento con ID {training_id} y usuario {usuario_id}")
                result = start_training_process.delay(training_id, usuario_id)
                
                # Opcional: Guardar ID del resultado para posible cancelación
                if cache_success:
                    safe_cache_set(f'training_task_{training_id}', result.id, 7200)
                    
                print(f"Proceso iniciado con éxito, ID de resultado: {result.id}")
                
            except Exception as task_error:
                # Log detallado del error específico de la tarea
                import traceback
                print(f"Error al crear la tarea asíncrona: {str(task_error)}")
                print(traceback.format_exc())
                
                # Intentar método alternativo si .delay() falla
                from .tasks import task_manager
                from .entrenamiento_utils import ejecutar_entrenamiento
                
                task_id = task_manager.start_task(ejecutar_entrenamiento, training_id, usuario_id)
                print(f"Método alternativo utilizado, tarea iniciada con ID: {task_id}")
                
                if cache_success:
                    safe_cache_set(f'training_task_{training_id}', task_id, 7200)
            
        except Exception as e:
            import traceback
            print(f"Error al iniciar el entrenamiento: {str(e)}")
            print(traceback.format_exc())
            
            return JsonResponse({
                'success': False,
                'error': f'Error al iniciar el entrenamiento: {str(e)}',
            }, status=500)
        
        return JsonResponse({
            'success': True,
            'training_id': training_id,
            'message': 'Proceso de entrenamiento iniciado',
            'cache_status': 'ok' if cache_success else 'fallback_to_session'
        })
    
    return JsonResponse({
        'success': False,
        'error': 'Método no permitido o solicitud inválida',
    }, status=400)


@login_required
def monitor_entrenamiento(request):
    """Endpoint Server-Sent Events para monitorear el progreso del entrenamiento"""
    training_id = request.GET.get('training_id')
    
    if not training_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de entrenamiento no proporcionado',
        }, status=400)
    
    # Verificar existencia del entrenamiento en sesión o cache
    from django.core.cache import cache
    config_key = f'training_config_{training_id}'
    config = cache.get(config_key)
    
    if not config and f'training_config_{training_id}' not in request.session:
        return JsonResponse({
            'success': False,
            'error': 'Sesión de entrenamiento no encontrada',
        }, status=404)
    
    # Configurar la respuesta de streaming con eventos del servidor
    # IMPORTANTE: No añadir ningún header de tipo hop-by-hop
    response = StreamingHttpResponse(
        _stream_training_updates(training_id, request.session),
        content_type='text/event-stream'
    )
    
    # Headers seguros para SSE (solo headers end-to-end)
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'
    
    return response


def _stream_training_updates(training_id, session):
    """
    Generador de eventos para Server-Sent Events (SSE) que transmite actualizaciones 
    de entrenamiento en tiempo real al cliente.
    
    Args:
        training_id: ID único del proceso de entrenamiento a monitorear
        session: Sesión de Django para acceso alternativo a datos
        
    Yields:
        Eventos SSE formateados con los datos actualizados del entrenamiento
    """
    import time
    import json
    from django.core.cache import cache
    from redes_neuronales.ipc_utils import get_updates
    
    # Configuración de monitoreo
    poll_interval = 0.05           # Tiempo entre verificaciones (segundos)
    heartbeat_interval = 1.0       # Tiempo entre heartbeats (segundos)
    diagnostic_interval = 15.0     # Tiempo entre diagnósticos (segundos)
    
    # Variables de seguimiento
    last_update_index = 0          # Último índice de actualización enviado
    last_heartbeat_time = 0        # Último momento en que se envió un heartbeat
    last_diagnostic_time = 0       # Último momento en que se realizó un diagnóstico
    last_check_time = time.time()  # Último momento en que se verificaron actualizaciones
    start_time = time.time()       # Momento de inicio del monitoreo
    epoch_logs_sent = set()        # Conjunto de logs de época ya enviados
    updates_counter = 0            # Contador de actualizaciones enviadas
    cycles_without_updates = 0     # Ciclos consecutivos sin actualizaciones
    
    # Enviar evento de conexión establecida
    yield _format_sse_event('connection', {
        'status': 'connected', 
        'training_id': training_id,
        'timestamp': time.time()
    })
    
    # Log para verificación de inicio
    yield _format_sse_event('log', {
        'type': 'log',
        'message': 'Sistema de monitorización activo - esperando datos del entrenamiento',
        'level': 'info',
        'timestamp': time.time()
    })
    
    # Bucle principal de monitorización
    while True:
        current_time = time.time()
        
        try:
            # Limitar la frecuencia de verificación para no sobrecargar el servidor
            if current_time - last_check_time < poll_interval:
                time.sleep(0.01)  # Pequeña pausa para no usar CPU excesivamente
                continue
                
            last_check_time = current_time
            
            # 1. Obtener actualizaciones desde el caché
            updates = _get_cache_updates(training_id, last_update_index)
            
            # 2. Si no hay actualizaciones en caché, intentar la cola IPC
            if not updates and cycles_without_updates % 5 == 0:
                updates = _get_queue_updates(training_id)
                
            # 3. Procesar las actualizaciones obtenidas
            if updates:
                for update in updates:
                    # Enviar actualizaciones según su tipo
                    yield _process_update(update, training_id, epoch_logs_sent)
                    updates_counter += 1
                
                # Actualizar índice tras procesar actualizaciones
                config = cache.get(f'training_config_{training_id}')
                if config and 'updates' in config:
                    last_update_index = len(config['updates'])
                
                cycles_without_updates = 0
            else:
                cycles_without_updates += 1
            
            # 4. Verificar finalización del entrenamiento
            status = _check_training_status(training_id)
            if status in ['completed', 'failed']:
                # Enviar un evento 'complete' con todos los datos necesarios
                complete_data = _prepare_complete_event(training_id)
                yield _format_sse_event('complete', complete_data)
                yield _format_sse_event('close', {
                    'status': status, 
                    'message': 'Stream finalizado'
                })
                break
            
            # 5. Enviar heartbeat periódicamente
            if current_time - last_heartbeat_time >= heartbeat_interval:
                yield _format_sse_event('heartbeat', {
                    'timestamp': current_time,
                    'stats': {
                        'cycles': cycles_without_updates,
                        'total_updates': updates_counter,
                        'monitoring_time': int(current_time - start_time)
                    }
                })
                last_heartbeat_time = current_time
            
            # 6. Realizar diagnóstico periódico si es necesario
            if cycles_without_updates > 300 and current_time - last_diagnostic_time >= diagnostic_interval:
                diagnostic_data = _run_diagnostics(training_id, cycles_without_updates)
                yield _format_sse_event('diagnostics', diagnostic_data)
                last_diagnostic_time = current_time
            
            # 7. Pequeña pausa para evitar sobrecarga de CPU
            time.sleep(poll_interval)
            
        except Exception as e:
            # Registrar el error pero continuar monitoreando
            import traceback
            error_data = {
                'type': 'error',
                'message': f'Error en monitorización: {str(e)}',
                'details': traceback.format_exc().split('\n')[-5:],
                'timestamp': time.time()
            }
            yield _format_sse_event('error', error_data)
            time.sleep(0.5)  # Pequeño retraso antes de continuar

# Funciones auxiliares para mantener el código principal limpio

def _format_sse_event(event_type, data):
    """Formatea un evento SSE con sus datos correspondientes"""
    import json
    return f'event: {event_type}\ndata: {json.dumps(data)}\n\n'

def _get_cache_updates(training_id, last_index):
    """Obtiene actualizaciones nuevas desde el caché"""
    from django.core.cache import cache
    
    config = cache.get(f'training_config_{training_id}')
    if not config or 'updates' not in config:
        return []
        
    if len(config['updates']) > last_index:
        return config['updates'][last_index:]
    
    return []

def _get_queue_updates(training_id):
    """Obtiene actualizaciones desde la cola IPC"""
    try:
        from redes_neuronales.ipc_utils import get_updates
        return get_updates(training_id)
    except:
        return []

def _check_training_status(training_id):
    """Verifica el estado actual del entrenamiento"""
    from django.core.cache import cache
    
    config = cache.get(f'training_config_{training_id}')
    if config:
        return config.get('status', 'unknown')
    return 'unknown'

def _process_update(update, training_id, epoch_logs_sent):
    """Procesa una actualización y la formatea como evento SSE"""
    update_type = update.get('type', 'log')
    
    # Registrar log de época para no enviar duplicados
    if update.get('is_epoch_log') and update.get('epoch_number'):
        epoch_num = update.get('epoch_number')
        if epoch_num in epoch_logs_sent:
            # Solo enviar eventos de progreso, no duplicar logs
            if update_type == 'progress':
                return _format_sse_event(update_type, update)
            return None
        epoch_logs_sent.add(epoch_num)
    
    # Manejar tipos de eventos específicos
    if update_type == 'batch_progress':
        # Estos eventos son muy frecuentes, enviar ocasionalmente
        if len(epoch_logs_sent) % 10 == 0:
            return _format_sse_event(update_type, update)
        return None
    
    # Para el resto de eventos, enviar normalmente
    return _format_sse_event(update_type, update)

def _prepare_complete_event(training_id):
    """
    Prepara un evento 'complete' con todos los datos necesarios para handleTrainingComplete
    Asegura que contenga: metrics, history, predictions, y_test, epoch_logs, model_id, model_name
    """
    from django.core.cache import cache
    import time
    
    # Obtener configuración y resultado del entrenamiento
    config = cache.get(f'training_config_{training_id}')
    
    # Inicializar datos por defecto
    complete_data = {
        'status': 'completed',
        'timestamp': time.time(),
        'training_id': training_id,
        'message': 'Entrenamiento finalizado exitosamente',
        'metrics': {},
        'history': {'loss': [], 'val_loss': []},
        'predictions': [],
        'y_test': [],
        'epoch_logs': [],
        'model_id': training_id,
        'model_name': 'tiempo_estimator'
    }
    
    if not config:
        return complete_data
        
    # Intentar diferentes ubicaciones para losdef _stream_training_updates(training_id, session):
    """
    Generador de eventos para Server-Sent Events (SSE) que transmite actualizaciones 
    de entrenamiento en tiempo real al cliente.
    
    Args:
        training_id: ID único del proceso de entrenamiento a monitorear
        session: Sesión de Django para acceso alternativo a datos
        
    Yields:
        Eventos SSE formateados con los datos actualizados del entrenamiento
    """
    import time
    import json
    from django.core.cache import cache
    from redes_neuronales.ipc_utils import get_updates
    
    # Configuración de monitoreo
    poll_interval = 0.05           # Tiempo entre verificaciones (segundos)
    heartbeat_interval = 1.0       # Tiempo entre heartbeats (segundos)
    diagnostic_interval = 15.0     # Tiempo entre diagnósticos (segundos)
    
    # Variables de seguimiento
    last_update_index = 0          # Último índice de actualización enviado
    last_heartbeat_time = 0        # Último momento en que se envió un heartbeat
    last_diagnostic_time = 0       # Último momento en que se realizó un diagnóstico
    last_check_time = time.time()  # Último momento en que se verificaron actualizaciones
    start_time = time.time()       # Momento de inicio del monitoreo
    epoch_logs_sent = set()        # Conjunto de logs de época ya enviados
    updates_counter = 0            # Contador de actualizaciones enviadas
    cycles_without_updates = 0     # Ciclos consecutivos sin actualizaciones
    
    # Enviar evento de conexión establecida
    yield _format_sse_event('connection', {
        'status': 'connected', 
        'training_id': training_id,
        'timestamp': time.time()
    })
    
    # Log para verificación de inicio
    yield _format_sse_event('log', {
        'type': 'log',
        'message': 'Sistema de monitorización activo - esperando datos del entrenamiento',
        'level': 'info',
        'timestamp': time.time()
    })
    
    # Bucle principal de monitorización
    while True:
        current_time = time.time()
        
        try:
            # Limitar la frecuencia de verificación para no sobrecargar el servidor
            if current_time - last_check_time < poll_interval:
                time.sleep(0.01)  # Pequeña pausa para no usar CPU excesivamente
                continue
                
            last_check_time = current_time
            
            # 1. Obtener actualizaciones desde el caché
            updates = _get_cache_updates(training_id, last_update_index)
            
            # 2. Si no hay actualizaciones en caché, intentar la cola IPC
            if not updates and cycles_without_updates % 5 == 0:
                updates = _get_queue_updates(training_id)
                
            # 3. Procesar las actualizaciones obtenidas
            if updates:
                for update in updates:
                    # Enviar actualizaciones según su tipo
                    yield _process_update(update, training_id, epoch_logs_sent)
                    updates_counter += 1
                
                # Actualizar índice tras procesar actualizaciones
                config = cache.get(f'training_config_{training_id}')
                if config and 'updates' in config:
                    last_update_index = len(config['updates'])
                
                cycles_without_updates = 0
            else:
                cycles_without_updates += 1
            
            # 4. Verificar finalización del entrenamiento
            status = _check_training_status(training_id)
            if status in ['completed', 'failed']:
                # Enviar un evento 'complete' con todos los datos necesarios
                complete_data = _prepare_complete_event(training_id)
                yield _format_sse_event('complete', complete_data)
                yield _format_sse_event('close', {
                    'status': status, 
                    'message': 'Stream finalizado'
                })
                break
            
            # 5. Enviar heartbeat periódicamente
            if current_time - last_heartbeat_time >= heartbeat_interval:
                yield _format_sse_event('heartbeat', {
                    'timestamp': current_time,
                    'stats': {
                        'cycles': cycles_without_updates,
                        'total_updates': updates_counter,
                        'monitoring_time': int(current_time - start_time)
                    }
                })
                last_heartbeat_time = current_time
            
            # 6. Realizar diagnóstico periódico si es necesario
            if cycles_without_updates > 300 and current_time - last_diagnostic_time >= diagnostic_interval:
                diagnostic_data = _run_diagnostics(training_id, cycles_without_updates)
                yield _format_sse_event('diagnostics', diagnostic_data)
                last_diagnostic_time = current_time
            
            # 7. Pequeña pausa para evitar sobrecarga de CPU
            time.sleep(poll_interval)
            
        except Exception as e:
            # Registrar el error pero continuar monitoreando
            import traceback
            error_data = {
                'type': 'error',
                'message': f'Error en monitorización: {str(e)}',
                'details': traceback.format_exc().split('\n')[-5:],
                'timestamp': time.time()
            }
            yield _format_sse_event('error', error_data)
            time.sleep(0.5)  # Pequeño retraso antes de continuar

# Funciones auxiliares para mantener el código principal limpio

def _format_sse_event(event_type, data):
    """Formatea un evento SSE con sus datos correspondientes"""
    import json
    return f'event: {event_type}\ndata: {json.dumps(data)}\n\n'

def _get_cache_updates(training_id, last_index):
    """Obtiene actualizaciones nuevas desde el caché"""
    from django.core.cache import cache
    
    config = cache.get(f'training_config_{training_id}')
    if not config or 'updates' not in config:
        return []
        
    if len(config['updates']) > last_index:
        return config['updates'][last_index:]
    
    return []

def _get_queue_updates(training_id):
    """Obtiene actualizaciones desde la cola IPC"""
    try:
        from redes_neuronales.ipc_utils import get_updates
        return get_updates(training_id)
    except:
        return []

def _check_training_status(training_id):
    """Verifica el estado actual del entrenamiento"""
    from django.core.cache import cache
    
    config = cache.get(f'training_config_{training_id}')
    if config:
        return config.get('status', 'unknown')
    return 'unknown'

def _process_update(update, training_id, epoch_logs_sent):
    """Procesa una actualización y la formatea como evento SSE"""
    update_type = update.get('type', 'log')
    
    # Registrar log de época para no enviar duplicados
    if update.get('is_epoch_log') and update.get('epoch_number'):
        epoch_num = update.get('epoch_number')
        if epoch_num in epoch_logs_sent:
            # Solo enviar eventos de progreso, no duplicar logs
            if update_type == 'progress':
                return _format_sse_event(update_type, update)
            return None
        epoch_logs_sent.add(epoch_num)
    
    # Manejar tipos de eventos específicos
    if update_type == 'batch_progress':
        # Estos eventos son muy frecuentes, enviar ocasionalmente
        if len(epoch_logs_sent) % 10 == 0:
            return _format_sse_event(update_type, update)
        return None
    
    # Para el resto de eventos, enviar normalmente
    return _format_sse_event(update_type, update)

def _prepare_complete_event(training_id):
    """
    Prepara un evento 'complete' con todos los datos necesarios para handleTrainingComplete
    Asegura que contenga: metrics, history, predictions, y_test, epoch_logs, model_id, model_name
    """
    from django.core.cache import cache
    import time
    
    # Obtener configuración y resultado del entrenamiento
    config = cache.get(f'training_config_{training_id}')
    
    # Inicializar datos por defecto
    complete_data = {
        'status': 'completed',
        'timestamp': time.time(),
        'training_id': training_id,
        'message': 'Entrenamiento finalizado exitosamente',
        'metrics': {},
        'history': {'loss': [], 'val_loss': []},
        'predictions': [],
        'y_test': [],
        'epoch_logs': [],
        'model_id': training_id,
        'model_name': 'tiempo_estimator'
    }
    
    if not config:
        return complete_data
        
    # Intentar diferentes ubicaciones para los resultados
    
    # 1. Buscar en config['result'] (estructura primaria)
    if 'result' in config:
        result = config['result']
        if isinstance(result, dict):
            # Extraer datos según el esquema esperado
            if 'metrics' in result:
                complete_data['metrics'] = result['metrics']
            if 'history' in result:
                complete_data['history'] = result['history']
            if 'predictions' in result:
                complete_data['predictions'] = result['predictions']
            if 'y_test' in result:
                complete_data['y_test'] = result['y_test']
            elif 'actual' in result:  # Compatibilidad con nombre alternativo
                complete_data['y_test'] = result['actual']
            if 'epoch_logs' in result:
                complete_data['epoch_logs'] = result['epoch_logs']
            if 'model_name' in result:
                complete_data['model_name'] = result['model_name']
            if 'model_id' in result:
                complete_data['model_id'] = result['model_id']
    
    # 2. Buscar en config (nivel superior) si no se encontró en result
    if not complete_data['metrics'] and 'metrics' in config:
        complete_data['metrics'] = config['metrics']
        
    if 'model_name' in config:
        complete_data['model_name'] = config['model_name']
    
    # 3. Recopilar épocas de logs de las actualizaciones si no se encontraron anteriormente
    if not complete_data['epoch_logs'] and 'updates' in config:
        complete_data['epoch_logs'] = [
            u for u in config['updates'] 
            if u.get('is_epoch_log', False) or 
               (u.get('type') == 'progress' and 'epoch' in u)
        ]
    
    # 4. Extraer datos de evaluación si existen
    if 'evaluation' in config:
        evaluation = config['evaluation']
        if not complete_data['metrics'] and 'metrics' in evaluation:
            complete_data['metrics'] = evaluation['metrics']
        if not complete_data['predictions'] and 'predictions' in evaluation:
            complete_data['predictions'] = evaluation['predictions']
        if not complete_data['y_test'] and 'actual' in evaluation:
            complete_data['y_test'] = evaluation['actual']
    
    # Asegurar que los campos críticos sean válidos
    for field in ['metrics', 'history', 'predictions', 'y_test']:
        if not complete_data[field] or not isinstance(complete_data[field], (dict, list)):
            if field == 'metrics':
                complete_data[field] = {'MSE': 0, 'MAE': 0, 'RMSE': 0, 'R2': 0}
            elif field == 'history':
                complete_data[field] = {'loss': [], 'val_loss': []}
            else:
                complete_data[field] = []
    
    # Registrar que enviamos datos completos
    print(f"Preparando evento complete para {training_id} - métricas: {complete_data['metrics']}")
    return complete_data


@login_required
def check_active_training(request):
    """Verifica si hay entrenamientos activos para el usuario actual"""
    from django.core.cache import cache
    
    try:
        usuario_id = request.user.idusuario
        active_trainings = []
        
        # Buscar claves de configuración de entrenamiento en caché
        keys_pattern = f'training_config_*'
        all_keys = cache.keys(keys_pattern)
        
        if not all_keys:
            # Si no podemos obtener las claves directamente, probamos con la sesión
            for key in request.session.keys():
                if key.startswith('training_config_'):
                    training_id = key.replace('training_config_', '')
                    config = request.session.get(key)
                    if config and config.get('status') in ['running', 'pending']:
                        active_trainings.append({
                            'training_id': training_id,
                            'model_name': config.get('model_name', 'tiempo_estimator'),
                            'status': config.get('status'),
                            'timestamp': config.get('timestamp')
                        })
        else:
            # Procesar claves de caché
            for key in all_keys:
                if key.startswith('training_config_'):
                    training_id = key.replace('training_config_', '')
                    config = cache.get(key)
                    
                    # Verificar si este entrenamiento pertenece al usuario actual
                    training_user_key = f'training_user_{training_id}'
                    training_user_id = cache.get(training_user_key)
                    
                    if (training_user_id == usuario_id and 
                        config and config.get('status') in ['running', 'pending']):
                        active_trainings.append({
                            'training_id': training_id,
                            'model_name': config.get('model_name', 'tiempo_estimator'),
                            'status': config.get('status'),
                            'timestamp': config.get('timestamp')
                        })
        
        return JsonResponse({
            'success': True,
            'active_trainings': active_trainings
        })
    except Exception as e:
        import traceback
        print(f"Error al verificar entrenamientos activos: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'success': False, 
            'message': f'Error: {str(e)}'
        })


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
            
            # Generar archivos - ahora usa la implementación unificada
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


@login_required
@require_POST
def evaluar_modelo(request):
    """
    Vista para evaluar un modelo existente y generar visualizaciones
    """
    try:
        # Recibir el ID del modelo (training_id) del cuerpo de la solicitud
        data = json.loads(request.body)
        model_id = data.get('model_id')
        
        if not model_id:
            return JsonResponse({
                'success': False,
                'message': 'No se proporcionó un ID de modelo válido'
            })
            
        # CORRECCIÓN: Usar rutas absolutas para mayor seguridad
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(BASE_DIR, 'redes_neuronales', 'estimacion_tiempo', 'models')
        
        # Crear directorio si no existe
        os.makedirs(models_dir, exist_ok=True)
        
        # Verificar que existe el modelo
        model_keras_path = os.path.join(models_dir, 'tiempo_estimator_model.keras')
        
        if not os.path.exists(model_keras_path):
            return JsonResponse({
                'success': False,
                'message': 'El modelo no existe en el sistema'
            })
        
        try:
            # Importar clases necesarias
            from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator
            from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
            import joblib
            import numpy as np
            import time
            
            print(f"Cargando modelo para evaluación desde: {models_dir}")
            # Cargar el modelo
            estimator = AdvancedRNNEstimator.load(models_dir, 'tiempo_estimator')
            
            # Cargar feature_dims
            feature_dims = joblib.load(os.path.join(models_dir, 'feature_dims.pkl'))
            
            # Cargar datos de validación
            try:
                print("Cargando datos de validación...")
                X_val = np.load(os.path.join(models_dir, 'X_val.npy'))
                y_val = np.load(os.path.join(models_dir, 'y_val.npy'))
            except Exception as e:
                print(f"Error al cargar datos de validación: {str(e)}")
                traceback.print_exc()
                return JsonResponse({
                    'success': False,
                    'message': f'Error al cargar datos de validación: {str(e)}'
                })
            
            print(f"Creando evaluador con directorio de salida: {models_dir}")
            # CAMBIO: Usar models_dir como directorio de salida para el evaluador
            evaluator = ModelEvaluator(estimator, feature_dims, models_dir)
            
            print("Realizando evaluación del modelo...")
            # Evaluar el modelo
            metrics, predictions = evaluator.evaluate_model(X_val, y_val)
            
            print("Generando gráficos de predicciones...")
            # Generar gráficos de predicciones
            evaluator.plot_predictions(y_val, predictions)
            
            print("Analizando importancia de características...")
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
            
            print("Realizando evaluación segmentada...")
            # Evaluación segmentada para comprender el rendimiento en diferentes tipos de tareas
            segments = {
                'pequeñas': lambda y: y <= 10,
                'medianas': lambda y: (y > 10) & (y <= 30),
                'grandes': lambda y: y > 30
            }
            segmented_results = evaluator.segmented_evaluation(X_val, y_val, segments)
            
            # Generar nombres de archivo únicos para evitar caché del navegador
            timestamp = int(time.time())
            
            # Copiar las imágenes al directorio static para que sean accesibles desde la web
            static_dir = os.path.join(BASE_DIR, 'static', 'evaluacion', model_id)
            os.makedirs(static_dir, exist_ok=True)
            
            # Funciones de utilidad para copiar y generar URL
            def copy_and_get_url(source_file, dest_name):
                import shutil
                # Verificar primero si source_file es None para evitar el error
                if source_file is None:
                    return None
                    
                dest_file = os.path.join(static_dir, f"{dest_name}_{timestamp}.png")
                if os.path.exists(source_file):
                    shutil.copy2(source_file, dest_file)
                    # Convertir a URL relativa para el frontend
                    return f"/static/evaluacion/{model_id}/{dest_name}_{timestamp}.png"
                return None
            
            # Copiar y generar URLs para las imágenes
            feature_importance_url = copy_and_get_url(
                os.path.join(models_dir, 'global_feature_importance.png'),
                'feature_importance'
            )
            
            evaluation_plots_url = copy_and_get_url(
                os.path.join(models_dir, 'evaluation_plots.png'),
                'evaluation_plots'
            )
            
            segmented_metrics_url = copy_and_get_url(
                os.path.join(models_dir, 'feature_importance_metrics.png'),
                'segmented_metrics'
            )

            # Calcular precisión global (similar a la función calculate_global_precision)
            # Si no tienes history de métricas, usa un valor predeterminado
            try:
                with open(os.path.join(models_dir, 'metrics_history.json'), 'r') as f:
                    metrics_history = json.load(f)
                global_precision = calculate_global_precision(metrics, metrics_history)
            except:
                # Si no hay historial, usar un cálculo simple basado en R2
                r2 = metrics.get('R2', 0)
                global_precision = min(1.0, max(0.0, (r2 + 0.2) / 1.2))
            
            
            # Devolver respuesta de éxito con métricas y URLs de imágenes
            return JsonResponse({
                'success': True,
                'message': 'Evaluación completada con éxito',
                'metrics': metrics,
                'global_precision': global_precision,
                'feature_importance_image': feature_importance_url,
                'evaluation_plots_image': evaluation_plots_url,
                'segmented_metrics_image': segmented_metrics_url,
                'segmented_results': segmented_results,
                'model_id': model_id
            })
            
        except Exception as e:
            print(f"Error durante la evaluación: {str(e)}")
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'message': f'Error durante la evaluación: {str(e)}'
            })
    
    except Exception as e:
        print(f"Error general: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error: {str(e)}'
        })


@login_required
@require_POST
def generar_informe_evaluacion(request):
    """
    Vista para generar un informe PDF con los resultados de la evaluación del modelo
    """
    try:
        # Obtener datos del request
        data = json.loads(request.body)
        model_id = data.get('model_id')
        include_charts = data.get('include_charts', True)
        include_metrics = data.get('include_metrics', True)
        include_feature_importance = data.get('include_feature_importance', True)
        
        if not model_id:
            return JsonResponse({
                'success': False,
                'message': 'No se proporcionó un ID de modelo válido'
            })
        
        # Configurar rutas y directorios
        BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        models_dir = os.path.join(BASE_DIR, 'redes_neuronales', 'estimacion_tiempo', 'models')
        static_dir = os.path.join(BASE_DIR, 'static', 'evaluacion', model_id)
        
        # Verificar que existe el modelo
        model_keras_path = os.path.join(models_dir, 'tiempo_estimator_model.keras')
        if not os.path.exists(model_keras_path):
            return JsonResponse({
                'success': False,
                'message': 'El modelo no existe en el sistema'
            })
        
        # Cargar métricas si existen
        metrics = {}
        try:
            with open(os.path.join(models_dir, 'evaluation_metrics.json'), 'r') as f:
                metrics = json.load(f)
        except:
            print("Archivo de métricas no encontrado, generando informe con datos limitados")
        
        # Importar librerías para generar PDFs
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak, KeepTogether
        from reportlab.platypus import Flowable, FrameBreak, NextPageTemplate, PageTemplate
        from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
        from reportlab.pdfgen.canvas import Canvas
        from reportlab.platypus.frames import Frame
        from reportlab.graphics.shapes import Drawing, Line
        from io import BytesIO
        from datetime import datetime
        
        # Crear un buffer para el PDF
        buffer = BytesIO()
        
        # Definir paleta de colores moderna
        colors_palette = {
            'primary': colors.Color(59/255, 70/255, 229/255),  # Indigo-600
            'secondary': colors.Color(79/255, 70/255, 229/255),  # Indigo-500
            'accent': colors.Color(124/255, 58/255, 237/255),   # Purple-600
            'text': colors.Color(31/255, 41/255, 55/255),       # Gray-800
            'text_light': colors.Color(107/255, 114/255, 128/255),  # Gray-500
            'light_bg': colors.Color(243/255, 244/255, 246/255), # Gray-100
            'border': colors.Color(209/255, 213/255, 219/255),  # Gray-300
            'success': colors.Color(5/255, 150/255, 105/255),   # Green-600
            'warning': colors.Color(245/255, 158/255, 11/255),  # Amber-500
        }

        # Función para crear encabezado y pie de página
        def add_page_number(canvas, doc):
            canvas.saveState()
            # Encabezado
            header_height = 0.5*inch
            canvas.setFillColor(colors_palette['primary'])
            canvas.rect(0, doc.height + doc.topMargin - header_height,
                        doc.width + doc.leftMargin + doc.rightMargin, header_height,
                        fill=1, stroke=0)
            
            # Texto del encabezado
            canvas.setFont("Helvetica-Bold", 10)
            canvas.setFillColor(colors.white)
            canvas.drawString(doc.leftMargin, doc.height + doc.topMargin - header_height + 15, 
                            "INFORME DE EVALUACIÓN DEL MODELO RNN")
            
            # Logo o marca de agua en el encabezado (opcional)
            canvas.setFont("Helvetica", 8)
            canvas.drawRightString(doc.width + doc.leftMargin, doc.height + doc.topMargin - header_height + 15, 
                                 f"Modelo ID: {model_id[:8]}")
            
            # Pie de página con número de página y fecha
            footer_y = doc.bottomMargin - 20
            canvas.setFillColor(colors_palette['text'])
            canvas.setFont("Helvetica", 8)
            page_num = f"Página {canvas.getPageNumber()}"
            canvas.drawRightString(doc.width + doc.leftMargin, footer_y, page_num)
            
            # Fecha en pie de página
            current_date = datetime.now().strftime("%d/%m/%Y %H:%M")
            canvas.drawString(doc.leftMargin, footer_y, f"Generado: {current_date}")
            
            # Línea separadora en el pie de página
            canvas.setStrokeColor(colors_palette['border'])
            canvas.line(doc.leftMargin, footer_y + 10, doc.width + doc.leftMargin, footer_y + 10)
            
            canvas.restoreState()

        # Crear el documento con plantillas de página
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch
        )
        
        # Estilos personalizados para el documento
        styles = getSampleStyleSheet()
        
        # Título principal
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontName='Helvetica-Bold',
            fontSize=24,
            leading=30,
            alignment=TA_CENTER,
            textColor=colors_palette['primary'],
            spaceAfter=24
        ))
        
        # Subtítulo para secciones
        styles.add(ParagraphStyle(
            name='CustomSubtitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=16,
            leading=20,
            alignment=TA_LEFT,
            textColor=colors_palette['primary'],
            spaceBefore=15,
            spaceAfter=10,
            borderWidth=0,
            borderPadding=7,
            borderRadius=5,
            borderColor=colors_palette['primary']
        ))
        
        # Estilo para textos destacados
        styles.add(ParagraphStyle(
            name='Highlight',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=colors_palette['accent']
        ))
        
        # Estilo para pies de imagen
        styles.add(ParagraphStyle(
            name='Caption',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors_palette['text']
        ))
        
        # Estilo para métricas principales
        styles.add(ParagraphStyle(
            name='MetricValue',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=14,
            alignment=TA_CENTER,
            textColor=colors_palette['primary']
        ))
        
        # Estilo para etiquetas de métricas
        styles.add(ParagraphStyle(
            name='MetricLabel',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            alignment=TA_CENTER,
            textColor=colors_palette['text']
        ))

        styles.add(ParagraphStyle(
            name='ModernBody',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=11,
            leading=14,
            textColor=colors_palette['text']
        ))

        styles.add(ParagraphStyle(
            name='MetricHeader',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=12,
            leading=16,
            textColor=colors.white,
            alignment=TA_CENTER
        ))
        
        # Construir el contenido
        elements = []
        
        # Portada
        elements.append(Paragraph("INFORME DE EVALUACIÓN", styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*inch))
        
        # Información del modelo en caja destacada
        model_info_data = [
            ["MODELO DE RED NEURONAL RECURRENTE"],
            [f"ID: {model_id}"],
            ["ESTIMACIÓN DE TIEMPOS DE EJECUCIÓN"]
        ]
        
        model_info = Table(model_info_data, colWidths=[5*inch])
        model_info.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), colors_palette['light_bg']),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors_palette['text']),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (0, 0), 14),
            ('FONTSIZE', (0, 1), (0, 1), 10),
            ('FONTSIZE', (0, 2), (0, 2), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROUNDEDCORNERS', [10, 10, 10, 10]),
            ('BOX', (0, 0), (-1, -1), 1, colors_palette['border']),
        ]))
        elements.append(model_info)
        
        # Información básica
        elements.append(Spacer(1, 0.5*inch))
        fecha_generacion = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        elements.append(Paragraph(f"Fecha generación: {fecha_generacion}", styles['Normal']))
        
        # Añadir resumen ejecutivo con métricas principales en una tabla visual
        if metrics:
            elements.append(Spacer(1, 0.3*inch))
            
            # Encabezado con diseño mejorado
            elements.append(Paragraph("RESUMEN EJECUTIVO", ParagraphStyle(
                name='ExecutiveSummaryTitle',
                parent=styles['CustomSubtitle'],
                fontSize=18,
                leading=22,
                textColor=colors_palette['primary'],
                alignment=TA_CENTER,  # Centrado para mayor impacto visual
                spaceAfter=15
            )))
            
            # Línea decorativa bajo el título
            line_table = Table([['']],
                colWidths=[3*inch],
                rowHeights=[2],
                style=[
                    ('BACKGROUND', (0,0), (0,0), colors_palette['primary']),
                    ('ALIGN', (0,0), (0,0), 'CENTER'),
                ])
            elements.append(line_table)
            elements.append(Spacer(1, 0.2*inch))
            
            # Descripción breve del resumen ejecutivo
            elements.append(Paragraph(
                "Este modelo de estimación de tiempos muestra los siguientes indicadores de rendimiento:",
                ParagraphStyle(
                    name='SummaryDescription',
                    parent=styles['Normal'],
                    fontSize=10,
                    alignment=TA_CENTER,
                    textColor=colors_palette['text'],
                    spaceAfter=15
                )
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # Métricas en tarjetas modernas (2x2 grid)
            main_metrics = [
                ('R2', 'Coeficiente R²', metrics.get('R2', 0)),
                ('MAE', 'Error Abs. Medio', metrics.get('MAE', 0)),
                ('RMSE', 'RMSE', metrics.get('RMSE', 0)),
                ('ACC', 'Precisión Global', metrics.get('Accuracy', 0))
            ]

            # Crear una tabla 2x2 con tarjetas de métricas
            metric_rows = []
            for i in range(0, len(main_metrics), 2):
                row = []
                for j in range(2):
                    if i + j < len(main_metrics):
                        code, name, value = main_metrics[i + j]
                        
                        # Color para el valor de la métrica (verde si bueno, rojo si malo)
                        value_color = colors_palette['primary']  # Color por defecto
                        
                        # Ajustar color según el tipo de métrica con gradiente más suave
                        if code == 'R2' or code == 'ACC':  # Métricas donde más alto es mejor
                            if value > 0.85:
                                value_color = colors.Color(10/255, 150/255, 80/255)  # Verde elegante
                            elif value > 0.7:
                                value_color = colors.Color(30/255, 160/255, 90/255)  # Verde moderado
                            elif value > 0.5:
                                value_color = colors.Color(202/255, 138/255, 4/255)  # Ámbar
                            else:
                                value_color = colors.Color(220/255, 50/255, 50/255)  # Rojo suave
                        
                        metric_cell = [
                            # Título de métrica
                            Paragraph(name, ParagraphStyle(
                                'MetricHeader',
                                parent=styles['Normal'],
                                fontName='Helvetica-Bold',
                                fontSize=12,
                                leading=16,
                                textColor=colors.white,
                                alignment=TA_CENTER
                            )),
                            # Valor
                            Paragraph(f"{value:.4f}" if code != 'ACC' else f"{value:.2f}", 
                                    ParagraphStyle(
                                        'MetricValue',
                                        parent=styles['Normal'],
                                        fontName='Helvetica-Bold',
                                        fontSize=22,  # Aumentar tamaño para mejor legibilidad
                                        leading=28,
                                        textColor=value_color,
                                        alignment=TA_CENTER,
                                        backColor=colors.white  # Añadir color de fondo para asegurar contraste
                                    )),
                            # Código
                            Paragraph(code, ParagraphStyle(
                                'CodeStyle',
                                parent=styles['Normal'],
                                fontName='Courier-Bold',
                                fontSize=10,
                                textColor=colors.white,
                                alignment=TA_CENTER
                            ))
                        ]
                        row.append(metric_cell)
                    else:
                        row.append(['', '', ''])  # Celda vacía para completar la tabla
                metric_rows.append(row)

            # Crear tabla de métricas con espaciado mejorado
            metrics_table = Table(metric_rows, 
                                colWidths=[2.75*inch, 2.75*inch], 
                                rowHeights=[1.3*inch, 1.3*inch],
                                hAlign='CENTER')

            # Definir colores para un diseño más armonioso
            base_colors = [
                colors.HexColor('#4F46E5'),  # Indigo-600
                colors.HexColor('#6366F1'),  # Indigo-500
                colors.HexColor('#818CF8'),  # Indigo-400
                colors.HexColor('#A5B4FC')   # Indigo-300
            ]

            # Aplicar estilo a cada celda con colores alternos
            for row in range(len(metric_rows)):
                for col in range(len(metric_rows[row])):
                    cell_content = metric_rows[row][col]
                    if cell_content[0]:  # Si hay contenido
                        # Usar una paleta más sobria y profesional con mejor contraste
                        color_index = (row * 2 + col) % len(base_colors)
                        header_color = base_colors[color_index]
                        footer_color = base_colors[(color_index + 2) % len(base_colors)]
                        
                        metrics_table.setStyle(TableStyle([
                            # Cabecera con color elegante
                            ('BACKGROUND', (col, row), (col, row), header_color),
                            ('VALIGN', (col, row), (col, row), 'TOP'),
                        ]))
                        
                        # Crear un estilo específico para el valor central con fondo blanco puro
                        metrics_table.setStyle(TableStyle([
                            # Valor centrado - usar LINEABOVE y LINEBELOW para separar visualmente las secciones
                            ('BACKGROUND', (col, row), (col, row), colors.white),
                            ('ALIGN', (col, row), (col, row), 'CENTER'),
                            ('VALIGN', (col, row), (col, row), 'MIDDLE'),
                            ('LINEABOVE', (col, row), (col, row), 1, colors.white),
                            ('LINEBELOW', (col, row), (col, row), 1, colors.white),
                        ]))
                        
                        # Código con color complementario
                        metrics_table.setStyle(TableStyle([
                            ('BACKGROUND', (col, row), (col, row), footer_color),
                            ('VALIGN', (col, row), (col, row), 'BOTTOM'),
                            ('TEXTCOLOR', (col, row), (col, row), colors.white),  # Asegurar texto claro en fondo oscuro
                        ]))

            
            # Estilo global para todas las celdas
            metrics_table.setStyle(TableStyle([
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 12),
                ('BOX', (0, 0), (0, 0), 1, colors_palette['border']),
                ('BOX', (1, 0), (1, 0), 1, colors_palette['border']),
                ('BOX', (0, 1), (0, 1), 1, colors_palette['border']),
                ('BOX', (1, 1), (1, 1), 1, colors_palette['border']),
                ('ROUNDEDCORNERS', [8, 8, 8, 8]),
            ]))

            # Contenedor para garantizar centrado correcto
            container_table = Table([[metrics_table]], colWidths=[6*inch])
            container_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ]))

            elements.append(container_table)
            
            # Añadir nota explicativa
            elements.append(Spacer(1, 0.3*inch))
            elements.append(Paragraph(
                "<i>Nota: El coeficiente R² indica la capacidad predictiva del modelo, mientras que " +
                "el Error Absoluto Medio (MAE) y RMSE indican la precisión de las estimaciones en horas.</i>",
                ParagraphStyle(
                    name='MetricsNote',
                    parent=styles['Caption'],
                    fontSize=9,
                    alignment=TA_CENTER,
                    textColor=colors_palette['text_light'],
                )
            ))
            elements.append(Spacer(1, 0.5*inch))
        
        # Sección de métricas completas
        if include_metrics and metrics:
            elements.append(Paragraph("MÉTRICAS DE EVALUACIÓN", styles['CustomSubtitle']))
            
            # Notas explicativas
            elements.append(Paragraph(
                "Esta sección presenta las métricas detalladas de evaluación del modelo, "
                "indicando el rendimiento en diferentes aspectos de la estimación.",
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # Tabla principal de métricas con diseño mejorado
            metric_data = [['Métrica', 'Valor', 'Descripción']]
            
            # Mapeo de métricas con descripciones
            metric_descriptions = {
                'MSE': 'Promedio de los errores al cuadrado. Menor valor indica mejor ajuste.',
                'MAE': 'Promedio del valor absoluto de los errores. Mide la magnitud promedio de los errores sin considerar su dirección.',
                'RMSE': 'Raíz cuadrada del MSE. Proporciona una medida del error en las mismas unidades que la variable objetivo.',
                'R2': 'Proporción de la varianza explicada por el modelo. Valor 1.0 indica predicción perfecta.',
                'Accuracy': 'Porcentaje de predicciones dentro del margen de error aceptable.',
                'MAPE': 'Error porcentual absoluto medio. Indica el error como porcentaje respecto al valor real.',
                'Precision': 'Proporción de predicciones correctas entre todas las predicciones realizadas.',
                'Recall': 'Proporción de predicciones correctas entre los valores reales positivos.',
                'F1': 'Media armónica de precisión y recall. Mejor valor en 1.0.',
            }
            
            main_metrics = [('MSE', 'Error Cuadrático Medio'), ('MAE', 'Error Absoluto Medio'), 
                         ('RMSE', 'Raíz del Error Cuadrático Medio'), ('R2', 'Coeficiente R²')]
            
            for key, name in main_metrics:
                if key in metrics:
                    value = metrics[key]
                    metric_data.append([
                        name, 
                        f"{value:.4f}", 
                        metric_descriptions.get(key, "")
                    ])
            
            # Otras métricas adicionales
            for key, value in metrics.items():
                if key not in ['MSE', 'MAE', 'RMSE', 'R2'] and isinstance(value, (int, float)):
                    metric_data.append([
                        key, 
                        f"{value:.4f}", 
                        metric_descriptions.get(key, "")
                    ])

            # Crear tabla de métricas con estilo moderno
            if len(metric_data) > 1:
                # 1. Convertir los textos de descripción en objetos Paragraph para mejor control del ajuste
                for i in range(1, len(metric_data)):
                    if len(metric_data[i]) > 2:  # Si tiene columna de descripción
                        # Convertir el texto de la descripción a un Paragraph con estilo específico
                        description_style = ParagraphStyle(
                            'Description',
                            parent=styles['Normal'],
                            fontName='Helvetica',
                            fontSize=9,
                            leading=11,  # Espaciado entre líneas
                            alignment=TA_LEFT,
                            wordWrap='CJK'  # Modo de ajuste de texto más estricto
                        )
                        # Reemplazar el texto plano con un objeto Paragraph
                        metric_data[i][2] = Paragraph(metric_data[i][2], description_style)
                
                # 2. Ajustar anchos de columnas - dar más espacio a la descripción
                table = Table(metric_data, colWidths=[2.0*inch, 0.8*inch, 3.2*inch])
                
                # 3. Estilo para las filas con altura automática
                table_style = [
                    # Estilos de encabezado
                    ('BACKGROUND', (0, 0), (-1, 0), colors_palette['primary']),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('TOPPADDING', (0, 0), (-1, 0), 12),
                ]
                
                # 4. Aplicar estilos filas de datos con colores alternos y asegurar espacio vertical
                for i in range(1, len(metric_data)):
                    # Color alterno para filas
                    if i % 2 == 1:  # Filas impares
                        table_style.append(('BACKGROUND', (0, i), (-1, i), colors_palette['light_bg']))
                    
                    # Alineación y formato para cada columna
                    table_style.extend([
                        ('ALIGN', (0, i), (0, i), 'LEFT'),       # Nombre de métrica alineado a la izquierda
                        ('ALIGN', (1, i), (1, i), 'CENTER'),     # Valor centrado
                        ('VALIGN', (0, i), (-1, i), 'TOP'),      # Alineación vertical superior para todas las celdas
                        ('FONTNAME', (1, i), (1, i), 'Helvetica-Bold'),  # Valor en negrita
                        
                        # Aumentar espacio interno para texto
                        ('TOPPADDING', (0, i), (-1, i), 10),
                        ('BOTTOMPADDING', (0, i), (-1, i), 10),
                        ('LEFTPADDING', (2, i), (2, i), 10),     # Más padding izquierdo para descripción
                        ('RIGHTPADDING', (2, i), (2, i), 10),    # Más padding derecho para descripción
                    ])
                
                # 5. Estilo global de la tabla
                table_style.extend([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors_palette['border']),
                    ('BOX', (0, 0), (-1, -1), 1, colors_palette['border']),
                ])
                
                # Aplicar todos los estilos
                table.setStyle(TableStyle(table_style))
                
                elements.append(table)
                elements.append(Spacer(1, 0.3*inch))
                
                # Explicación de las métricas
                elements.append(Paragraph(
                    "<b>Nota:</b> Un modelo ideal tiene un valor R² cercano a 1.0, y valores bajos en MAE, RMSE y MSE.",
                    styles['Caption']
                ))
        
        # Añadir imágenes si están disponibles
        if include_charts:
            elements.append(PageBreak())
            elements.append(Paragraph("VISUALIZACIÓN DE RESULTADOS", styles['CustomSubtitle']))
            
            elements.append(Paragraph(
                "Los siguientes gráficos muestran el rendimiento del modelo en términos "
                "de precisión de predicciones y análisis de características importantes.",
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # Primero gráfico: predicciones vs valores reales
            evaluation_plots_path = os.path.join(static_dir, [f for f in os.listdir(static_dir) if 'evaluation_plots' in f][0]) if os.path.exists(static_dir) and any('evaluation_plots' in f for f in os.listdir(static_dir)) else None
            
            if evaluation_plots_path and os.path.exists(evaluation_plots_path):
                # Título de la sección de gráficos
                elements.append(Paragraph("Análisis de Predicciones", styles['Highlight']))
                elements.append(Spacer(1, 0.1*inch))
                
                # Crear un contenedor para la imagen con borde
                elements.append(Spacer(1, 0.1*inch))
                img = Image(evaluation_plots_path)
                img.drawHeight = 4.5*inch
                img.drawWidth = 6.5*inch
                
                # Crear tabla para poner borde y espacio alrededor de la imagen
                img_table = Table([[img]], colWidths=[6.5*inch], rowHeights=[4.5*inch])
                img_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors_palette['border']),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(img_table)
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(
                    "Figura 1: Comparación entre valores reales y predicciones del modelo. "
                    "La diagonal representa la predicción perfecta. Puntos más cercanos a esta línea indican mejor precisión.",
                    styles['Caption']
                ))
                elements.append(Spacer(1, 0.3*inch))
        
        # Añadir importancia de características con diseño mejorado
        if include_feature_importance:
            feature_importance_path = os.path.join(static_dir, [f for f in os.listdir(static_dir) if 'feature_importance' in f][0]) if os.path.exists(static_dir) and any('feature_importance' in f for f in os.listdir(static_dir)) else None
            
            if feature_importance_path and os.path.exists(feature_importance_path):
                elements.append(PageBreak())
                elements.append(Paragraph("ANÁLISIS DE CARACTERÍSTICAS", styles['CustomSubtitle']))
                
                elements.append(Paragraph(
                    "Este análisis identifica qué variables tienen mayor impacto en las predicciones "
                    "del modelo, permitiendo una mejor interpretación de los factores que influyen en los tiempos de ejecución.",
                    styles['Normal']
                ))
                elements.append(Spacer(1, 0.2*inch))
                
                # Título de la sección
                elements.append(Paragraph("Importancia Relativa de Características", styles['Highlight']))
                elements.append(Spacer(1, 0.1*inch))
                
                img = Image(feature_importance_path)
                img.drawHeight = 4.5*inch
                img.drawWidth = 6.5*inch
                
                # Tabla con borde para la imagen
                img_table = Table([[img]], colWidths=[6.5*inch], rowHeights=[4.5*inch])
                img_table.setStyle(TableStyle([
                    ('BOX', (0, 0), (-1, -1), 1, colors_palette['border']),
                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                    ('LEFTPADDING', (0, 0), (-1, -1), 5),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                    ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                
                elements.append(img_table)
                elements.append(Spacer(1, 0.1*inch))
                elements.append(Paragraph(
                    "Figura 2: Influencia de cada variable en las predicciones del modelo. "
                    "Las características con mayor puntuación tienen un impacto más significativo en la predicción de tiempos.",
                    styles['Caption']
                ))
                elements.append(Spacer(1, 0.3*inch))
        
        # Añadir métricas segmentadas con diseño mejorado
        segmented_metrics_path = os.path.join(static_dir, [f for f in os.listdir(static_dir) if 'segmented_metrics' in f][0]) if os.path.exists(static_dir) and any('segmented_metrics' in f for f in os.listdir(static_dir)) else None
        
        if segmented_metrics_path and os.path.exists(segmented_metrics_path):
            elements.append(PageBreak())
            elements.append(Paragraph("ANÁLISIS POR SEGMENTOS", styles['CustomSubtitle']))
            
            elements.append(Paragraph(
                "Este análisis muestra cómo se comporta el modelo en diferentes categorías de tareas, "
                "permitiendo identificar áreas específicas donde el modelo tiene mayor o menor precisión.",
                styles['Normal']
            ))
            elements.append(Spacer(1, 0.2*inch))
            
            # Título de la sección
            elements.append(Paragraph("Rendimiento por Categorías", styles['Highlight']))
            elements.append(Spacer(1, 0.1*inch))
            
            img = Image(segmented_metrics_path)
            img.drawHeight = 4.5*inch
            img.drawWidth = 6.5*inch
            
            # Tabla con borde para la imagen
            img_table = Table([[img]], colWidths=[6.5*inch], rowHeights=[4.5*inch])
            img_table.setStyle(TableStyle([
                ('BOX', (0, 0), (-1, -1), 1, colors_palette['border']),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                ('LEFTPADDING', (0, 0), (-1, -1), 5),
                ('RIGHTPADDING', (0, 0), (-1, -1), 5),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
            ]))
                    
            elements.append(img_table)
            elements.append(Spacer(1, 0.15*inch))
            elements.append(Paragraph(
                "Figura 3: Visualización del rendimiento del modelo por categorías de tareas, "
                "mostrando las métricas de evaluación para diferentes segmentos del conjunto de datos.",
                styles['Caption']
            ))
                    
            # Conclusión final
            elements.append(Spacer(1, 0.4*inch))
            elements.append(Paragraph("Conclusión", styles['Heading3']))
            elements.append(Spacer(1, 0.1*inch))
                    
            # Mostrar R2 o precisión global si está disponible
            r2_value = metrics.get('R2', 0)
            accuracy = metrics.get('Accuracy', 0)
            conclusion_text = f"""
            El modelo evaluado muestra un coeficiente de determinación (R²) de {r2_value:.4f} 
            y una precisión global de {accuracy:.4f}. Esto indica que el modelo 
            {"tiene un buen rendimiento" if r2_value > 0.7 else "requiere mejoras"} 
            para la estimación de tiempos de ejecución de tareas.
            """
                    
            elements.append(Paragraph(conclusion_text, styles['ModernBody']))
        
        # Footer personalizado
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors_palette['text_light'])
            
            # Dibujar línea
            canvas.setStrokeColor(colors_palette['border'])
            canvas.line(doc.leftMargin, 0.5*inch, doc.width + doc.leftMargin, 0.5*inch)
            
            # Texto del pie de página
            footer_text = f"Informe generado el {datetime.now().strftime('%d-%m-%Y')} | Modelo #{model_id[:8]}"
            canvas.drawRightString(doc.width + doc.leftMargin, 0.3*inch, footer_text)
            
            # Número de página
            page_num = canvas.getPageNumber()
            canvas.drawCentredString(doc.width/2 + doc.leftMargin, 0.3*inch, f"Página {page_num}")
            
            canvas.restoreState()
        
        # Construir el PDF con el pie de página personalizado
        doc.build(elements, onFirstPage=add_footer, onLaterPages=add_footer)
        
        # Obtener el contenido del PDF
        pdf = buffer.getvalue()
        buffer.close()
        
        # Crear respuesta HTTP con el PDF
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="evaluacion_modelo_{model_id[:8]}.pdf"'
        response.write(pdf)
        
        # Registrar actividad de usuario si está configurado el módulo de auditoría
        try:
            from auditoria.models import Actividad
            Actividad.objects.create(
                nombre=f"Generación de informe de evaluación",
                descripcion=f"El usuario generó un informe de evaluación para el modelo {model_id}",
                idusuario=request.user,
                accion="CREACION",
                es_automatica=True,
                entidad_tipo="Modelo IA",
                entidad_id=model_id
            )
        except:
            # Si no está disponible el módulo de auditoría, continuar sin error
            pass
        
        return response
        
    except Exception as e:
        import traceback
        print(f"Error al generar el informe: {str(e)}")
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error al generar el informe: {str(e)}'
        })
    

@login_required
def diagnosticar_entrenamiento(request):
    """Endpoint para realizar diagnósticos específicos sobre los logs de época"""
    training_id = request.GET.get('training_id')
    
    if not training_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de entrenamiento no proporcionado'
        }, status=400)
    
    try:
        # Importar utilidades de diagnóstico
        from .debug_utils import verify_connections, check_cache_state, inspect_queue, trace_log
        from .ipc_utils import dump_queue_status, get_queue_for_training
        
        # 1. Verificar estado de conexiones (cache y cola)
        connections = verify_connections(training_id)
        
        # 2. Diagnóstico específico de logs de época
        epoch_logs_diagnostics = diagnosticar_logs_epoca(training_id)
        
        # 3. Verificar el estado de la sesión
        session_info = {}
        if hasattr(request, 'session'):
            config_key = f'training_config_{training_id}'
            if config_key in request.session:
                config = request.session[config_key]
                session_info = {
                    'status': config.get('status', 'unknown'),
                    'timestamp': config.get('timestamp', ''),
                    'has_updates': 'updates' in config,
                    'updates_count': len(config.get('updates', [])),
                    'epoch_logs_count': sum(1 for u in config.get('updates', []) 
                                         if u.get('type') == 'log' and u.get('is_epoch_log', False))
                }
            else:
                session_info = {'status': 'not_found'}
        
        # Obtener info de las últimas actualizaciones para análisis
        cache_state = check_cache_state(training_id)
        last_updates = get_last_updates(training_id, 10)  # Obtener las últimas 10 actualizaciones
        
        # 4. Elaborar informe completo de diagnóstico
        diagnostics_report = {
            'success': True,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'training_id': training_id,
            'connections': connections,
            'epoch_logs': epoch_logs_diagnostics,
            'session_info': session_info,
            'queue_status': dump_queue_status(),
            'last_updates': last_updates
        }
        
        # Registrar un log del diagnóstico realizado
        trace_log(f"Diagnóstico completo para training_id={training_id}", 
                 category="DIAGNOSTIC_REQUEST", include_stack=True)
        
        return JsonResponse(diagnostics_report)
    
    except Exception as e:
        error_trace = traceback.format_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': error_trace
        }, status=500)


def diagnosticar_logs_epoca(training_id, request=None):
    """Realiza diagnóstico específico sobre los logs de época para un entrenamiento"""
    from django.core.cache import cache
    from .debug_utils import trace_log
    from django_redis import get_redis_connection
    
    # Diagnóstico detallado de logs de época
    result = {
        'total_found': 0,
        'in_cache': {
            'count': 0,
            'epochs_found': []
        },
        'in_queue': {
            'count': 0,
            'queue_size': 0,
            'epochs_found': []
        },
        'issues': [],
        'process_info': {}
    }
    
    try:
        # Verificar conexión Redis
        redis_connected = False
        try:
            conn = get_redis_connection("default")
            # Prueba simple para verificar que Redis responde
            conn.ping()
            redis_connected = True
        except Exception as e:
            trace_log(f"Error al verificar Redis: {str(e)}", category="REDIS_CHECK")
            result['issues'].append({
                'type': 'redis_connection',
                'message': f'Error al verificar conexión Redis: {str(e)}'
            })
        
        # Añadir información sobre procesos
        from .tasks import _ACTIVE_TASKS, active_processes
        
        # MEJORA: Verificar si hay cualquier proceso activo, no solo el exacto del training_id
        process_active = False
        direct_process = False
        
        # 1. Verificar si hay un proceso específico para este training_id
        if training_id in _ACTIVE_TASKS:
            process_active = True
            direct_process = True
            result['process_info'] = {
                'id': training_id,
                'status': _ACTIVE_TASKS[training_id].get('status', 'unknown'),
                'start_time': _ACTIVE_TASKS[training_id].get('start_time'),
                'is_direct': True
            }
        
        # 2. Si no hay proceso específico, verificar procesos activos en general
        if not direct_process:
            active_count = len(active_processes)
            if active_count > 0:
                process_active = True
                result['process_info'] = {
                    'active_count': active_count,
                    'is_direct': False
                }
        
        # 1. Revisar logs de época en caché especializados
        epoch_logs_specialized = []
        for i in range(1, 101):
            epoch_key = f'epoch_log_{training_id}_{i}'
            epoch_data = cache.get(epoch_key)
            if epoch_data:
                epoch_logs_specialized.append(i)
                result['in_cache']['count'] += 1
                if i not in result['in_cache']['epochs_found']:
                    result['in_cache']['epochs_found'].append(i)
                result['total_found'] += 1
                
        if epoch_logs_specialized:
            result['in_cache']['specialized_keys'] = len(epoch_logs_specialized)
            result['in_cache']['specialized_epochs'] = epoch_logs_specialized
        
        # 2. Revisar logs de época en configuración general
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key)
        
        if config:
            updates = config.get('updates', [])
            epoch_logs = [u for u in updates if u.get('type') == 'log' and 
                          (u.get('is_epoch_log') or 'epoch' in u)]
            
            # Extraer números de época
            for log in epoch_logs:
                epoch_num = log.get('epoch_number') or log.get('epoch')
                if epoch_num and isinstance(epoch_num, (int, str)) and str(epoch_num).isdigit():
                    epoch_num = int(epoch_num)
                    if epoch_num not in result['in_cache']['epochs_found']:
                        result['in_cache']['epochs_found'].append(epoch_num)
                    result['in_cache']['count'] += 1
                    result['total_found'] += 1
        else:
            result['issues'].append({
                'type': 'cache_missing',
                'message': 'No se encontró configuración en caché para este entrenamiento'
            })

        # MEJORA: También buscar en la caché genérica por clave de training_id
        status_key = f'training_status_{training_id}'
        training_status = cache.get(status_key)
        if training_status:
            status_epoch_logs = training_status.get('epoch_logs', [])
            for epoch_num in status_epoch_logs:
                if epoch_num not in result['in_cache']['epochs_found']:
                    result['in_cache']['epochs_found'].append(epoch_num)
                    result['in_cache']['count'] += 1
                    result['total_found'] += 1

        # 3. Revisar logs en la cola IPC
        from .ipc_utils import get_queue_for_training, get_updates
        
        # Crear una copia temporal de la cola para hacer el diagnóstico
        # sin afectar la cola original
        try:
            queue = get_queue_for_training(training_id)
            result['in_queue']['queue_size'] = queue.qsize() if hasattr(queue, 'qsize') else 'unknown'
        except Exception as e:
            trace_log(f"Error al verificar cola IPC: {str(e)}", category="QUEUE_CHECK")
            result['issues'].append({
                'type': 'queue_error',
                'message': f'Error al verificar cola IPC: {str(e)}'
            })
        
        # 5. Actualizar estado de proceso activo según todo lo analizado
        result['process_info']['is_active'] = process_active
        
        # Resultado final con información de Redis
        result['connection_status'] = {
            'redis_connected': redis_connected,
            'ipc_queue_available': hasattr(queue, 'qsize') if 'queue' in locals() else False,
            'cache_status': 'active' if config else 'missing',
            'cache_timestamp': config.get('timestamp') if config else None
        }
        
        # 6. Analizar fallos específicos de comunicación
        if result['total_found'] == 0 and not redis_connected:
            result['issues'].append({
                'type': 'no_communication',
                'message': 'No se detectó comunicación de logs de época y Redis no está conectado'
            })
        
        # Resultado final con información de Redis
        result['connection_status'] = {
            'redis_connected': redis_connected,
            'ipc_queue_available': hasattr(queue, 'qsize') if 'queue' in locals() else False,
            'cache_status': 'active' if config else 'missing',
            'cache_timestamp': config.get('timestamp') if config else None
        }
        
    except Exception as e:
        error_trace = traceback.format_exc()
        trace_log(f"Error en diagnóstico de logs de época: {str(e)}\n{error_trace}", 
                 category="DIAGNOSTIC_ERROR", include_stack=True)
        result['issues'].append({
            'type': 'diagnostic_error',
            'message': f'Error durante el diagnóstico: {str(e)}',
            'traceback': error_trace
        })
    
    return result


def get_last_updates(training_id, limit=10):
    """Obtiene las últimas actualizaciones para un entrenamiento desde el caché"""
    config_key = f'training_config_{training_id}'
    config = safe_cache_get(config_key)
    
    if config and 'updates' in config:
        updates = config['updates'][-limit:]  # Obtener las últimas 'limit' actualizaciones
        
        # Sanitizar y simplificar para la respuesta JSON
        sanitized_updates = []
        for update in updates:
            # Crear una copia para no modificar el original
            sanitized = {
                'type': update.get('type', 'unknown'),
                'timestamp': update.get('timestamp', 0),
                'is_epoch_log': update.get('is_epoch_log', False),
                'is_real_epoch': update.get('is_real_epoch', False),
                'epoch_number': update.get('epoch_number'),
                'level': update.get('level', 'info')
            }
            
            # Añadir un resumen del mensaje si existe
            if 'message' in update:
                message = update['message']
                sanitized['message_preview'] = message[:100] + '...' if len(message) > 100 else message
            
            sanitized_updates.append(sanitized)
        
        return sanitized_updates
    
    return None


@login_required
def model_status(request):
    """Devuelve el estado actual del modelo y sus métricas"""
    try:
        # Cargar las métricas desde el archivo JSON
        import os
        import json
        metrics_file = os.path.join(os.path.dirname(__file__), 'estimacion_tiempo', 'models', 'evaluation_metrics.json')
        
        if os.path.exists(metrics_file):
            with open(metrics_file, 'r') as f:
                metrics = json.load(f)
        else:
            metrics = {
                'MSE': 0.0,
                'RMSE': 0.0,
                'MAE': 0.0,
                'R2': 0.0,
                'Accuracy': 0.0,
                'Precision': 0.0,
                'Recall': 0.0,
                'F1': 0.0,
            }
        
        return JsonResponse({
            'status': 'success',
            'metrics': metrics,
            'model_name': 'tiempo_estimator',
            'is_main_model': True
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': str(e)
        })


@login_required
def open_tensorboard(request):
    """Inicia TensorBoard para visualizar el entrenamiento de un modelo específico"""
    model_id = request.GET.get('model_id')
    
    if not model_id:
        return JsonResponse({'success': False, 'message': 'ID de modelo no proporcionado'})
    
    try:
        # Directorio donde se almacenan los logs de TensorBoard
        log_dir = os.path.join('logs')
        
        # Verificar si el directorio existe
        if not os.path.exists(log_dir):
            return JsonResponse({
                'success': False, 
                'message': f'No se encontraron logs de TensorBoard para el modelo {model_id}'
            })
        
        # Iniciar TensorBoard en un proceso separado
        # Esto usa el módulo tensorboard.manager para iniciar un servidor en segundo plano
        from tensorboard import program
        tb = program.TensorBoard()
        tb.configure(argv=[None, '--logdir', log_dir, '--port', '6006'])
        url = tb.launch()
        
        # Alternativamente, puedes usar un puerto fijo configurado en settings:
        # tb_port = getattr(settings, 'TENSORBOARD_PORT', 6006)
        # url = f"http://localhost:{tb_port}"
        
        return JsonResponse({
            'success': True,
            'message': 'TensorBoard iniciado correctamente',
            'url': url
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'message': f'Error al iniciar TensorBoard: {str(e)}'
        })
    

@login_required
def reload_model(request):
    """Recarga el modelo sin reiniciar la aplicación"""
    from redes_neuronales.estimacion_tiempo import estimacion_service
    try:
        # Reinicializar el servicio para cargar el nuevo modelo
        estimacion_service = None  # Liberar el modelo actual
        from redes_neuronales.estimacion_tiempo import get_estimacion_service
        service = get_estimacion_service()
        service.initialize()  # Volver a cargar el modelo
        
        # Registrar en log para auditoria
        print("[ModelReload] Modelo recargado correctamente por usuario:", request.user)
        
        return JsonResponse({
            'success': True, 
            'message': 'Modelo recargado correctamente',
            'timestamp': timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        })
    except Exception as e:
        import traceback
        print("[ModelReload] Error:", str(e))
        traceback.print_exc()
        return JsonResponse({
            'success': False, 
            'message': f'Error al recargar el modelo: {str(e)}'
        }, status=500)
    
    