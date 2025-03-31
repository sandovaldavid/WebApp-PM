import os
import logging
from django.conf import settings
import numpy as np
import joblib

# Configuración de logging
logger = logging.getLogger(__name__)


class EstimacionService:
    """
    Servicio para cargar y utilizar el modelo de estimación de tiempo en producción
    """

    _instance = None

    def __new__(cls):
        """Implementa patrón singleton para no recargar el modelo constantemente"""
        if cls._instance is None:
            cls._instance = super(EstimacionService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self.model = None
        self.processor = None
        self.feature_dims = None
        self.scalers = None
        self.encoders = None
        self._load_model()
        self._initialized = True

    def _load_model(self):
        """Carga el modelo de estimación de tiempo entrenado"""
        try:
            # Primero intentar cargar el modelo avanzado RNN
            from redes_neuronales.estimacion_tiempo.rnn_model import (
                AdvancedRNNEstimator,
            )
            from redes_neuronales.estimacion_tiempo.data_processor import DataProcessor

            # Definir rutas de modelos (modelo principal y fallback)
            models_dir = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "redes_neuronales",
                "estimacion_tiempo",
                "models",
            )

            # Verificar que exista el directorio
            if not os.path.exists(models_dir):
                logger.warning(f"Directorio de modelos no encontrado: {models_dir}")
                models_dir = os.path.join(os.path.dirname(__file__), "models")

            # Cargar el procesador de datos primero
            self.processor = DataProcessor()
            if not self.processor.load_preprocessors(models_dir):
                logger.warning(
                    "No se pudieron cargar los preprocessors del modelo avanzado"
                )
                raise Exception("Error al cargar preprocessors")

            # Intentar cargar modelo avanzado
            try:
                self.model = AdvancedRNNEstimator.load(models_dir, "tiempo_estimator")
                self.feature_dims = self.processor.feature_dims
                logger.info("Modelo avanzado de estimación RNN cargado correctamente")
                self.model_type = "advanced"
                return
            except Exception as e:
                logger.warning(f"Error al cargar el modelo RNN avanzado: {e}")

            # Si falla, intentar cargar el modelo simple
            try:
                from redes_neuronales.ml_model import EstimacionModel

                # Cargar escaladores y encoders
                self.scalers = joblib.load(os.path.join(models_dir, "scaler.pkl"))
                self.encoders = joblib.load(
                    os.path.join(models_dir, "preprocessor.pkl")
                )

                # Configuración básica para el modelo
                config = {"vocab_size": 10, "dropout_rate": 0.2}
                self.model = EstimacionModel(config)

                # Cargar los pesos del modelo
                model_path = os.path.join(models_dir, "modelo_estimacion.keras")
                if os.path.exists(model_path):
                    self.model.model.load_weights(model_path)
                    logger.info("Modelo básico de estimación cargado correctamente")
                    self.model_type = "basic"
                    return
                else:
                    logger.error(
                        f"No se encuentra el archivo de modelo en: {model_path}"
                    )
            except Exception as e:
                logger.error(f"Error al cargar el modelo básico: {e}")

            raise Exception("No se pudo cargar ningún modelo de estimación")

        except Exception as e:
            logger.error(f"Error al cargar el modelo de estimación: {e}")
            self.model = None
            self.processor = None

    def estimar_tiempo_tarea(self, tarea_data):
        """
        Estima el tiempo para una tarea basada en sus características

        Args:
            tarea_data: Diccionario con características de la tarea

        Returns:
            dict: Resultado con tiempo estimado y metadatos
        """
        if not self.model:
            raise Exception("El modelo de estimación no está disponible")

        try:
            # Log para depuración de los datos recibidos
            logger.debug(f"Datos recibidos para estimación: {tarea_data}")

            # Verificamos que las claves necesarias existan
            required_keys = [
                "complejidad",
                "tipo_tarea",
                "fase_tarea",
                "cantidad_recursos",
            ]
            for key in required_keys:
                if key not in tarea_data:
                    logger.error(f"Falta la clave {key} en los datos de entrada")
                    raise ValueError(f"Falta parámetro necesario: {key}")

            # Preparar datos para el modelo según el tipo
            if self.model_type == "advanced":
                # Procesar datos para modelo avanzado
                X = self.processor.process_single_task(tarea_data)
                logger.debug(f"Datos procesados para modelo avanzado: {X}")
                prediction = self.model.predict(X, self.feature_dims)
                tiempo_estimado = float(prediction[0])

                return {
                    "tiempo_estimado": tiempo_estimado,
                    "unidad": "horas",
                    "modelo": "RNN avanzado",
                    "confianza": 0.85,  # Valor hipotético, idealmente calculado del modelo
                }
            else:
                # Procesar datos para modelo básico
                numeric_data = np.array(
                    [[tarea_data.get("complejidad", 3), tarea_data.get("prioridad", 2)]]
                )

                # Normalizar datos numéricos
                X_num = self.scalers.transform(numeric_data)

                # Procesar tipo de tarea
                tipo_tarea = tarea_data.get("tipo_tarea", "backend")
                X_task = np.array(
                    [[self.encoders.texts_to_sequences([tipo_tarea])[0][0]]]
                )

                # Procesar datos del requerimiento (información contextual)
                X_req = np.array(
                    [
                        [
                            tarea_data.get("complejidad_req", 3),
                            tarea_data.get("max_complejidad_req", 5),
                            tarea_data.get("num_tareas_req", 5),
                            tarea_data.get("prioridad_media_req", 2),
                        ]
                    ]
                )

                prediction = self.model.predict(X_num, X_task, X_req)
                tiempo_estimado = float(prediction[0][0])

                return {
                    "tiempo_estimado": tiempo_estimado,
                    "unidad": "horas",
                    "modelo": "Modelo básico",
                    "confianza": 0.7,  # Valor hipotético
                }

        except Exception as e:
            logger.error(f"Error al estimar tiempo: {e}")
            raise Exception(f"Error en la estimación de tiempo: {str(e)}")
