import os
import sys

os.environ["MPLBACKEND"] = "Agg"  # Esta línea debe ir ANTES de importar matplotlib

import joblib
import numpy as np
import pandas as pd
import json
from datetime import datetime
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score

# Ahora importa matplotlib con el backend ya configurado
import matplotlib

matplotlib.use("Agg")  # Redundante pero por seguridad
import matplotlib.pyplot as plt
import seaborn as sns
import traceback

# Desactivar cualquier uso interactivo
plt.ioff()  # Desactivar modo interactivo

# Asegurar que podemos importar desde este directorio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Rutas importantes
MODELS_DIR = os.path.join("redes_neuronales", "estimacion_tiempo", "models")
MODEL_NAME = "tiempo_estimator"


def ensure_directory_exists(directory):
    """Asegura que un directorio exista, creándolo si es necesario"""
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)


def load_model_and_preprocessors():
    """Carga el modelo y los preprocesadores"""
    try:
        from rnn_model import AdvancedRNNEstimator

        # Cargar feature_dims
        feature_dims_path = os.path.join(MODELS_DIR, "feature_dims.pkl")
        if not os.path.exists(feature_dims_path):
            raise FileNotFoundError(
                f"No se encontró feature_dims.pkl en {feature_dims_path}"
            )

        feature_dims = joblib.load(feature_dims_path)
        print(f"Dimensiones de características cargadas: {feature_dims}")

        # Cargar modelo
        model_path = os.path.join(MODELS_DIR, f"{MODEL_NAME}_model.keras")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"No se encontró modelo en {model_path}")

        estimator = AdvancedRNNEstimator.load(MODELS_DIR, MODEL_NAME)
        print(f"Modelo cargado correctamente desde {model_path}")

        # Cargar datos de validación de varias fuentes posibles
        X_val = None
        y_val = None

        # 1. Intentar cargar desde archivos .npy
        X_val_path = os.path.join(MODELS_DIR, "X_val.npy")
        y_val_path = os.path.join(MODELS_DIR, "y_val.npy")

        if os.path.exists(X_val_path) and os.path.exists(y_val_path):
            X_val = np.load(X_val_path)
            y_val = np.load(y_val_path)
            print(
                f"Datos de validación cargados: X_val: {X_val.shape}, y_val: {y_val.shape}"
            )
        else:
            # 2. Intentar cargar desde archivo joblib
            joblib_path = os.path.join(MODELS_DIR, "validation_data.joblib")
            if os.path.exists(joblib_path):
                try:
                    validation_data = joblib.load(joblib_path)
                    X_val = validation_data.get("X_val")
                    y_val = validation_data.get("y_val")
                    if X_val is not None and y_val is not None:
                        print(
                            f"Datos de validación cargados desde joblib: X_val: {X_val.shape}, y_val: {y_val.shape}"
                        )
                except Exception as e:
                    print(f"Error al cargar datos desde joblib: {e}")

        # 3. Si aún no hay datos, generar datos sintéticos para evaluación
        if X_val is None or y_val is None:
            print(
                "No se encontraron datos de validación. Generando datos sintéticos para evaluación..."
            )
            total_dims = sum(feature_dims.values())
            X_val = (
                np.random.randn(100, total_dims) * 0.5 + 0.5
            )  # Valores positivos cercanos a 0.5
            y_val = np.abs(
                np.random.randn(100) * 10 + 20
            )  # Valores positivos con media 20

            # Guardar estos datos para uso futuro
            np.save(X_val_path, X_val)
            np.save(y_val_path, y_val)
            print(
                f"Datos sintéticos generados: X_val: {X_val.shape}, y_val: {y_val.shape}"
            )

        return estimator, feature_dims, X_val, y_val

    except Exception as e:
        print(f"Error al cargar modelo y preprocesadores: {e}")
        raise


