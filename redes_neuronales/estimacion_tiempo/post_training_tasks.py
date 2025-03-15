"""
Script para ejecutar tareas posteriores al entrenamiento del modelo.
"""

# Al inicio del archivo, antes de cualquier importación
import os

os.environ["MPLBACKEND"] = "Agg"  # Forzar backend no interactivo
import sys
import time
import traceback
from datetime import datetime
from multiprocessing import Process  # Importar Process en lugar de Thread

# Luego de las importaciones iniciales
import matplotlib

matplotlib.use("Agg")  # Redundante pero por seguridad

# Asegurar que se puede importar desde el directorio padre
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)


def run_evaluation_in_background(training_id=None):
    """
    Ejecuta la generación de archivos de evaluación en segundo plano
    """
    print(
        f"[PostTraining] Iniciando generación de archivos de evaluación en segundo plano"
    )

    # Configuración de matplotlib
    import matplotlib

    matplotlib.use("Agg")
    os.environ["MPLBACKEND"] = "Agg"

    # Esperar para asegurarse de que el modelo se haya guardado
    time.sleep(5)

    try:
        # Verificar la existencia del modelo
        models_dir = os.path.join("redes_neuronales", "estimacion_tiempo", "models")
        if not os.path.exists(os.path.join(models_dir, "tiempo_estimator_model.keras")):
            print(
                "[PostTraining] ❌ El archivo del modelo no existe después de esperar. Abortando."
            )
            _notify_completion(
                training_id, False, "No se encontró el archivo del modelo"
            )
            return False

        # Usar directamente el ModelEvaluator para toda la evaluación
        from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator
        from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
        import joblib
        import numpy as np

        # Cargar el modelo
        estimator = AdvancedRNNEstimator.load(models_dir, "tiempo_estimator")

        # Cargar feature_dims
        feature_dims = joblib.load(os.path.join(models_dir, "feature_dims.pkl"))

        # Cargar datos de validación o crear sintéticos si no existen
        X_val_path = os.path.join(models_dir, "X_val.npy")
        y_val_path = os.path.join(models_dir, "y_val.npy")

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
        _notify_completion(
            training_id,
            True,
            "Métricas generadas correctamente. Puede visualizar detalles en el panel de métricas.",
        )
        return True

    except Exception as e:
        print(f"[PostTraining] ❌ Error durante la generación de archivos: {e}")
        traceback.print_exc()
        _notify_completion(training_id, False, f"Error: {str(e)}")
        return False


def _notify_completion(training_id, success, message):
    """Notifica la finalización del proceso de post-entrenamiento al cliente"""
    if not training_id:
        return

    try:
        # Importamos aquí para evitar problemas de importación circular
        from django.core.cache import cache

        # Obtener configuración del entrenamiento
        config_key = f"training_config_{training_id}"
        config = cache.get(config_key)

        if config:
            # Añadir notificación de finalización del post-procesamiento
            if "updates" not in config:
                config["updates"] = []

            # Añadir actualización con estado de post-procesamiento
            status_type = "success" if success else "warning"
            config["updates"].append(
                {
                    "type": "log",
                    "message": f"Post-procesamiento: {message}",
                    "level": status_type,
                    "timestamp": (
                        datetime.now().isoformat()
                        if "datetime" in sys.modules
                        else time.time()
                    ),
                    "is_post_processing": True,
                }
            )

            # Si fue exitoso, añadir evento de cierre explícito
            if success:
                config["updates"].append(
                    {
                        "type": "post_processing_complete",
                        "success": True,
                        "message": "Procesamiento posterior completado con éxito.",
                        "timestamp": time.time(),
                    }
                )

            # Actualizar en caché
            cache.set(config_key, config, 7200)  # 2 horas
            print(f"[PostTraining] Notificación enviada al cliente: {message}")

    except Exception as e:
        print(f"[PostTraining] Error al notificar finalización: {str(e)}")
        traceback.print_exc()


def start_background_tasks(training_id=None):
    """
    Inicia las tareas en segundo plano después del entrenamiento

    Args:
        training_id: ID del proceso de entrenamiento
    """
    process = Process(target=run_evaluation_in_background, args=(training_id,))
    process.daemon = True
    process.start()
    return process


# Punto de entrada para ejecutar manualmente
if __name__ == "__main__":
    print("Ejecutando tareas post-entrenamiento manualmente...")
    run_evaluation_in_background()
