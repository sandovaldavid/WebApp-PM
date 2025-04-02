import os
import sys
import numpy as np
import pandas as pd
import time
import json
import traceback
import joblib
from datetime import datetime

# Configurar el path del proyecto Django
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

import django

django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from tensorflow.keras.callbacks import Callback


def _get_training_config(training_id, max_retries=3):
    """
    Obtiene la configuración de entrenamiento desde la caché con reintentos.

    Args:
        training_id: ID único del entrenamiento
        max_retries: Número máximo de reintentos si hay problemas de caché

    Returns:
        dict: Configuración del entrenamiento o None si no se encuentra
    """
    from django.core.cache import cache

    config = None
    retry_count = 0

    while not config and retry_count < max_retries:
        try:
            config = cache.get(f"training_config_{training_id}")
            if config:
                return config

            # Pequeña pausa antes de reintentar
            if retry_count > 0:
                time.sleep(0.1)

            retry_count += 1
        except Exception as e:
            print(
                f"Error al obtener la configuración del entrenamiento (intento {retry_count}): {str(e)}"
            )
            retry_count += 1

    return config


def _validate_complete_data(update_data):
    """
    Valida que los datos de actualización de tipo 'complete' tengan la estructura correcta
    """
    required_fields = ["metrics", "model_id"]
    for field in required_fields:
        if field not in update_data:
            # Ajustar campo faltante con un valor por defecto
            if field == "metrics":
                update_data["metrics"] = {"MSE": 0, "MAE": 0, "RMSE": 0, "R2": 0}
            elif field == "model_id":
                update_data["model_id"] = update_data.get("training_id", "unknown")


def _add_update(training_id, update_data):
    """Añade una actualización al cache para ser enviada al cliente"""
    # Importar cache explícitamente
    from django.core.cache import cache

    # Añadir timestamp si no existe
    if "timestamp" not in update_data:
        update_data["timestamp"] = time.time()

    # Manejo especial para actualización de tipo 'complete'
    if update_data.get("type") == "complete":
        _validate_complete_data(update_data)

    # Manejo especial para logs de época
    if "epoch" in update_data and "total_epochs" in update_data:
        if not update_data.get("is_epoch_log"):
            update_data["is_epoch_log"] = True

    # Obtener configuración (con reintentos)
    config = _get_training_config(training_id)

    # Actualizar y guardar config
    if config:
        if "updates" not in config:
            config["updates"] = []

        config["updates"].append(update_data)
        config["last_activity_time"] = time.time()

        # Limitar cantidad de actualizaciones
        if len(config["updates"]) > 1000:
            config["updates"] = config["updates"][-1000:]

        # Guardar en caché
        return cache.set(f"training_config_{training_id}", config, 7200)  # 2 horas
    else:
        # Crear config inicial si no existe
        new_config = {
            "status": "running",
            "updates": [update_data],
            "last_activity_time": time.time(),
        }
        return cache.set(f"training_config_{training_id}", new_config, 7200)