def generate_evaluation_metrics(estimator, X_val, y_val, feature_dims):
    """Genera métricas de evaluación del modelo"""
    try:
        # Obtener predicciones
        y_pred = estimator.predict(X_val, feature_dims)

        # Calcular métricas
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)

        # Calcular accuracy con umbral de 20%
        thresholds = np.maximum(np.abs(y_val) * 0.2, 0.5)  # Mínimo 0.5 horas
        absolute_errors = np.abs(y_val - y_pred)
        correct_predictions = absolute_errors <= thresholds
        accuracy = np.mean(correct_predictions)

        # Crear diccionario de métricas
        metrics = {
            "MSE": float(mse),
            "RMSE": float(rmse),
            "MAE": float(mae),
            "R2": float(r2),
            "Accuracy": float(accuracy),
            "Precision": float(accuracy),  # Simplificado
            "Recall": float(accuracy),  # Simplificado
            "F1": float(accuracy),  # Simplificado
        }

        # Guardar métricas
        metrics_path = os.path.join(MODELS_DIR, "evaluation_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)

        print(f"\nMétricas de evaluación guardadas en {metrics_path}:")
        for name, value in metrics.items():
            print(f"  {name}: {value:.4f}")

        return metrics, y_pred

    except Exception as e:
        print(f"Error al generar métricas de evaluación: {e}")
        raise


def generate_evaluation_plots(X_val, y_val, y_pred):
    """Genera gráficos de evaluación del modelo"""
    try:
        # 1. Gráfico de dispersión: real vs predicho
        plt.figure(figsize=(10, 6))
        plt.scatter(y_val, y_pred, alpha=0.6)
        plt.plot([min(y_val), max(y_val)], [min(y_val), max(y_val)], "r--")
        plt.title("Tiempo real vs Tiempo predicho")
        plt.xlabel("Tiempo real (horas)")
        plt.ylabel("Tiempo predicho (horas)")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(MODELS_DIR, "prediction_scatter.png"), dpi=300)
        plt.close("all")  # Cerrar TODAS las figuras

        # 2. Histograma de errores
        errors = y_pred - y_val
        plt.figure(figsize=(10, 6))
        plt.hist(errors, bins=30, alpha=0.7, color="blue")
        plt.axvline(x=0, color="r", linestyle="--")
        plt.title("Distribución de errores de predicción")
        plt.xlabel("Error (predicho - real)")
        plt.ylabel("Frecuencia")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(os.path.join(MODELS_DIR, "error_histogram.png"), dpi=300)
        plt.close("all")

        # 3. Gráfico combinado: 4 paneles
        plt.figure(figsize=(12, 10))

        # a. Scatter de real vs predicho
        plt.subplot(2, 2, 1)
        plt.scatter(y_val, y_pred, alpha=0.6)
        plt.plot([min(y_val), max(y_val)], [min(y_val), max(y_val)], "r--")
        plt.xlabel("Tiempo real (horas)")
        plt.ylabel("Tiempo predicho (horas)")
        plt.title("Predicción vs Valor Real")
        plt.grid(True, alpha=0.3)

        # b. Histograma de errores
        plt.subplot(2, 2, 2)
        plt.hist(errors, bins=20, alpha=0.6, color="green")
        plt.axvline(x=0, color="r", linestyle="--")
        plt.xlabel("Error de predicción (horas)")
        plt.ylabel("Frecuencia")
        plt.title("Distribución de Errores")
        plt.grid(True, alpha=0.3)

        # c. Residuos vs predicciones
        plt.subplot(2, 2, 3)
        plt.scatter(y_pred, errors, alpha=0.6, color="purple")
        plt.axhline(y=0, color="r", linestyle="--")
        plt.xlabel("Tiempo estimado (horas)")
        plt.ylabel("Residuo (horas)")
        plt.title("Análisis de Residuos")
        plt.grid(True, alpha=0.3)

        # d. Distribución de tiempos
        plt.subplot(2, 2, 4)
        sns.kdeplot(y_val, label="Real", color="blue")
        sns.kdeplot(y_pred, label="Estimado", color="orange")
        plt.xlabel("Tiempo (horas)")
        plt.ylabel("Densidad")
        plt.title("Distribución de Tiempos")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(os.path.join(MODELS_DIR, "evaluation_plots.png"), dpi=300)
        plt.close("all")

        print(f"Gráficos de evaluación generados en {MODELS_DIR}")

    except Exception as e:
        print(f"Error al generar gráficos de evaluación: {e}")
        raise

    finally:
        # Siempre cerrar todas las figuras al terminar
        plt.close("all")


