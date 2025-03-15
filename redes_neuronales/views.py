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
        normalized_mse = normalize_metric(
            current_metrics.get('MSE', 0), 'MSE', metrics_history
        )
        normalized_mae = normalize_metric(
            current_metrics.get('MAE', 0), 'MAE', metrics_history
        )
        normalized_r2 = normalize_metric(
            current_metrics.get('R2', 0), 'R2', metrics_history
        )
        normalized_acc = normalize_metric(
            current_metrics.get('Accuracy', 0), 'Accuracy', metrics_history
        )

        # Ponderación de métricas (ajustar según la importancia relativa)
        weights = {'mse': 0.25, 'mae': 0.25, 'r2': 0.25, 'acc': 0.25}

        # Calcular precisión global ponderada
        global_precision = (
            normalized_mse * weights['mse']
            + normalized_mae * weights['mae']
            + normalized_r2 * weights['r2']
            + normalized_acc * weights['acc']
        )

        return float(global_precision)
    except Exception as e:
        print(f"Error al calcular precisión global: {e}")
        return 0.5  # Valor predeterminado en caso de error


@login_required
def dashboard(request):
    """Renderiza el dashboard de métricas de la red neuronal"""
    try:
        with open(
            'redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r'
        ) as f:
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
                global_precision = calculate_global_precision(
                    metrics_data, metrics_history
                )
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
            timestamp = entry.get(
                'timestamp', entry.get('date', entry.get('created_at', ''))
            )

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


# falta adaptar al nuevo modelo
@login_required
def estimate_time(request):
    if request.method == 'POST':
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            REDES_DIR = os.path.join(BASE_DIR, 'redes_neuronales')
            MODEL_DIR = os.path.join(BASE_DIR, "redes_neuronales", "models")

            if REDES_DIR not in sys.path:
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
        with open(
            'redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r'
        ) as f:
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
            'model_version': '1.2.0',
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
        with open(
            'redes_neuronales/estimacion_tiempo/models/evaluation_metrics.json', 'r'
        ) as f:
            evaluation_metrics = json.load(f)
        context['evaluation_metrics'] = evaluation_metrics
    except Exception as e:
        print(f"Error al cargar métricas de evaluación: {e}")
        context['evaluation_metrics'] = (
            latest_metrics.get('metrics', {}) if latest_metrics else {}
        )

    try:
        with open(
            'redes_neuronales/estimacion_tiempo/models/segmented_evaluation.json', 'r'
        ) as f:
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
                data.append(
                    {
                        'name': row['Feature'],
                        'importance': float(row['Importance']),
                        'importance_normalized': round(
                            float(row['Importance_Normalized']) * 100, 2
                        ),
                    }
                )
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


