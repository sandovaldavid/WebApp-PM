#!/usr/bin/env python
# Este script puede ser ejecutado periódicamente mediante un cronjob

import os
import sys
import pandas as pd
import numpy as np
from datetime import datetime
import logging
import traceback
import json

# Configurar el path para importar desde el proyecto Django
PROJECT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, PROJECT_PATH)

# Configurar Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
import django

django.setup()

# Importar modelos y clases
from dashboard.models import Tarea, TipoTarea, Fase, Tarearecurso, Recursohumano
from redes_neuronales.estimacion_tiempo.data_processor import DataProcessor
from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(PROJECT_PATH, 'logs/retrain_model.log')),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


def collect_data_from_db():
    """Recolecta datos de entrenamiento desde la base de datos"""
    logger.info("Recolectando datos desde la base de datos...")

    try:
        # Obtener tareas completadas con duración registrada
        tareas = Tarea.objects.filter(
            estado='Completada', duracionactual__isnull=False
        ).select_related('tipo_tarea', 'fase', 'idrequerimiento')

        if not tareas.exists():
            logger.warning("No hay tareas completadas con duración registrada")
            return None

        # Preparar datos
        data = []
        for tarea in tareas:
            # Obtener recursos asignados
            recursos = Tarearecurso.objects.filter(idtarea=tarea)
            cantidad_recursos = recursos.count() or 1

            # Información de recursos (hasta 3)
            carga_trabajo = [0, 0, 0]
            experiencia = [0, 0, 0]

            for i, recurso_asignacion in enumerate(recursos[:3]):
                carga_trabajo[i] = recurso_asignacion.idrecurso.carga_trabajo or 1
                experiencia[i] = recurso_asignacion.experiencia or 3

            # Determinar tipo de tarea y fase
            tipo_tarea = tarea.tipo_tarea.nombre if tarea.tipo_tarea else "Backend"
            fase = tarea.fase.nombre if tarea.fase else "Construcción/Desarrollo"

            # Agregar al dataset
            data.append(
                {
                    'ID': tarea.idtarea,
                    'Complejidad': tarea.dificultad or 3,
                    'Tipo_Tarea': tipo_tarea,
                    'Fase_Tarea': fase,
                    'Cantidad_Recursos': cantidad_recursos,
                    'Carga_Trabajo_R1': carga_trabajo[0],
                    'Experiencia_R1': experiencia[0],
                    'Carga_Trabajo_R2': carga_trabajo[1],
                    'Experiencia_R2': experiencia[1],
                    'Carga_Trabajo_R3': carga_trabajo[2],
                    'Experiencia_R3': experiencia[2],
                    'Experiencia_Equipo': 3,  # Valor por defecto
                    'Claridad_Requisitos': tarea.claridad_requisitos or 0.7,
                    'Tamaño_Tarea': tarea.tamaño_estimado or 5,
                    'Tiempo_Ejecucion': tarea.duracionactual,
                }
            )

        # Crear DataFrame
        df = pd.DataFrame(data)
        logger.info(f"Dataset creado con {len(df)} registros")

        # Guardar CSV como backup
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        df.to_csv(f"training_data_{timestamp}.csv", index=False)

        return df

    except Exception as e:
        logger.error(f"Error al recolectar datos: {str(e)}")
        logger.error(traceback.format_exc())
        return None


def retrain_model():
    """Reentrenar el modelo con nuevos datos"""
    logger.info("Iniciando reentrenamiento del modelo...")

    try:
        # 1. Recolectar datos
        df = collect_data_from_db()
        if df is None or len(df) < 10:
            logger.warning(
                "Datos insuficientes para reentrenar. Se necesitan al menos 10 registros."
            )
            return False

        # 2. Preparar directorio de modelos
        model_dir = os.path.join(os.path.dirname(__file__), 'models')
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # 3. Inicializar procesador de datos
        processor = DataProcessor()
        processor.data = df

        # 4. Preprocesar datos
        X_train, X_val, y_train, y_val, feature_dims = processor.preprocess_data()
        processor.save_preprocessors(output_dir=model_dir)

        # 5. Configurar modelo
        model_config = {
            'rnn_units': 64,
            'dense_units': [128, 64, 32],
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'l2_reg': 0.001,
            'use_bidirectional': True,
            'rnn_type': 'GRU',
            'activation': 'relu',
            'batch_size': min(32, len(X_train)),
            'epochs': 100,
        }

        # 6. Inicializar y entrenar modelo
        estimator = AdvancedRNNEstimator(model_config)
        estimator.build_model(feature_dims)
        history = estimator.train(X_train, y_train, X_val, y_val, feature_dims)

        # 7. Guardar modelo reentrenado
        timestamp = datetime.now().strftime("%Y%m%d")
        estimator.save(model_dir=model_dir, name=f'tiempo_estimator_{timestamp}')

        # También guardar como modelo principal
        estimator.save(model_dir=model_dir, name='tiempo_estimator')

        # 8. Evaluar modelo
        evaluator = ModelEvaluator(estimator, feature_dims, model_dir)
        metrics, _ = evaluator.evaluate_model(X_val, y_val)

        # 9. Guardar historial de métricas (formato compatible con evaluate_metrics.py)
        history_path = os.path.join(model_dir, 'metrics_history.json')

        # Dataset stats para el historial
        dataset_stats = {
            "total_samples": len(df),
            "training_samples": len(X_train),
            "validation_samples": len(X_val),
        }

        # Información de reentrenamiento
        retraining_info = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metrics': metrics,
            'training_type': 'retraining',
            'model_config': model_config,
            'dataset_stats': dataset_stats,
        }

        # Cargar historial existente o crear nuevo
        try:
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    metrics_history = json.load(f)
                    if not isinstance(metrics_history, list):
                        # Convertir al nuevo formato
                        if 'evaluations' in metrics_history:
                            metrics_history = metrics_history['evaluations']
                        else:
                            metrics_history = []
            else:
                metrics_history = []
        except Exception as e:
            logger.error(f"Error al cargar historial de métricas: {str(e)}")
            metrics_history = []

        # Añadir nueva evaluación al historial
        metrics_history.append(retraining_info)

        # Guardar historial actualizado
        with open(history_path, 'w') as f:
            json.dump(metrics_history, f, indent=4)

        # 10. Actualizar registro en la base de datos
        from dashboard.models import Modeloestimacionrnn

        modelo, _ = Modeloestimacionrnn.objects.update_or_create(
            nombremodelo='RNN Avanzado',
            defaults={
                'descripcionmodelo': 'Modelo de red neuronal recurrente para estimación de tiempo (reentrenado)',
                'versionmodelo': f"1.0.{timestamp}",
                'precision': metrics.get('r2', 0.8),
                'fechamodificacion': datetime.now(),
            },
        )

        logger.info(f"Modelo reentrenado exitosamente con {len(df)} registros")
        logger.info(
            f"Métricas: R² = {metrics.get('r2', 'N/A')}, MAE = {metrics.get('mae', 'N/A')}"
        )
        return True

    except Exception as e:
        logger.error(f"Error durante el reentrenamiento: {str(e)}")
        logger.error(traceback.format_exc())
        return False


if __name__ == "__main__":
    retrain_model()