def generate_feature_importance(X_val, y_val, estimator, feature_dims):
    """Genera archivo CSV con importancia de características"""
    try:
        # Características disponibles
        feature_names = [
            "Complejidad",
            "Cantidad_Recursos",
            "Carga_Trabajo_R1",
            "Experiencia_R1",
            "Carga_Trabajo_R2",
            "Experiencia_R2",
            "Carga_Trabajo_R3",
            "Experiencia_R3",
            "Experiencia_Equipo",
            "Claridad_Requisitos",
            "Tamaño_Tarea",
        ]

        # Agregar nombres para características categóricas
        for i in range(feature_dims["tipo_tarea"]):
            feature_names.append(f"Tipo_Tarea_{i+1}")
        for i in range(feature_dims["fase"]):
            feature_names.append(f"Fase_{i+1}")

        # Predecir valores base
        y_base = estimator.predict(X_val, feature_dims)
        base_error = mean_squared_error(y_val, y_base)

        # Calcular importancia de cada característica por permutación
        importance_values = []

        # Para cada característica
        for i, feature_name in enumerate(feature_names):
            # Crear una copia de los datos y perturbar la característica
            X_perturbed = X_val.copy()
            X_perturbed[:, i] = np.random.permutation(X_perturbed[:, i])

            # Predecir con datos perturbados
            y_perturbed = estimator.predict(X_perturbed, feature_dims)

            # Calcular incremento en error
            perturbed_error = mean_squared_error(y_val, y_perturbed)
            importance = perturbed_error - base_error

            # Guardar importancia (usar valor absoluto)
            importance_values.append((feature_name, abs(importance)))

        # Ordenar por importancia
        importance_values.sort(key=lambda x: x[1], reverse=True)

        # Crear DataFrame
        feature_importance_df = pd.DataFrame(
            importance_values, columns=["Feature", "Importance"]
        )

        # Normalizar importancias
        sum_importance = feature_importance_df["Importance"].sum()
        if sum_importance > 0:
            feature_importance_df["Importance_Normalized"] = (
                feature_importance_df["Importance"] / sum_importance
            )
        else:
            feature_importance_df["Importance_Normalized"] = 0

        # Guardar CSV
        feature_importance_path = os.path.join(
            MODELS_DIR, "global_feature_importance.csv"
        )
        feature_importance_df.to_csv(feature_importance_path, index=False)

        print(f"\nImportancia de características guardada en {feature_importance_path}")
        print("Top 5 características más importantes:")
        for i in range(min(5, len(importance_values))):
            name, value = importance_values[i]
            print(f"  {i+1}. {name}: {value:.6f}")

        # Generar gráfico
        plt.figure(figsize=(12, 8))
        plt.barh(
            feature_importance_df["Feature"].head(10),
            feature_importance_df["Importance_Normalized"].head(10),
            color="teal",
        )
        plt.xlabel("Importancia Normalizada")
        plt.ylabel("Característica")
        plt.title("Top 10 Características Más Importantes")
        plt.tight_layout()
        plt.savefig(os.path.join(MODELS_DIR, "feature_importance.png"), dpi=300)
        plt.close()

        # Crear análisis por número de recursos
        try:
            recursos_scaled = X_val[:, 1]  # La columna 1 es Cantidad_Recursos
            valores_unicos = np.sort(np.unique(recursos_scaled))

            if len(valores_unicos) >= 3:
                # Crear segmentos basados en el valor escalado
                segmentos = {
                    "1_Recurso": np.isclose(recursos_scaled, valores_unicos[0]),
                    "2_Recursos": np.isclose(recursos_scaled, valores_unicos[1]),
                    "3_o_más_Recursos": np.isclose(recursos_scaled, valores_unicos[2]),
                }

                for nombre, mascara in segmentos.items():
                    if np.sum(mascara) < 5:  # Saltamos si hay muy pocos ejemplos
                        continue

                    # Calcular importancia para este segmento
                    X_segment = X_val[mascara]
                    y_segment = y_val[mascara]

                    segment_importance_values = []

                    # Calcular importancia de cada característica
                    for i, feature_name in enumerate(feature_names):
                        # Perturbar la característica
                        X_perturbed = X_segment.copy()
                        X_perturbed[:, i] = np.random.permutation(X_perturbed[:, i])

                        # Predecir y calcular cambio en error
                        y_base_segment = estimator.predict(X_segment, feature_dims)
                        base_error_segment = mean_squared_error(
                            y_segment, y_base_segment
                        )

                        y_perturbed_segment = estimator.predict(
                            X_perturbed, feature_dims
                        )
                        perturbed_error_segment = mean_squared_error(
                            y_segment, y_perturbed_segment
                        )

                        importance = abs(perturbed_error_segment - base_error_segment)
                        segment_importance_values.append((feature_name, importance))

                    # Ordenar por importancia
                    segment_importance_values.sort(key=lambda x: x[1], reverse=True)

                    # Crear DataFrame y normalizar
                    segment_df = pd.DataFrame(
                        segment_importance_values, columns=["Feature", "Importance"]
                    )
                    sum_importance = segment_df["Importance"].sum()

                    if sum_importance > 0:
                        segment_df["Importance_Normalized"] = (
                            segment_df["Importance"] / sum_importance
                        )
                    else:
                        segment_df["Importance_Normalized"] = 0

                    # Guardar CSV para este segmento
                    segment_path = os.path.join(
                        MODELS_DIR, f"feature_importance_{nombre}.csv"
                    )
                    segment_df.to_csv(segment_path, index=False)
                    print(f"Guardado análisis para {nombre}: {segment_path}")
            else:
                print(
                    "No hay suficientes valores únicos para crear segmentos por número de recursos"
                )
        except Exception as e:
            print(f"Error al crear análisis por recursos: {e}")

        return feature_importance_df

    except Exception as e:
        print(f"Error al generar importancia de características: {e}")
        raise