@login_required
def entrenar_modelo(request):
    """Renderiza la interfaz de entrenamiento de red neuronal"""
    try:
        with open(
            'redes_neuronales\estimacion_tiempo\models\metrics_history.json', 'r'
        ) as f:
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

    static_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'static', 'img'
    )
    neural_bg_path = os.path.join(static_dir, 'neural-bg.svg')

    if not os.path.exists(static_dir):
        os.makedirs(static_dir, exist_ok=True)

    if not os.path.exists(neural_bg_path):
        with open(neural_bg_path, 'w') as f:
            f.write(
                '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 800 600">
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
            </svg>'''
            )

    return render(request, 'redes_neuronales/entrenar_modelo.html', context)


@login_required
def iniciar_entrenamiento(request):
    """API para iniciar el proceso de entrenamiento"""
    if (
        request.method == 'POST'
        and request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    ):
        import uuid

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

        # Configuración del entrenamiento
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
            'timestamp': timezone.now().isoformat(),  # Usar timezone para consistencia
        }

        # Guardar configuración en la sesión
        request.session[f'training_config_{training_id}'] = config

        # Guardar también en caché para acceso desde procesos separados
        from django.core.cache import cache

        cache.set(f'training_config_{training_id}', config, 7200)  # 2 horas de vida

        try:
            usuario_id = request.user.idusuario

            # MODIFICADO: Usar AsyncTask en lugar de Thread directo
            from .tasks import start_training_process

            # Iniciar el proceso asíncrono
            result = start_training_process.delay(training_id, usuario_id)

            # Opcional: Guardar ID del resultado para posible cancelación
            cache.set(f'training_task_{training_id}', result.id, 7200)

        except Exception as e:
            return JsonResponse(
                {
                    'success': False,
                    'error': f'Error al iniciar el entrenamiento: {str(e)}',
                },
                status=500,
            )

        return JsonResponse(
            {
                'success': True,
                'training_id': training_id,
                'message': 'Proceso de entrenamiento iniciado',
            }
        )

    return JsonResponse(
        {
            'success': False,
            'error': 'Método no permitido o solicitud inválida',
        },
        status=400,
    )


@login_required
def monitor_entrenamiento(request):
    """Endpoint Server-Sent Events para monitorear el progreso del entrenamiento"""
    training_id = request.GET.get('training_id')

    if not training_id:
        return JsonResponse(
            {
                'success': False,
                'error': 'ID de entrenamiento no proporcionado',
            },
            status=400,
        )

    # Verificar existencia del entrenamiento en sesión o cache
    from django.core.cache import cache

    config_key = f'training_config_{training_id}'
    config = cache.get(config_key)

    if not config and f'training_config_{training_id}' not in request.session:
        return JsonResponse(
            {
                'success': False,
                'error': 'Sesión de entrenamiento no encontrada',
            },
            status=404,
        )

    # Configurar la respuesta de streaming con eventos del servidor
    response = StreamingHttpResponse(
        _stream_training_updates(training_id, request.session),
        content_type='text/event-stream',
    )
    # Configurar headers para evitar caché y buffering
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    response['Access-Control-Allow-Origin'] = '*'  # Para CORS si es necesario

    return response


def _stream_training_updates(training_id, session):
    """Función generadora para enviar actualizaciones SSE con mejor responsividad"""
    import time
    import json
    from django.core.cache import cache

    # Parámetros optimizados para máxima responsividad
    poll_interval = 0.1  # Reducido a 0.1s para actualización más rápida
    heartbeat_interval = 1.0  # Enviar heartbeat cada segundo
    last_update_count = 0
    last_heartbeat_time = 0
    last_epoch_data = None

    # Enviar estado inicial inmediatamente para mejor feedback al usuario
    initial_update = {
        'type': 'log',
        'message': 'Conexión establecida con el servidor',
        'level': 'info',
        'timestamp': time.time(),
    }
    yield f'data: {json.dumps(initial_update)}\n\n'

    while True:
        current_time = time.time()
        config_key = f'training_config_{training_id}'
        config = cache.get(config_key) or session.get(config_key)

        # Verificar si hay configuración disponible
        if not config:
            yield f'data: {json.dumps({"type": "log", "message": "Esperando datos del entrenamiento...", "level": "info"})}\n\n'
            time.sleep(1)  # Esperar más tiempo si no hay configuración
            continue

        # Enviar heartbeat periódico para mantener la conexión viva
        if current_time - last_heartbeat_time >= heartbeat_interval:
            yield f'event: heartbeat\ndata: {json.dumps({"timestamp": current_time, "training_id": training_id})}\n\n'
            last_heartbeat_time = current_time

        # Procesar actualizaciones pendientes
        updates = config.get('updates', [])

        if len(updates) > last_update_count:
            # Procesar solo las nuevas actualizaciones
            for i in range(last_update_count, len(updates)):
                update = updates[i]
                update_type = update.get('type')

                # Enriquecer datos de progreso cuando sea posible
                if update_type == 'progress':
                    # Guardar datos de época para uso posterior en actualizaciones de batch
                    if update.get('stage') == 'epoch_end':
                        last_epoch_data = update.copy()

                        # Asegurar que campos cruciales estén presentes
                        for field in ['train_loss', 'val_loss', 'train_mae', 'val_mae']:
                            if field not in update:
                                update[field] = 0.0

                        # Información textual adicional
                        update['status_text'] = (
                            f"Época {update.get('epoch', 0)}/{update.get('total_epochs', 0)}"
                        )

                    yield f'event: progress\ndata: {json.dumps(update)}\n\n'

                elif update_type == 'batch_progress':
                    # Enriquecer con datos de la época actual si están disponibles
                    if last_epoch_data:
                        if 'epoch' not in update and 'epoch' in last_epoch_data:
                            update['epoch'] = last_epoch_data['epoch']
                        if (
                            'total_epochs' not in update
                            and 'total_epochs' in last_epoch_data
                        ):
                            update['total_epochs'] = last_epoch_data['total_epochs']

                    yield f'event: batch_progress\ndata: {json.dumps(update)}\n\n'

                elif update_type == 'complete':
                    # Indicar finalización exitosa
                    yield f'event: complete\ndata: {json.dumps(update)}\n\n'
                    # Esperar un momento para asegurar recepción antes de cerrar
                    time.sleep(0.2)
                    yield f'event: close\ndata: {json.dumps({"message": "Entrenamiento finalizado con éxito"})}\n\n'
                    return  # Terminar stream después de complete

                elif update_type == 'error':
                    # Indicar error
                    yield f'event: error\ndata: {json.dumps(update)}\n\n'
                    # Esperar un momento para asegurar recepción antes de cerrar
                    time.sleep(0.2)
                    yield f'event: close\ndata: {json.dumps({"message": "Entrenamiento fallido"})}\n\n'
                    return  # Terminar stream después de error

                elif update_type == 'post_processing_complete':
                    # Indicar finalización del post-procesamiento
                    yield f'event: post_processing_complete\ndata: {json.dumps(update)}\n\n'
                    # Esperar un momento para asegurar recepción antes de cerrar
                    time.sleep(0.2)
                    yield f'event: close\ndata: {json.dumps({"message": "Procesamiento completo"})}\n\n'
                    return  # Terminar stream

                else:
                    # Para otros tipos de actualizaciones (logs, etc.)
                    yield f'data: {json.dumps(update)}\n\n'

            # Actualizar contador de actualizaciones procesadas
            last_update_count = len(updates)

        # Verificar finalización por estado
        if config.get('status') in ['completed', 'failed']:
            # Si llegamos aquí y no se ha procesado el evento de finalización específico,
            # enviar un evento de cierre genérico
            message = (
                "Entrenamiento completado"
                if config.get('status') == 'completed'
                else "Entrenamiento fallido"
            )
            yield f'event: close\ndata: {json.dumps({"message": message})}\n\n'
            break

        # Breve pausa antes de la siguiente verificación
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
                return JsonResponse(
                    {
                        'success': False,
                        'message': f'Faltan archivos necesarios: {", ".join(model_check["missing_files"][:3])}',
                    }
                )

            # Generar archivos
            result = generate_evaluation_files(request)
            return JsonResponse(result)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Error al generar archivos de evaluación: {str(e)}',
                }
            )

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})


@login_required
def model_status(request):
    """Obtener estado actual del modelo para actualizar la interfaz"""
    try:
        from .views_utils import get_model_status

        status = get_model_status()
        return JsonResponse(status)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


@login_required
def evaluar_modelo(request):
    """API para evaluar un modelo entrenado"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            model_id = data.get('model_id')

            # Obtener el directorio de modelos
            models_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')

            # Importar el evaluador
            from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator

            # Cargar el modelo
            from redes_neuronales.estimacion_tiempo.rnn_model import (
                AdvancedRNNEstimator,
            )

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
                'Complejidad',
                'Cantidad_Recursos',
                'Carga_Trabajo_R1',
                'Experiencia_R1',
                'Carga_Trabajo_R2',
                'Experiencia_R2',
                'Carga_Trabajo_R3',
                'Experiencia_R3',
                'Experiencia_Equipo',
                'Claridad_Requisitos',
                'Tamaño_Tarea',
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
                'grandes': lambda y: y > 30,
            }
            evaluator.segmented_evaluation(X_val, y_val, segments)

            return JsonResponse({'success': True, 'metrics': metrics})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Método no permitido'})