def ejecutar_entrenamiento(training_id, user_id):
    """
    Ejecuta el proceso de entrenamiento en segundo plano y envía actualizaciones al frontend.

    Args:
        training_id: ID único del proceso de entrenamiento
        user_id: ID del usuario que inició el entrenamiento

    Returns:
        bool: True si el entrenamiento se completó con éxito, False en caso contrario
    """
    # Importar cache explícitamente al inicio de la función
    from django.core.cache import cache

    # Guardar la asociación del usuario con el entrenamiento en cache
    cache.set(f"training_user_{training_id}", user_id, 3600)  # 1 hora de tiempo de vida

    # Notificar inicio
    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Iniciando proceso de entrenamiento...",
            "level": "info",
        },
    )

    try:
        # Configuración para matplotlib si se usa
        _configurar_matplotlib()

        # Obtener configuración del entrenamiento
        config = _obtener_config_entrenamiento(training_id, user_id)

        # 1. Cargar y preparar datos
        data, processor = _cargar_datos(training_id, config)

        # 2. Preprocesar datos
        X_train, X_val, y_train, y_val, feature_dims = _preprocesar_datos(
            training_id, config, processor, data
        )

        # 3. Crear y configurar modelo
        estimator = _configurar_modelo(training_id, config, feature_dims)

        # 4. Entrenar modelo
        history, epoch_logs = _entrenar_modelo(
            training_id, config, estimator, X_train, y_train, X_val, y_val, feature_dims
        )

        # 5. Evaluar modelo
        metrics, y_pred = _evaluar_modelo(
            training_id, estimator, X_val, y_val, feature_dims
        )

        # 6. Guardar modelo
        _guardar_modelo(training_id, config, estimator)

        # 7. Actualizar registro en base de datos
        _actualizar_registro_bd(training_id, config, metrics)

        # 8. Preparar resultados para frontend
        loss_history, predictions_sample, actual_sample = _preparar_resultados_frontend(
            history, y_pred, y_val
        )

        # 9. Actualizar estado a completado y enviar evento complete
        _completar_entrenamiento(
            training_id,
            config,
            metrics=metrics,
            history=loss_history,
            predictions=predictions_sample,
            y_test=actual_sample,
            epoch_logs=epoch_logs,
        )

        # 10. Iniciar tareas de post-procesamiento
        _iniciar_tareas_posteriores(training_id)

        print(f"Entrenamiento {training_id} completado exitosamente.")
        return True

    except Exception as e:
        # Manejar excepciones y registrar errores
        _manejar_error_entrenamiento(training_id, e)
        return False


def _configurar_matplotlib():
    """Configura matplotlib para uso no interactivo"""
    import os

    os.environ["MPLBACKEND"] = "Agg"
    import matplotlib

    matplotlib.use("Agg")


def _obtener_config_entrenamiento(training_id, user_id):
    """Obtiene la configuración del entrenamiento desde la caché o la sesión"""
    from django.core.cache import cache

    config_key = f"training_config_{training_id}"
    config = cache.get(config_key)

    if not config:
        # Si no está en el cache, cargar desde la sesión de Django
        config = _buscar_config_en_sesion(training_id, user_id)

    if not config:
        raise ValueError("No se encontró la configuración del entrenamiento")

    # Actualizar estado
    config["status"] = "running"
    cache.set(config_key, config, 3600)

    return config


def _buscar_config_en_sesion(training_id, user_id):
    """Busca la configuración de entrenamiento en las sesiones activas"""
    from django.contrib.sessions.models import Session
    from django.contrib.sessions.backends.db import SessionStore

    User = get_user_model()
    config_key = f"training_config_{training_id}"

    try:
        # Buscar el usuario
        user = User.objects.get(idusuario=user_id)

        # Buscar en todas las sesiones activas
        for session in Session.objects.all():
            session_data = session.get_decoded()
            if session_data.get("_auth_user_id") and str(user.idusuario) == str(
                session_data.get("_auth_user_id")
            ):
                store = SessionStore(session_key=session.session_key)
                config = store.get(config_key)
                if config:
                    return config
    except Exception as e:
        print(f"Error al buscar configuración en sesión: {e}")

    return None


def _cargar_datos(training_id, config):
    """Carga los datos según el método seleccionado (CSV o DB)"""
    from redes_neuronales.estimacion_tiempo.data_processor import DataProcessor

    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Preparando datos de entrenamiento...",
            "level": "info",
        },
    )

    if config["training_method"] == "csv":
        # Método CSV
        if not config["data_path"] or not os.path.exists(config["data_path"]):
            raise ValueError(f"Archivo CSV no encontrado en: {config['data_path']}")

        processor = DataProcessor(data_path=config["data_path"])
        data = processor.load_data()

        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Datos cargados desde CSV. {len(data)} registros encontrados.",
                "level": "info",
            },
        )
    else:
        # Método DB
        processor, data = _cargar_datos_desde_db(training_id, config)

    # Verificar que hay suficientes datos
    if data is None or len(data) < 10:
        raise ValueError(
            f"Conjunto de datos insuficiente. Se necesitan al menos 10 registros, se encontraron {0 if data is None else len(data)}."
        )

    return data, processor


