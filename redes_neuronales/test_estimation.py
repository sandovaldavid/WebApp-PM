import os
import numpy as np
import tensorflow as tf
import joblib
from ml_model import EstimacionModel


def test_estimaciones():
    """Test the trained model with different test cases"""
    try:
        # Configurar rutas relativas
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        MODEL_DIR = os.path.join(BASE_DIR, "models")

        # Asegurar que existe el directorio
        if not os.path.exists(MODEL_DIR):
            os.makedirs(MODEL_DIR)

        config = {
            "vocab_size": 6,
            "lstm_units": 32,
            "dense_units": [64, 32],
            "dropout_rate": 0.2,
        }
        model = EstimacionModel(config)

        # Definir rutas de archivos
        MODEL_PATH = os.path.join(MODEL_DIR, "modelo_estimacion.keras")
        PREPROCESSOR_PATH = os.path.join(MODEL_DIR, "preprocessor.pkl")
        SCALER_NUM_PATH = os.path.join(MODEL_DIR, "scaler.pkl")
        SCALER_REQ_PATH = os.path.join(MODEL_DIR, "scaler_req.pkl")

        # Verificar si los archivos existen
        for path in [MODEL_PATH, PREPROCESSOR_PATH, SCALER_NUM_PATH, SCALER_REQ_PATH]:
            if not os.path.exists(path):
                raise FileNotFoundError(f"No se encuentra el archivo: {path}")

        # Cargar modelo y preprocessors
        model.model = tf.keras.models.load_model(MODEL_PATH)
        preprocessor = joblib.load(PREPROCESSOR_PATH)
        scaler_num = joblib.load(SCALER_NUM_PATH)
        scaler_req = joblib.load(SCALER_REQ_PATH)

    except FileNotFoundError as e:
        print(f"Error: {str(e)}")
        print(
            "Asegúrate de que los archivos del modelo existan en el directorio 'models/'"
        )
        return
    except Exception as e:
        print(f"Error inesperado: {str(e)}")
        return

    # Casos de prueba
    test_cases = [
        # (idreq, complejidad, prioridad, tipo_tarea)
        (1, 3, 2, "backend"),  # Tarea simple backend
        (1, 5, 1, "frontend"),  # Tarea media frontend
        (2, 5, 3, "database"),  # Tarea compleja database
        (2, 4, 2, "backend"),  # Tarea alta backend
        (3, 2, 3, "testing"),  # Tarea baja testing
        (4, 1, 1, "deployment"),
        (4, 5, 3, "deployment"),
        (4, 5, 1, "frontend"),
    ]

    print("\nPruebas de Estimación de Duración:")
    print("====================================")

    for idreq, comp, prior, tipo in test_cases:
        try:
            # Preparar datos numéricos (2 características)
            X_num = np.array([[comp, prior]], dtype=np.float32)

            # Preparar datos de requerimiento (4 características)
            X_req = np.array([[comp, comp, 1, prior]], dtype=np.float32)

            # Preparar datos de tipo de tarea
            X_task = preprocessor.encode_task_types([tipo])

            # Normalizar datos usando los scalers correctos
            X_num_norm = scaler_num.transform(X_num)
            X_req_norm = scaler_req.transform(X_req)

            # Realizar predicción usando predict_individual_task
            resultado = model.predict_individual_task(
                X_num_norm, np.array(X_task).reshape(-1, 1), X_req_norm
            )

            print(f"\nRequerimiento ID: {idreq}")
            print(f"Tipo de tarea: {tipo}")
            print(f"Complejidad: {comp}")
            print(f"Prioridad: {prior}")
            print(
                f"Estimación de duración: {float(resultado['tiempo_estimado']):.2f} horas"
            )
            print("------------------------------------")

        except Exception as e:
            print(f"Error en predicción para {tipo}: {str(e)}")


if __name__ == "__main__":
    test_estimaciones()