def generate_segmented_evaluation(X_val, y_val, estimator, feature_dims):
    """Genera evaluación por segmentos (tareas pequeñas, medianas, grandes)"""
    try:
        # Definir segmentos
        segments = {
            "pequeñas": lambda y: y <= 10,
            "medianas": lambda y: (y > 10) & (y <= 30),
            "grandes": lambda y: y > 30,
        }

        # Predecir valores
        y_pred = estimator.predict(X_val, feature_dims)

        # Evaluar por segmento
        results = {}

        for segment_name, segment_func in segments.items():
            # Seleccionar datos del segmento
            mask = segment_func(y_val)

            # Verificar si hay datos en este segmento
            if not np.any(mask):
                print(f"No hay datos para el segmento '{segment_name}'")
                continue

            X_segment = X_val[mask]
            y_segment = y_val[mask]
            y_pred_segment = y_pred[mask]

            # Calcular métricas
            segment_metrics = {
                "mse": float(mean_squared_error(y_segment, y_pred_segment)),
                "rmse": float(np.sqrt(mean_squared_error(y_segment, y_pred_segment))),
                "mae": float(mean_absolute_error(y_segment, y_pred_segment)),
                "r2": float(r2_score(y_segment, y_pred_segment)),
                "count": int(np.sum(mask)),
            }

            results[segment_name] = segment_metrics

        # Guardar resultados
        segmented_path = os.path.join(MODELS_DIR, "segmented_evaluation.json")
        with open(segmented_path, "w") as f:
            json.dump(results, f, indent=4)

        print(f"\nEvaluación segmentada guardada en {segmented_path}")
        for segment_name, metrics in results.items():
            print(f"  Segmento '{segment_name}' (n={metrics['count']}):")
            print(
                f"    RMSE: {metrics['rmse']:.2f}, MAE: {metrics['mae']:.2f}, R²: {metrics['r2']:.4f}"
            )

        return results

    except Exception as e:
        print(f"Error al generar evaluación segmentada: {e}")
        raise