def _cargar_datos_desde_db(training_id, config):
    """Carga datos desde la base de datos, opcionalmente generando datos sintéticos"""
    from redes_neuronales.estimacion_tiempo.data_processor import DataProcessor

    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Cargando datos desde la base de datos...",
            "level": "info",
        },
    )

    processor = DataProcessor(use_db=True)

    if config["use_synthetic"]:
        # Generar datos sintéticos
        return _generar_datos_sinteticos(training_id, processor)
    else:
        # Cargar directamente desde la DB
        data = processor.load_data_from_db()

        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Datos cargados desde la base de datos. {len(data)} registros encontrados.",
                "level": "info",
            },
        )

        return processor, data


def _generar_datos_sinteticos(training_id, processor):
    """Genera datos sintéticos para aumentar el conjunto de entrenamiento"""
    from redes_neuronales.estimacion_tiempo.datos_sinteticos import (
        generar_datos_monte_carlo,
    )
    import tempfile

    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Generando datos sintéticos para aumentar el conjunto de entrenamiento...",
            "level": "info",
        },
    )

    # Generar paths temporales
    temp_dir = tempfile.gettempdir()
    temp_input = os.path.join(temp_dir, f"db_data_{training_id}.csv")
    temp_output = os.path.join(temp_dir, f"synthetic_data_{training_id}.csv")

    # Obtener datos de la DB y guardarlos temporalmente
    processor.load_data_from_db(save_path=temp_input)

    # Generar datos sintéticos
    generar_datos_monte_carlo(temp_input, 2000, temp_output)

    # Cargar los datos combinados
    processor.data_path = temp_output
    data = processor.load_data()

    _add_update(
        training_id,
        {
            "type": "log",
            "message": f"Datos combinados generados. {len(data)} registros disponibles.",
            "level": "success",
        },
    )

    return processor, data


def _preprocesar_datos(training_id, config, processor, data):
    """Preprocesa los datos para el entrenamiento"""
    _add_update(
        training_id,
        {"type": "log", "message": "Preprocesando datos...", "level": "info"},
    )

    # Preprocesar datos
    X_train, X_val, y_train, y_val, feature_dims = processor.preprocess_data(
        test_size=config["test_size"], val_size=config["validation_size"]
    )

    # Guardar los preprocesadores y datos de validación
    output_dir = os.path.join("redes_neuronales", "estimacion_tiempo", "models")
    os.makedirs(output_dir, exist_ok=True)
    processor.save_preprocessors(output_dir=output_dir)

    # Guardar explícitamente los datos de validación para evaluación posterior
    _guardar_datos_validacion(X_val, y_val, feature_dims, output_dir)

    _add_update(
        training_id,
        {
            "type": "log",
            "message": f"Preprocesamiento completado. Conjunto de entrenamiento: {len(X_train)}, Conjunto de validación: {len(X_val)}",
            "level": "success",
        },
    )

    return X_train, X_val, y_train, y_val, feature_dims


def _guardar_datos_validacion(X_val, y_val, feature_dims, output_dir):
    """Guarda los datos de validación para uso posterior"""
    np.save(os.path.join(output_dir, "X_val.npy"), X_val)
    np.save(os.path.join(output_dir, "y_val.npy"), y_val)

    # Guardar datos completos en un archivo joblib para uso posterior
    validation_data = {"X_val": X_val, "y_val": y_val, "feature_dims": feature_dims}
    joblib.dump(validation_data, os.path.join(output_dir, "validation_data.joblib"))
    joblib.dump(feature_dims, os.path.join(output_dir, "feature_dims.pkl"))


