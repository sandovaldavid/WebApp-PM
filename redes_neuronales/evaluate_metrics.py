import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    mean_squared_error,
    r2_score,
    mean_absolute_error,
)
from sklearn.model_selection import train_test_split
import pandas as pd
import tensorflow as tf
import joblib
from sklearn.preprocessing import StandardScaler
import json
from datetime import datetime


def load_and_preprocess_data():
    """Carga y preprocesa los datos para evaluación"""
    try:
        # Cargar datos
        df = pd.read_csv("estimacion_tiempos.csv")

        # Calcular estadísticas de requerimientos
        req_stats = (
            df.groupby("idrequerimiento")
            .agg(
                {"complejidad": ["mean", "max"], "prioridad": "mean", "duracion": "sum"}
            )
            .reset_index()
        )

        req_stats.columns = [
            "idrequerimiento",
            "complejidad_media_req",
            "complejidad_max_req",
            "prioridad_media_req",
            "duracion_total_req",
        ]

        # Añadir número de tareas por requerimiento
        tareas_por_req = (
            df.groupby("idrequerimiento").size().reset_index(name="num_tareas_req")
        )
        req_stats = req_stats.merge(tareas_por_req, on="idrequerimiento")

        # Unir con datos originales
        df = df.merge(req_stats, on="idrequerimiento")

        # Separar features
        X_numeric = df[["complejidad", "prioridad"]].values
        X_task = df["tipo_tarea"].values
        X_req = df[
            [
                "num_tareas_req",
                "prioridad_media_req",
                "complejidad_media_req",
                "complejidad_max_req",
            ]
        ].values
        y = df["duracion"].values

        print("\nEstadísticas del dataset:")
        print(f"Número total de requerimientos: {df['idrequerimiento'].nunique()}")
        print(f"Número total de tareas: {len(df)}")
        print(f"Promedio de duración: {y.mean():.2f} horas")
        print(f"Mediana de duración: {np.median(y):.2f} horas")
        print(f"Desviación estándar: {y.std():.2f} horas")

        # Dividir datos
        (
            X_num_train,
            X_num_test,
            X_task_train,
            X_task_test,
            X_req_train,
            X_req_test,
            y_train,
            y_test,
        ) = train_test_split(
            X_numeric, X_task, X_req, y, test_size=0.2, random_state=42
        )

        return {
            "train": [X_num_train, X_req_train, X_task_train, y_train],
            "test": [X_num_test, X_req_test, X_task_test, y_test],
        }

    except Exception as e:
        print(f"Error en carga de datos: {str(e)}")
        return None


def calculate_metrics(y_true, y_pred):
    """Calcula múltiples métricas de evaluación"""

    # Métricas de regresión
    mse = mean_squared_error(y_true, y_pred)
    rmse = np.sqrt(mse)
    mae = mean_absolute_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    # Convertir a clasificación para métricas adicionales
    y_true_class = np.round(y_true)
    y_pred_class = np.round(y_pred)

    # Métricas de clasificación
    accuracy = accuracy_score(y_true_class, y_pred_class)
    precision = precision_score(
        y_true_class, y_pred_class, average="weighted", zero_division=0
    )
    recall = recall_score(
        y_true_class, y_pred_class, average="weighted", zero_division=0
    )
    f1 = f1_score(y_true_class, y_pred_class, average="weighted", zero_division=0)

    return {
        "MSE": mse,
        "RMSE": rmse,
        "MAE": mae,
        "R2": r2,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1": f1,
    }


def evaluate_model():
    """Evalúa el modelo entrenado usando múltiples métricas"""
    try:
        # Cargar datos
        data = load_and_preprocess_data()
        if data is None:
            return None

        # Cargar modelo y preprocessors
        model = tf.keras.models.load_model("models/modelo_estimacion.keras")
        preprocessor = joblib.load("models/preprocessor.pkl")
        scaler_num = joblib.load("models/scaler.pkl")
        scaler_req = joblib.load("models/scaler_req.pkl")

        # Obtener datos de test
        X_num_test = data["test"][0]  # Features numéricas
        X_req_test = data["test"][1]  # Info del requerimiento
        X_task_test = data["test"][2]  # Tipos de tarea
        y_test = data["test"][3]  # Valores reales

        # Obtener estadísticas del dataset
        y_all = np.concatenate([data["train"][3], y_test])
        df = pd.read_csv("estimacion_tiempos.csv")
        total_reqs = df["idrequerimiento"].nunique()

        dataset_stats = {
            "total_reqs": total_reqs,
            "total_tasks": len(y_all),
            "mean_duration": float(np.mean(y_all)),
            "median_duration": float(np.median(y_all)),
            "std_duration": float(np.std(y_all)),
        }

        # Codificar tipos de tarea
        X_task_encoded = preprocessor.encode_task_types(X_task_test)

        # Usar los scalers guardados en vez de crear nuevos
        X_num_norm = scaler_num.transform(X_num_test)
        X_req_norm = scaler_req.transform(X_req_test)

        # Realizar predicciones
        y_pred = model.predict(
            [X_num_norm, X_req_norm, np.array(X_task_encoded).reshape(-1, 1)]
        )

        # Calcular métricas
        metrics = calculate_metrics(y_test, y_pred.flatten())

        # Imprimir resultados
        print("\nMétricas de Rendimiento del Modelo:")
        print("=====================================")
        print(f"Error Cuadrático Medio (MSE): {metrics['MSE']:.4f}")
        print(f"Raíz del Error Cuadrático Medio (RMSE): {metrics['RMSE']:.4f}")
        print(f"Error Absoluto Medio (MAE): {metrics['MAE']:.4f}")
        print(f"Coeficiente de Determinación (R²): {metrics['R2']:.4f}")
        print(f"Precisión (Accuracy): {metrics['Accuracy']:.4f}")
        print(f"Exactitud (Precision): {metrics['Precision']:.4f}")
        print(f"Recuperación (Recall): {metrics['Recall']:.4f}")
        print(f"Puntuación F1 (F1-Score): {metrics['F1']:.4f}")

        # Guardar métricas y estadísticas en el historial
        save_metrics_history(metrics, dataset_stats)

        return metrics

    except Exception as e:
        print(f"Error durante la evaluación: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return None


def save_metrics_history(metrics, dataset_stats=None):
    """Guarda las métricas y estadísticas del dataset en un archivo JSON como historial"""

    history_file = "models/metrics_history.json"

    # Prepare new metrics entry with dataset stats
    metrics_entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": {k: float(v) for k, v in metrics.items()},
        "dataset_stats": (
            {
                "total_requerimientos": int(dataset_stats["total_reqs"]),
                "total_tareas": int(dataset_stats["total_tasks"]),
                "duracion_promedio": float(dataset_stats["mean_duration"]),
                "duracion_mediana": float(dataset_stats["median_duration"]),
                "duracion_std": float(dataset_stats["std_duration"]),
            }
            if dataset_stats
            else None
        ),
    }

    # Load existing history or create new
    try:
        with open(history_file, "r") as f:
            history = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        history = []

    # Add new metrics and save
    history.append(metrics_entry)

    # Save updated history
    with open(history_file, "w") as f:
        json.dump(history, f, indent=4)

    print(f"\nMétricas y estadísticas guardadas en: {history_file}")


if __name__ == "__main__":
    evaluate_model()
