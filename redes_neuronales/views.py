from django.shortcuts import render
import json
import numpy as np
import tensorflow as tf
import joblib
from datetime import datetime
from django.http import JsonResponse, StreamingHttpResponse
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
            'updates': [],  # IMPORTANTE: Inicializar array de actualizaciones vacío
            'timestamp': timezone.now().isoformat()  # Usar timezone para consistencia
        }
        
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
    """Función generadora para enviar actualizaciones SSE con mejor responsividad"""
    import time
    import json
    import re
    import traceback
    from redes_neuronales.ipc_utils import get_updates, dump_queue_status
    from redes_neuronales.debug_utils import trace_log, inspect_queue, verify_connections
    from django.core.cache import cache
    
    # Diagnóstico inicial
    trace_log(f"Iniciando stream para training_id={training_id}", category="STREAM")
    
    # Parámetros optimizados para máxima responsividad
    poll_interval = 0.03  # Reducido para actualización más inmediata 
    last_update_count = 0
    last_heartbeat_time = 0
    last_debug_time = 0
    last_diagnostic_time = 0
    start_monitoring_time = time.time()  # Registrar cuándo iniciamos el monitoreo
    
    # Variables para seguimiento
    cycles_without_updates = 0
    total_epochs_seen = set()
    total_updates_received = 0
    total_epoch_logs_received = 0
    
    # NUEVO: Ajuste de umbrales para diagnósticos
    warning_threshold = 1000  # AUMENTADO: De 200/300 a 1000 ciclos (30 segundos aprox.)
    info_threshold = 500      # Nuevo umbral para logs informativos
    
    # Creamos conjunto para rastrear los logs de época ya enviados
    epoch_logs_sent = set()
    # Rastreo de la última época verificada para epoch_log_X claves especializadas
    last_epoch_checked = 0
    next_epoch_check_time = 0
    
    # Enviar estado inicial inmediatamente
    initial_update = {
        'type': 'log',
        'message': 'Conexión establecida con el servidor',
        'level': 'info',
        'timestamp': time.time()
    }
    yield f'event: log\ndata: {json.dumps(initial_update)}\n\n'
    
    # Añadir mensaje de debug para saber que estamos iniciando el streaming
    print(f"Iniciando streaming para training_id: {training_id}")
    
    # Enviar un mensaje de log explícito para verificar que la comunicación funciona
    verification_msg = {
        'type': 'log',
        'message': 'Sistema de monitorización activo - esperando datos del entrenamiento',
        'level': 'info',
        'timestamp': time.time() + 0.1
    }
    yield f'event: log\ndata: {json.dumps(verification_msg)}\n\n'
    
    # Enviar diagnóstico inicial como evento especial
    diagnostics = {
        'type': 'diagnostics',
        'message': 'Iniciando diagnóstico de comunicación',
        'timestamp': time.time(),
        'queue_status': dump_queue_status()
    }
    yield f'event: diagnostics\ndata: {json.dumps(diagnostics)}\n\n'
    
    while True:
        current_time = time.time()
        config_key = f'training_config_{training_id}'
        updates = []
        
        try:
            # Recuperar la configuración y actualizaciones desde la caché
            config = cache.get(config_key)
            
            # MODIFICACIÓN 1: Verificar primero si hay actualizaciones en caché - OPTIMIZADO
            if config and 'updates' in config:
                cache_updates = config['updates']
                
                if len(cache_updates) > last_update_count:
                    # Hay nuevas actualizaciones en caché
                    new_updates = cache_updates[last_update_count:]
                    updates.extend(new_updates)
                    
                    # Actualizar contador para la próxima verificación
                    last_update_count = len(cache_updates)
                    
                    # Resetear contador de ciclos sin actualizaciones
                    cycles_without_updates = 0
                    
                    # Registrar actualizaciones procesadas
                    total_updates_received += len(new_updates)
                    
                    # Registrar épocas vistas
                    for update in new_updates:
                        if update.get('is_epoch_log') and update.get('epoch_number'):
                            total_epochs_seen.add(update.get('epoch_number'))
                            total_epoch_logs_received += 1
                else:
                    # No hay actualizaciones nuevas en caché, incrementar contador
                    cycles_without_updates += 1
            else:
                # No se encontró configuración o no tiene actualizaciones
                cycles_without_updates += 1
            
            # DIAGNÓSTICO: Ejecutar verificación periódica (cada 15 segundos)
            if current_time - last_diagnostic_time > 15:
                last_diagnostic_time = current_time
                
                # NUEVO: Evaluación progresiva según la gravedad
                if cycles_without_updates > warning_threshold:
                    # Solo reportar como advertencia después de muchos ciclos
                    connections = verify_connections(training_id)
                    
                    # MODIFICADO: Usar nivel INFO en lugar de WARNING
                    trace_log(f"Muchos ciclos sin actualizaciones: {cycles_without_updates}", 
                             category="INFO", include_stack=False)
                    
                    # Solo mostrar WARN después de 2 minutos sin updates
                    if current_time - start_monitoring_time > 120 and len(total_epochs_seen) == 0:
                        trace_log(f"Posible problema de comunicación: {connections}", 
                                 category="WARNING", include_stack=False)
                
                elif cycles_without_updates > info_threshold:
                    # Reportar como INFO si supera el umbral informativo pero no el de advertencia
                    trace_log(f"Varios ciclos sin actualizaciones: {cycles_without_updates}", 
                             category="DEBUG", include_stack=False)
            
            # MODIFICACIÓN 2: Solo intentar recuperar desde la cola cada 5 ciclos
            if not updates and cycles_without_updates % 5 == 0:
                # Intentar obtener desde la cola IPC solo ocasionalmente para reducir carga
                ipc_updates = get_updates(training_id)
                if ipc_updates:
                    updates.extend(ipc_updates)
                    cycles_without_updates = 0
                    
                    # Registrar actualizaciones procesadas
                    total_updates_received += len(ipc_updates)
            
            # Enviar heartbeat cada segundo
            if current_time - last_heartbeat_time >= 1.0:
                heartbeat_data = {
                    "timestamp": current_time,
                    "stats": {
                        "cycles": cycles_without_updates,
                        "total_updates": total_updates_received,
                        "epochs_seen": len(total_epochs_seen),
                        "monitoring_time": int(current_time - start_monitoring_time)
                    }
                }
                yield f'event: heartbeat\ndata: {json.dumps(heartbeat_data)}\n\n'
                last_heartbeat_time = current_time
            
            # Procesar actualizaciones recibidas
            for update in updates:
                # Determinar el tipo de evento según el contenido
                event_type = update.get('type', 'log')
                
                # Serializar la actualización a JSON y enviarla
                update_json = json.dumps(update)
                yield f'event: {event_type}\ndata: {update_json}\n\n'
            
            # Verificar si el entrenamiento ha terminado
            if config and config.get('status') in ['completed', 'failed']:
                if not updates:  # Solo cerramos si no hay más actualizaciones
                    trace_log(f"Entrenamiento terminado con estado: {config.get('status')}. Cerrando stream.", category="STREAM_END")
                    
                    # NUEVO: Enviar evento complete con los resultados finales antes de cerrar
                    # Obtener métricas finales si están disponibles
                    final_metrics = {}
                    training_results = {}
                    
                    # Intentar obtener métricas finales desde la configuración
                    if config.get('metrics'):
                        final_metrics = config.get('metrics')
                    if config.get('results'):
                        training_results = config.get('results')
                    
                    # Construir respuesta de finalización completa
                    complete_data = {
                        'status': config.get('status'),
                        'timestamp': time.time(),
                        'training_id': training_id,
                        'message': 'Entrenamiento finalizado',
                        'metrics': final_metrics,
                        'results': training_results,
                        'model_id': training_id,
                        'model_name': config.get('model_name', 'tiempo_estimator')
                    }
                    
                    # Emitir evento complete con los resultados
                    yield f'event: complete\ndata: {json.dumps(complete_data)}\n\n'
                    
                    # Emitir evento de cierre después del complete
                    yield f'event: close\ndata: {json.dumps({"message": "Stream finalizado correctamente"})}\n\n'
                    break
            
            # Si no hay actualizaciones, añadir un pequeño retraso para evitar CPU al 100%
            if not updates:
                time.sleep(poll_interval)

        except Exception as e:
            error_trace = traceback.format_exc()
            trace_log(f"Error en stream de actualizaciones: {str(e)}\n{error_trace}", 
                     category="STREAM_ERROR", include_stack=True)
            
            # Pequeño retraso antes de continuar
            time.sleep(0.5)
        
        # Esperar un pequeño tiempo antes de la siguiente actualización
        time.sleep(poll_interval)

@login_required
def generar_archivos_evaluacion(request):
    """Vista para generar archivos de evaluación para un modelo existente"""
    if request.method == 'POST':
        try:
            # Importar utilidades
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
            evaluator.segmented_evaluation(X_val, y_val, segments)
            
            # Construir rutas para las imágenes generadas
            # IMPORTANTE: Ahora apuntan al directorio de modelos para acceso via backend
            image_paths = {
                'feature_importance': os.path.join(models_dir, 'global_feature_importance.png'),
                'evaluation_plots': os.path.join(models_dir, 'evaluation_plots.png'),
                'segmented_metrics': os.path.join(models_dir, 'segmented_metrics.png')
            }
            
            print("Evaluación completa. Enviando resultados...")
            # Devolver respuesta de éxito con métricas y rutas de imágenes
            return JsonResponse({
                'success': True,
                'message': 'Evaluación completada con éxito',
                'metrics': metrics,
                'files_location': models_dir,  # Informar dónde están los archivos
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