def _configurar_modelo(training_id, config, feature_dims):
    """Configura el modelo de red neuronal"""
    from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator

    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Configurando modelo de red neural...",
            "level": "info",
        },
    )

    # Primero crear una instancia con la configuración predeterminada
    temp_estimator = AdvancedRNNEstimator()
    base_config = temp_estimator.default_config

    # Configurar el modelo sobreescribiendo los valores específicos
    model_config = base_config.copy()
    model_config.update(
        {
            "rnn_units": config["rnn_units"],
            "dropout_rate": config["dropout_rate"],
            "learning_rate": config["learning_rate"],
            "use_bidirectional": config["bidirectional"],
            "rnn_type": config["rnn_type"],
            "batch_size": config["batch_size"],
            "epochs": config["epochs"],
            # Parámetros adicionales que podrías querer exponer en la interfaz
            "optimizer": config.get("optimizer", "adam"),
            "activation": config.get("activation", "relu"),
        }
    )

    # Crear y construir el modelo con la configuración completa
    estimator = AdvancedRNNEstimator(model_config)
    estimator.build_model(feature_dims)

    _add_update(
        training_id,
        {
            "type": "log",
            "message": f'Modelo configurado: {config["rnn_type"]} {"bidireccional" if config["bidirectional"] else "unidireccional"} con {config["rnn_units"]} unidades',
            "level": "info",
        },
    )

    return estimator


def _entrenar_modelo(
    training_id, config, estimator, X_train, y_train, X_val, y_val, feature_dims
):
    """Entrena el modelo con los datos proporcionados"""
    _add_update(
        training_id,
        {
            "type": "log",
            "message": f'Iniciando entrenamiento del modelo con {config["epochs"]} épocas...',
            "level": "info",
        },
    )

    # Crear callback personalizado para monitorizar progreso
    progress_callback = ProgressCallback(training_id, config["epochs"])

    # Entrenar modelo con el callback
    history = estimator.train(
        X_train, y_train, X_val, y_val, feature_dims, callbacks=[progress_callback]
    )

    # Recolectar logs de época
    epoch_logs = _recolectar_epoch_logs(training_id)

    _add_update(
        training_id,
        {
            "type": "log",
            "message": "Entrenamiento completado. Evaluando modelo...",
            "level": "success",
        },
    )

    return history, epoch_logs


def _recolectar_epoch_logs(training_id):
    """Recolecta todos los logs de época generados durante el entrenamiento"""
    from django.core.cache import cache

    config_key = f"training_config_{training_id}"
    config = cache.get(config_key)

    epoch_logs = []
    if config and "updates" in config:
        # Filtrar todos los updates que son logs de época
        epoch_logs = [u for u in config["updates"] if u.get("is_epoch_log")]

    return epoch_logs


