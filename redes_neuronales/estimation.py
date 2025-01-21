import os
import numpy as np
import tensorflow as tf
from ml_model import EstimacionModel, DataPreprocessor
import traceback
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib

def setup_environment():
    """Configura el ambiente para TensorFlow"""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

def load_and_process_data():
    """
    Carga y procesa los datos del CSV para el modelo de estimación

    Returns:
        tuple: Datos procesados para entrenamiento y validación
    """
    try:
        # 1. Carga de datos
        data = pd.read_csv("estimacion_tiempos.csv")

        # 2. Validación de columnas requeridas
        required_columns = [
            "idrequerimiento",
            "complejidad",
            "prioridad",
            "tipo_tarea",
            "duracion",
        ]
        if not all(col in data.columns for col in required_columns):
            raise ValueError("El CSV no contiene todas las columnas requeridas")

        # 3. Procesamiento por requerimiento
        req_stats = (
            data.groupby("idrequerimiento")
            .agg(
                {
                    "complejidad": ["mean", "max", "count"],
                    "duracion": "sum",
                    "prioridad": "mean",
                }
            )
            .reset_index()
        )

        # Renombrar columnas agregadas
        req_stats.columns = [
            "idrequerimiento",
            "complejidad_media_req",
            "complejidad_max_req",
            "num_tareas_req",
            "duracion_total_req",
            "prioridad_media_req",
        ]

        # Unir con datos originales
        data = data.merge(req_stats, on="idrequerimiento")

        # 4. Validaciones de rangos y valores
        if not (
            data["complejidad"].between(1, 5).all()
            and data["prioridad"].between(1, 3).all()
        ):
            raise ValueError(
                "Valores fuera de rango en complejidad (1-5) o prioridad (1-3)"
            )

        if not data["idrequerimiento"].notna().all():
            raise ValueError("Hay requerimientos sin ID")

        # 5. Procesamiento de tipos de tarea
        preprocessor = DataPreprocessor()
        tipos_tarea_unicos = sorted(data["tipo_tarea"].unique())
        expected_tasks = ["backend", "frontend", "database", "testing", "deployment"]

        if not all(task in tipos_tarea_unicos for task in expected_tasks):
            raise ValueError(f"Faltan tipos de tarea. Esperados: {expected_tasks}")

        print("Tipos de tareas encontrados:", tipos_tarea_unicos)
        print(f"Número total de requerimientos: {data['idrequerimiento'].nunique()}")
        print(f"Número total de tareas: {len(data)}")

        # 6. Codificación de tipos de tarea
        preprocessor.fit_tokenizer(tipos_tarea_unicos)
        tipos_tarea_encoded = preprocessor.encode_task_types(data["tipo_tarea"].values)
        tipos_tarea_encoded = np.array(tipos_tarea_encoded)

        # 7. Preparación de features
        X_numeric = data[["complejidad", "prioridad"]].values
        X_req = data[
            [
                "complejidad_media_req",
                "complejidad_max_req",
                "num_tareas_req",
                "prioridad_media_req",
            ]
        ].values
        y = data["duracion"].values

        # 8. Validación de nulos
        if np.isnan(X_numeric).any() or np.isnan(X_req).any() or np.isnan(y).any():
            raise ValueError("Hay valores nulos en los datos")

        # 9. Normalización de datos
        scaler = StandardScaler()
        scaler_req = StandardScaler()

        X_numeric_scaled = scaler.fit_transform(X_numeric)
        X_req_scaled = scaler_req.fit_transform(X_req)

        # 10. Split estratificado de datos
        (
            X_num_train,
            X_num_val,
            X_req_train,
            X_req_val,
            X_task_train,
            X_task_val,
            y_train,
            y_val,
        ) = train_test_split(
            X_numeric_scaled,
            X_req_scaled,
            tipos_tarea_encoded,
            y,
            test_size=0.2,
            random_state=42,
            stratify=data["tipo_tarea"],
        )

        # 11. Guardar preprocessors y scalers
        joblib.dump(preprocessor, "models/preprocessor.pkl")
        joblib.dump(scaler, "models/scaler.pkl") 
        joblib.dump(scaler_req, "models/scaler_req.pkl")

        print("\nEstadísticas del dataset:")
        print(f"Promedio de duración: {y.mean():.2f} horas")
        print(f"Mediana de duración: {np.median(y):.2f} horas")
        print(f"Desviación estándar: {y.std():.2f} horas")

        return (
            X_num_train,
            X_num_val,
            X_req_train,
            X_req_val,
            X_task_train,
            X_task_val,
            y_train,
            y_val,
            len(tipos_tarea_unicos) + 1,
        )

    except FileNotFoundError:
        raise FileNotFoundError("No se encontró el archivo estimacion_tiempos.csv")
    except Exception as e:
        raise Exception(f"Error al procesar los datos: {str(e)}")

def main():
    try:
        # Setup
        setup_environment()

        # Cargar y procesar datos
        (
            X_num_train,
            X_num_val,
            X_req_train,
            X_req_val,  # Añadido X_req para información del requerimiento
            X_task_train,
            X_task_val,
            y_train,
            y_val,
            vocab_size,
        ) = load_and_process_data()

        # Configuración del modelo
        config = {
            "vocab_size": vocab_size,
            "lstm_units": 32,
            "dense_units": [64, 32],
            "dropout_rate": 0.2,
        }

        # Crear modelo
        model = EstimacionModel(config)

        # Normalizar datos
        X_num_train_norm, scaler = model.normalize_data(X_num_train)
        X_num_val_norm = scaler.transform(X_num_val)

        # Validación cruzada
        mean_score, std_score = model.cross_validate_model(
            X_num_train_norm, X_task_train, X_req_train, y_train
        )

        print(f"CV Score: {mean_score:.4f} (+/- {std_score:.4f})")

        # Entrenar modelo final
        history = model.train(
            [
                X_num_train_norm,
                X_req_train,
                X_task_train,
            ],  # Incluir X_req en el entrenamiento
            y_train,
            validation_data=([X_num_val_norm, X_req_val, X_task_val], y_val),
            epochs=100,
        )

        # Analizar importancia de features
        feature_names = ["Complejidad", "Prioridad", "Info Requerimiento"]
        importance_scores = model.analyze_feature_importance(
            X_num_train_norm, X_task_train, X_req_train, y_train, feature_names
        )

        print("\nImportancia de características:")
        print("===============================")
        for feature, score in importance_scores:
            print(f"{feature}: {score:.4f}")

        # Guardar modelo
        model.model.summary()
        model.model.save("models/modelo_estimacion.keras")
        print("Modelo guardado exitosamente")

        return history

    except Exception as e:
        print(f"Error durante el entrenamiento: {str(e)}")
        print(traceback.format_exc())
    return None

if __name__ == "__main__":
    main()
