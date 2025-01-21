import os
import numpy as np
import tensorflow as tf
from ml_model import EstimacionModel, DataPreprocessor
import traceback
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import pandas as pd
import joblib
from tqdm import tqdm

def print_dataset_stats(data, y):
    """
    Imprime estadísticas básicas del dataset
    
    Args:
        data: DataFrame con los datos completos
        y: Array con los valores objetivo (duraciones)
    """
    try:
        # Imprimir estadísticas generales
        print("\nEstadísticas del dataset:")
        print(f"Número total de requerimientos: {data['idrequerimiento'].nunique()}")
        print(f"Número total de tareas: {len(data)}")
        print(f"\nPromedio de duración: {y.mean():.2f} horas")
        print(f"Mediana de duración: {np.median(y):.2f} horas")
        print(f"Desviación estándar: {y.std():.2f} horas")

        # Imprimir tipos de tareas únicos
        print(f"\nTipos de tareas encontrados: {sorted(data['tipo_tarea'].unique())}")
        
    except Exception as e:
        print(f"Error al imprimir estadísticas: {str(e)}")

def evaluate_predictions(y_true, y_pred):
    """Evalúa las predicciones usando múltiples métricas"""
    mse = tf.keras.metrics.mean_squared_error(y_true, y_pred)
    mae = tf.keras.metrics.mean_absolute_error(y_true, y_pred)
    mape = tf.keras.metrics.mean_absolute_percentage_error(y_true, y_pred)
    r2 = 1 - np.sum(np.square(y_true - y_pred)) / np.sum(np.square(y_true - np.mean(y_true)))
    
    return {
        'mse': float(np.mean(mse)),
        'rmse': float(np.sqrt(np.mean(mse))),
        'mae': float(np.mean(mae)),
        'mape': float(np.mean(mape)),
        'r2': float(r2)
    }

def setup_environment():
    """Configura el ambiente para TensorFlow"""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

def load_and_process_data():
    """Carga y procesa los datos del CSV para el modelo de estimación"""
    try:
        print("Iniciando procesamiento de datos...")
        progress_bar = tqdm(total=6, desc="Procesando datos")

        # 1. Carga de datos con tipos específicos
        dtypes = {
            'idrequerimiento': np.int32,
            'complejidad': np.int8,
            'prioridad': np.int8,
            'tipo_tarea': 'category',
            'duracion': np.float32
        }
        data = pd.read_csv("estimacion_tiempos.csv", dtype=dtypes)
        progress_bar.update(1)

        # 2. Procesar tipo_tarea y obtener vocab_size
        tipos_tarea_unicos = data['tipo_tarea'].unique()
        vocab_size = len(tipos_tarea_unicos)  # Guardar el tamaño del vocabulario
        tipo_tarea_map = {tipo: idx for idx, tipo in enumerate(tipos_tarea_unicos)}
        data['tipo_tarea_encoded'] = data['tipo_tarea'].map(tipo_tarea_map).astype(np.int32)

        # 3. Validación de datos
        if data.isnull().any().any():
            raise ValueError("Hay valores nulos en el dataset")

        # 4. Estadísticas por requerimiento
        req_stats = data.groupby("idrequerimiento").agg({
            "complejidad": ["mean", "max", "count"],
            "duracion": ["sum", "mean", "std"],
            "prioridad": "mean"
        }).reset_index()

        req_stats.columns = [
            "idrequerimiento", 
            "complejidad_media", "complejidad_max", "num_tareas",
            "duracion_total", "duracion_media", "duracion_std",
            "prioridad_media"
        ]

        # 5. Unir y preparar features
        data = data.merge(req_stats, on="idrequerimiento", how="left")
        
        X_numeric = data[[
            "complejidad", "prioridad", 
            "complejidad_media", "complejidad_max",
            "num_tareas", "prioridad_media"
        ]].values.astype(np.float32)
        
        X_task = data["tipo_tarea_encoded"].values.reshape(-1, 1).astype(np.int32)
        
        X_req = data[[
            "duracion_media", "duracion_std",
            "complejidad_media", "prioridad_media"
        ]].values.astype(np.float32)
        
        y = data["duracion"].values.astype(np.float32)

        # 6. Train-test split
        (X_num_train, X_num_val, X_task_train, X_task_val,
         X_req_train, X_req_val, y_train, y_val) = train_test_split(
            X_numeric, X_task, X_req, y, test_size=0.2, random_state=42
        )

        print_dataset_stats(data, y)
        
        return (
            X_num_train, X_num_val,
            X_req_train, X_req_val,
            X_task_train, X_task_val,
            y_train, y_val,
            vocab_size  # Asegurar que se retorna el vocab_size
        )

    except Exception as e:
        print(f"Error en el procesamiento de datos: {str(e)}")
        raise

def main():
    try:
        print("\nIniciando entrenamiento del modelo de estimación...")
        
        # Configuración inicial
        os.makedirs("models", exist_ok=True)
        progress_bar_main = tqdm(total=4, desc="Proceso de entrenamiento")

        try:
            # 1. Cargar y procesar datos
            (X_num_train, X_num_val, X_req_train, X_req_val, 
             X_task_train, X_task_val, y_train, y_val, vocab_size) = load_and_process_data()
            progress_bar_main.update(1)

            # 2. Configurar modelo
            config = {
                "vocab_size": vocab_size + 1,
                "lstm_units": [128, 64, 32],
                "dense_units": [256, 128, 64],
                "dropout_rate": 0.4,
                "learning_rate": 0.001,
                "batch_size": 64,
                "input_dims": {
                    "numeric": 6,
                    "req": 4,
                    "task": 1
                }
            }
            model = EstimacionModel(config)
            progress_bar_main.update(1)

            # 3. Normalizar datos
            print("\nNormalizando datos...")
            
            # Barra de progreso para normalización
            with tqdm(total=2, desc="Normalizando datos") as norm_progress:
                X_num_train_norm, scaler = model.normalize_data(X_num_train)
                norm_progress.update(1)
                
                X_num_val_norm = scaler.transform(X_num_val)
                norm_progress.update(1)
            
            progress_bar_main.update(1)
            print("Datos normalizados exitosamente!")

            # 4. Entrenar modelo y validación cruzada
            print("\nIniciando entrenamiento...")
            print("Realizando validación cruzada...")
            
            # Barra de progreso para validación cruzada
            with tqdm(total=100, desc="Validación cruzada") as cv_progress:
                history = model.train(
                    [X_num_train_norm, X_req_train, X_task_train],
                    y_train,
                    validation_data=([X_num_val_norm, X_req_val, X_task_val], y_val),
                    epochs=100
                )
            
            progress_bar_main.update(1)

            # Guardar modelo y scaler
            print("\nGuardando modelo y scaler...")
            model.model.save("models/modelo_estimacion.keras")
            joblib.dump(scaler, "models/scaler.pkl")
            
            progress_bar_main.close()
            print("\nEntrenamiento completado exitosamente!")
            return history

        except Exception as e:
            print(f"\nError en el proceso: {str(e)}")
            if 'progress_bar_main' in locals():
                progress_bar_main.close()
            raise e

    except Exception as e:
        print(f"\nError durante el entrenamiento: {str(e)}")
        if 'progress_bar_main' in locals():
            progress_bar_main.close()
        return None

if __name__ == "__main__":
    main()