class ProgressCallback(Callback):
    """Callback personalizado para monitorear el progreso del entrenamiento"""

    def __init__(self, training_id, total_epochs):
        super().__init__()
        self.training_id = training_id
        self.total_epochs = total_epochs
        self.start_time = time.time()
        self.last_update_time = 0
        self.last_batch_update_time = 0
        self.epoch_log = 0

    def on_batch_end(self, batch, logs=None):
        """Maneja el evento de fin de batch"""
        current_time = time.time()
        if (
            current_time - self.last_batch_update_time >= 0.5
        ):  # Actualizar cada 0.5 segundos como máximo
            self.last_batch_update_time = current_time
            _add_update(
                self.training_id,
                {
                    "type": "batch_progress",
                    "batch": batch,
                    "loss": float(logs.get("loss", 0)),
                    "mae": float(logs.get("mae", 0)),
                    "epoch": self.epoch_log + 1,
                    "total_epochs": self.total_epochs,
                    "progress_percent": ((self.epoch_log + 1) / self.total_epochs)
                    * 100,
                    "timestamp": time.time(),
                },
            )

    def on_epoch_begin(self, epoch, logs=None):
        """Maneja el evento de inicio de época"""
        self.epoch_log = epoch
        _add_update(
            self.training_id,
            {
                "type": "progress",
                "stage": "epoch_start",
                "epoch": epoch + 1,
                "total_epochs": self.total_epochs,
                "progress_percent": (epoch / self.total_epochs) * 100,
            },
        )

    def on_epoch_end(self, epoch, logs=None):
        """Maneja el evento de fin de época"""
        logs = logs or {}

        # Calcular tiempo restante estimado
        elapsed = time.time() - self.start_time
        epoch_time = elapsed / (epoch + 1)
        remaining_epochs = self.total_epochs - (epoch + 1)
        remaining_secs = remaining_epochs * epoch_time

        # Formato de tiempo restante
        if remaining_secs > 3600:
            remaining_time = (
                f"{int(remaining_secs/3600)}h {int((remaining_secs%3600)/60)}m"
            )
        elif remaining_secs > 60:
            remaining_time = f"{int(remaining_secs/60)}m {int(remaining_secs%60)}s"
        else:
            remaining_time = f"{int(remaining_secs)}s"

        # Enviar actualización detallada
        _add_update(
            self.training_id,
            {
                "type": "progress",
                "stage": "epoch_end",
                "epoch": epoch + 1,
                "total_epochs": self.total_epochs,
                "progress_percent": ((epoch + 1) / self.total_epochs) * 100,
                "train_loss": float(logs.get("loss", 0)),
                "val_loss": float(logs.get("val_loss", 0)),
                "train_mae": float(logs.get("mae", 0)),
                "val_mae": float(logs.get("val_mae", 0)),
                "remaining_time": remaining_time,
                "elapsed_time": int(elapsed),
                "epoch_time": int(epoch_time),
                "is_epoch_log": True,
                "epoch_number": epoch + 1,
                "loss": float(logs.get("loss", 0)),
                "val_loss": float(logs.get("val_loss", 0)),
            },
        )

        # Mensaje de log para mayor compatibilidad
        if (epoch + 1) % 5 == 0 or epoch == 0 or (epoch + 1) == self.total_epochs:
            _add_update(
                self.training_id,
                {
                    "type": "log",
                    "message": f'Época {epoch + 1}/{self.total_epochs} - loss: {logs.get("loss", 0):.4f} - val_loss: {logs.get("val_loss", 0):.4f} - mae: {logs.get("mae", 0):.4f}',
                    "level": "info",
                },
            )


def _evaluar_modelo(training_id, estimator, X_val, y_val, feature_dims):
    """Evalúa el modelo y calcula métricas"""
    try:
        # Obtener predicciones
        y_pred = estimator.predict(X_val, feature_dims)

        # Calcular métricas
        from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)

        # Crear diccionario de métricas
        metrics = {
            "MSE": float(mse),
            "RMSE": float(rmse),
            "MAE": float(mae),
            "R2": float(r2),
            "Accuracy": 0.0,
        }

        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Evaluación completada. Métricas: R²: {r2:.4f}, MAE: {mae:.2f}, RMSE: {rmse:.2f}",
                "level": "success",
            },
        )

        return metrics, y_pred

    except Exception as e:
        print(f"Error durante la evaluación del modelo: {str(e)}")
        traceback.print_exc()

        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Error durante la evaluación del modelo: {str(e)}",
                "level": "warning",
            },
        )

        # Crear métricas por defecto
        metrics = {"MSE": 0.0, "RMSE": 0.0, "MAE": 0.0, "R2": 0.0, "Accuracy": 0.0}

        return metrics, np.array([])