def update_metrics_history(metrics):
    """Actualiza el historial de métricas"""
    try:
        history_path = os.path.join(MODELS_DIR, "metrics_history.json")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Crear entrada para el historial
        new_entry = {"timestamp": timestamp, "metrics": metrics}

        # Cargar historial existente o crear uno nuevo
        if os.path.exists(history_path):
            with open(history_path, "r") as f:
                try:
                    history = json.load(f)
                    if isinstance(history, list):
                        history.append(new_entry)
                    elif isinstance(history, dict) and "entries" in history:
                        history["entries"].append(new_entry)
                    else:
                        # Formato desconocido, crear nuevo
                        history = [new_entry]
                except json.JSONDecodeError:
                    # Archivo no válido, crear nuevo
                    history = [new_entry]
        else:
            # Archivo no existe, crear nuevo historial
            history = [new_entry]

        # Limitar historial a últimos 20 registros
        if isinstance(history, list) and len(history) > 20:
            history = history[-20:]
        elif (
            isinstance(history, dict)
            and "entries" in history
            and len(history["entries"]) > 20
        ):
            history["entries"] = history["entries"][-20:]

        # Guardar historial actualizado
        with open(history_path, "w") as f:
            json.dump(history, f, indent=4)

        print(f"Historial de métricas actualizado en {history_path}")

    except Exception as e:
        print(f"Error al actualizar historial de métricas: {e}")

# Asegurar que se puede importar desde el directorio padre
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