def _guardar_modelo(training_id, config, estimator):
    """Guarda el modelo entrenado"""
    _add_update(
        training_id,
        {
            "type": "log",
            "message": f'Guardando modelo como {config["model_name"]}...',
            "level": "info",
        },
    )

    output_dir = os.path.join("redes_neuronales", "estimacion_tiempo", "models")
    timestamp = datetime.now().strftime("%Y%m%d")

    # Guardar con timestamp
    estimator.save(model_dir=output_dir, name=f'{config["model_name"]}_{timestamp}')

    # Si se marcó como modelo principal, guardar con nombre fijo
    if config["save_as_main"]:
        estimator.save(model_dir=output_dir, name="tiempo_estimator")
        _add_update(
            training_id,
            {
                "type": "log",
                "message": "Modelo establecido como principal para predicciones.",
                "level": "success",
            },
        )

    return timestamp


def _actualizar_registro_bd(training_id, config, metrics):
    """Actualiza el registro del modelo en la base de datos"""
    try:
        from dashboard.models import Modeloestimacionrnn

        timestamp = datetime.now().strftime("%Y%m%d")

        # Definir los defaults básicos
        defaults = {
            "descripcionmodelo": f'Modelo entrenado desde la interfaz web ({config["rnn_type"]} {"bidireccional" if config["bidirectional"] else "unidireccional"})',
            "versionmodelo": f"1.0.{timestamp}",
            "precision": metrics.get("R2", 0.8),
            "fechamodificacion": timezone.now(),
        }

        # Si es una creación, también establecer la fecha de creación
        modelo, created = Modeloestimacionrnn.objects.update_or_create(
            nombremodelo=config["model_name"], defaults=defaults
        )

        # Si se acaba de crear, establecer la fecha de creación
        if created:
            modelo.fechacreacion = timezone.now()
            modelo.save()

        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Registro del modelo actualizado en la base de datos.",
                "level": "success",
            },
        )

    except Exception as e:
        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"No se pudo actualizar el registro en la base de datos: {str(e)}",
                "level": "warning",
            },
        )


def _preparar_resultados_frontend(history, y_pred, y_val):
    """Prepara los resultados del entrenamiento para mostrar en el frontend"""
    # Extraer datos relevantes del historial para gráficas
    loss_history = {
        "loss": [float(val) for val in history.history["loss"]],
        "val_loss": (
            [float(val) for val in history.history["val_loss"]]
            if "val_loss" in history.history
            else []
        ),
    }

    # Preparar datos para gráfica de predicciones
    predictions_sample = []
    actual_sample = []

    # Verificar si tenemos predicciones
    if isinstance(y_pred, np.ndarray) and len(y_pred) > 0:
        # Tomar una muestra representativa (máx 100 puntos)
        max_sample = min(100, len(y_val))
        step_size = max(1, len(y_val) // max_sample)

        for i in range(0, len(y_val), step_size):
            if i < len(y_pred) and len(predictions_sample) < max_sample:
                predictions_sample.append(float(y_pred[i]))
                actual_sample.append(float(y_val[i]))
    else:
        # Datos por defecto
        predictions_sample = [0, 0]
        actual_sample = [0, 0]

    return loss_history, predictions_sample, actual_sample


def _completar_entrenamiento(
    training_id, config, metrics, history, predictions, y_test, epoch_logs
):
    """Actualiza el estado a completado y envía el evento complete"""
    from django.core.cache import cache

    # Actualizar configuración con resultados
    config_key = f"training_config_{training_id}"

    # Crear estructura de resultado completa
    result = {
        "metrics": metrics,
        "history": history,
        "predictions": predictions,
        "y_test": y_test,
        "epoch_logs": epoch_logs,
        "model_id": training_id,
        "model_name": config["model_name"],
        "is_main_model": config["save_as_main"],
        "timestamp": timezone.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Actualizar config con resultado
    config["status"] = "completed"
    config["result"] = result
    cache.set(config_key, config, 7200)  # 2 horas de tiempo de vida

    # Enviar evento complete con todos los datos necesarios
    _add_update(
        training_id,
        {
            "type": "complete",
            "metrics": metrics,
            "history": history,
            "predictions": predictions,
            "y_test": y_test,
            "epoch_logs": epoch_logs,
            "model_id": training_id,
            "model_name": config["model_name"],
            "save_as_main": config["save_as_main"],
            "message": "Entrenamiento finalizado exitosamente.",
        },
    )

    # Notificar finalización por log
    _add_update(
        training_id,
        {
            "type": "log",
            "message": "✅ Proceso de entrenamiento completado. El modelo está listo para ser utilizado.",
            "level": "success",
        },
    )


def _iniciar_tareas_posteriores(training_id):
    """Inicia las tareas posteriores al entrenamiento"""
    try:
        _add_update(
            training_id,
            {
                "type": "log",
                "message": "Iniciando generación de archivos adicionales...",
                "level": "info",
            },
        )

        from redes_neuronales.estimacion_tiempo.post_training_tasks import (
            start_background_tasks,
        )

        start_background_tasks(training_id)

        _add_update(
            training_id,
            {
                "type": "log",
                "message": "Proceso de generación de archivos iniciado en segundo plano.",
                "level": "info",
            },
        )

    except Exception as e:
        print(f"Error al iniciar tareas posteriores al entrenamiento: {str(e)}")
        _add_update(
            training_id,
            {
                "type": "log",
                "message": f"Advertencia: No se pudieron iniciar algunas tareas adicionales. {str(e)}",
                "level": "warning",
            },
        )


def _manejar_error_entrenamiento(training_id, exception):
    """Maneja los errores durante el entrenamiento"""
    from django.core.cache import cache

    # Registrar el error detalladamente
    error_trace = traceback.format_exc()
    print(f"Error en entrenamiento {training_id}: {str(exception)}\n{error_trace}")

    # Actualizar el estado en caché para reflejar el error
    config_key = f"training_config_{training_id}"
    config = cache.get(config_key)

    if config:
        # Asegurar que exista la lista de actualizaciones
        if "updates" not in config:
            config["updates"] = []

        # Añadir actualización de error
        config["status"] = "failed"
        config["updates"].append(
            {
                "type": "error",
                "message": f"Error en el entrenamiento: {str(exception)}",
                "error_detail": str(exception),
                "timestamp": time.time(),
            }
        )

        # Guardar en caché
        cache.set(config_key, config, 7200)  # 2 horas de tiempo de vida

    # Notificar al frontend
    _add_update(
        training_id,
        {
            "type": "error",
            "message": f"Error en el entrenamiento: {str(exception)}",
            "level": "error",
            "details": error_trace.split("\n")[-5:] if error_trace else [],
            "timestamp": time.time(),
        },
    )

    # También enviar un evento de finalización con error para que el UI pueda responder adecuadamente
    _add_update(
        training_id,
        {
            "type": "complete",
            "status": "failed",
            "message": "El entrenamiento falló debido a un error",
            "error": str(exception),
            "model_id": training_id,
        },
    )


def verificar_estado_entrenamiento(training_id):
    """
    Verifica el estado actual de un entrenamiento.

    Args:
        training_id: ID del entrenamiento a verificar

    Returns:
        dict: Estado actual del entrenamiento con métricas si está completo
    """
    from django.core.cache import cache

    config_key = f"training_config_{training_id}"
    config = cache.get(config_key)

    if not config:
        return {"status": "not_found", "message": "Entrenamiento no encontrado"}

    result = {
        "status": config.get("status", "unknown"),
        "timestamp": config.get("last_activity_time", time.time()),
        "training_id": training_id,
    }

    # Si está completado, añadir métricas y resultados
    if config.get("status") == "completed" and "result" in config:
        result["metrics"] = config["result"].get("metrics", {})
        result["model_name"] = config["result"].get("model_name", "")

    return result