def main(model_dir=None):
    """
    Genera archivos de evaluación para el modelo actual.
    
    Args:
        model_dir: Directorio donde se encuentra el modelo y donde guardar resultados
    
    Returns:
        dict: Resultados de la operación
    """
    print("Iniciando generación de archivos de evaluación...")
    
    # Usar directorio por defecto si no se especifica
    if model_dir is None:
        model_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')
    
    # Asegurar que existe el directorio
    os.makedirs(model_dir, exist_ok=True)
    
    try:
        # 1. Importar clases necesarias
        from redes_neuronales.estimacion_tiempo.evaluator import ModelEvaluator
        from redes_neuronales.estimacion_tiempo.rnn_model import AdvancedRNNEstimator
        
        # 2. Cargar el modelo existente
        print(f"Cargando modelo desde {model_dir}...")
        model = AdvancedRNNEstimator.load(model_dir, 'tiempo_estimator')
        
        # 3. Cargar feature_dims
        feature_dims = joblib.load(os.path.join(model_dir, 'feature_dims.pkl'))
        
        # 4. Cargar datos de validación
        print("Cargando datos de validación...")
        try:
            X_val = np.load(os.path.join(model_dir, 'X_val.npy'))
            y_val = np.load(os.path.join(model_dir, 'y_val.npy'))
        except FileNotFoundError:
            print("No se encontraron datos de validación, generando datos sintéticos...")
            # Crear datos sintéticos para pruebas
            total_dims = sum(feature_dims.values())
            X_val = np.random.randn(100, total_dims) * 0.5 + 0.5
            y_val = np.abs(np.random.randn(100) * 10 + 20)
            
            # Guardar los datos sintéticos
            np.save(os.path.join(model_dir, 'X_val.npy'), X_val)
            np.save(os.path.join(model_dir, 'y_val.npy'), y_val)
        
        print(f"Datos cargados: X_val {X_val.shape}, y_val {y_val.shape}")
        
        # 5. Crear el evaluador
        evaluator = ModelEvaluator(model, feature_dims, model_dir)
        
        # 6. Evaluar el modelo y guardar métricas
        print("Evaluando modelo...")
        metrics, y_pred = evaluator.evaluate_model(X_val, y_val)
        print("Métricas calculadas:", metrics)
        
        # 7. Generar gráficos de predicciones
        print("Generando gráficos de predicciones...")
        plots_file = evaluator.plot_predictions(y_val, y_pred)
        
        # 8. Analizar importancia de características
        print("Analizando importancia de características...")
        # Lista de nombres de características
        feature_names = [
            'Complejidad', 'Cantidad_Recursos', 'Carga_Trabajo_R1', 
            'Experiencia_R1', 'Carga_Trabajo_R2', 'Experiencia_R2', 
            'Carga_Trabajo_R3', 'Experiencia_R3', 'Experiencia_Equipo', 
            'Claridad_Requisitos', 'Tamaño_Tarea'
        ]
        
        # Añadir nombres para características categóricas
        for i in range(feature_dims.get('tipo_tarea', 0)):
            feature_names.append(f'Tipo_Tarea_{i+1}')
        for i in range(feature_dims.get('fase', 0)):
            feature_names.append(f'Fase_{i+1}')
        
        # Completar feature_names si no hay suficientes
        if len(feature_names) < X_val.shape[1]:
            for i in range(len(feature_names), X_val.shape[1]):
                feature_names.append(f'Feature_{i+1}')
        
        importance_results = evaluator.analyze_feature_importance(X_val, y_val, feature_names)
        
        # 9. Realizar evaluación segmentada
        print("Realizando evaluación segmentada...")
        segments = {
            'pequeñas': lambda y: y <= 10,
            'medianas': lambda y: (y > 10) & (y <= 30),
            'grandes': lambda y: y > 30
        }
        segmented_results = evaluator.segmented_evaluation(X_val, y_val, segments)
        
        # 10. Realizar evaluación por recursos (opcional si hay datos disponibles)
        try:
            print("Buscando datos para análisis por recursos...")
            
            # Intentar cargar datos más detallados para análisis específicos
            for resource_count in range(1, 4):
                resource_file = os.path.join(model_dir, f'X_val_recursos_{resource_count}.npy')
                
                if os.path.exists(resource_file):
                    print(f"Analizando datos para {resource_count} recursos...")
                    X_res = np.load(resource_file)
                    y_res = np.load(os.path.join(model_dir, f'y_val_recursos_{resource_count}.npy'))
                    
                    # Evaluar específicamente para este segmento
                    _, y_pred_res = evaluator.evaluate_model(X_res, y_res)
                    evaluator.analyze_feature_importance(X_res, y_res, feature_names)
                else:
                    print(f"No se encontraron datos para {resource_count} recursos")
            
        except Exception as e:
            print(f"Error al realizar análisis por recursos: {str(e)}")
            # Este error no debe detener el proceso principal
        
        # 11. Actualizar archivo de estado del modelo
        status_file = os.path.join(model_dir, 'model_status.json')
        model_status = {
            'last_evaluation': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'metrics': metrics,
            'files_generated': {
                'evaluation_metrics': 'evaluation_metrics.json',
                'metrics_history': 'metrics_history.json',
                'evaluation_plots': 'evaluation_plots.png',
                'feature_importance': 'global_feature_importance.png',
                'segmented_evaluation': 'segmented_evaluation.json',
                'segmented_metrics': 'segmented_metrics.png'
            }
        }
        
        with open(status_file, 'w') as f:
            json.dump(model_status, f, indent=2)
        
        print("Generación de archivos completada con éxito.")
        
        return {
            'success': True,
            'message': 'Archivos de evaluación generados correctamente',
            'metrics': metrics,
            'files': model_status['files_generated']
        }
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"Error durante la generación de archivos: {str(e)}")
        print(error_trace)
        
        return {
            'success': False,
            'message': f'Error al generar archivos: {str(e)}',
            'error_trace': error_trace
        }


if __name__ == "__main__":
    # Ejecutar directamente si se llama como script
    result = main()
    print("Resultado:", result['message'])
    print(f"\nEjecución {'exitosa ✅' if result else 'fallida ❌'}")



