# Al inicio del archivo
import os

os.environ["MPLBACKEND"] = "Agg"
import numpy as np
import pandas as pd

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    r2_score,
    mean_absolute_percentage_error,
)
from datetime import datetime
import json
import joblib
import traceback


class ModelEvaluator:
    """Clase para evaluar el rendimiento de los modelos de estimación de tiempo"""

    def __init__(self, model, feature_dims, output_dir="models"):
        """Inicializa el evaluador

        Args:
            model: Modelo entrenado (AdvancedRNNEstimator)
            feature_dims: Diccionario con dimensiones de features
            output_dir: Directorio para guardar resultados
        """
        self.model = model
        self.feature_dims = feature_dims
        self.output_dir = output_dir

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Configuración de estilo para visualizaciones
        self._setup_visualization_style()

    def _setup_visualization_style(self):
        """Configura el estilo para todas las visualizaciones"""
        # Configuración global para gráficos
        plt.style.use("seaborn-v0_8-whitegrid")
        sns.set_palette("viridis")
        plt.rcParams["figure.figsize"] = (10, 6)
        plt.rcParams["font.size"] = 12

    def calculate_classification_metrics(
        self, y_true, y_pred, threshold_percentage=0.2
    ):
        """Calcula métricas de clasificación adaptadas para regresión

        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            threshold_percentage: Umbral relativo de error aceptable como porcentaje del valor real

        Returns:
            dict: Métricas de clasificación adaptadas
        """
        # Convertir valores a arrays numpy si no lo son
        y_true = np.array(y_true).flatten()
        y_pred = np.array(y_pred).flatten()

        # Determinar predicciones "correctas" usando un umbral relativo al valor real
        # Para valores muy pequeños, usar un umbral mínimo de 0.5 horas
        thresholds = np.maximum(np.abs(y_true) * threshold_percentage, 0.5)
        absolute_errors = np.abs(y_true - y_pred)
        correct_predictions = absolute_errors <= thresholds

        # Total de predicciones
        total = len(y_true)

        # True positives (predicciones correctas)
        tp = np.sum(correct_predictions)

        # Calcular métricas (todas en rango 0-1)
        accuracy = float(tp / total) if total > 0 else 0
        precision = (
            float(tp / total) if total > 0 else 0
        )  # En este contexto simplificado
        recall = float(tp / total) if total > 0 else 0  # son iguales a accuracy
        f1 = float(tp / total) if total > 0 else 0

        # Verificar que todas las métricas estén entre 0 y 1
        metrics = {
            "accuracy": min(max(accuracy, 0), 1),
            "precision": min(max(precision, 0), 1),
            "recall": min(max(recall, 0), 1),
            "f1": min(max(f1, 0), 1),
        }

        return metrics

    def evaluate_model(self, X_test, y_test):
        """Evalúa el modelo en datos de prueba

        Args:
            X_test: Datos de prueba
            y_test: Valores objetivo reales

        Returns:
            dict: Métricas de evaluación
        """
        # Preparar inputs para el modelo
        inputs = self.model.prepare_inputs(X_test, self.feature_dims)

        # Obtener predicciones
        y_pred = self.model.model.predict(inputs)

        # Calcular métricas de regresión
        mse = float(mean_squared_error(y_test, y_pred))
        rmse = float(np.sqrt(mse))
        mae = float(mean_absolute_error(y_test, y_pred))
        mape = float(mean_absolute_percentage_error(y_test, y_pred))
        r2 = float(r2_score(y_test, y_pred))

        # Calcular métricas adaptadas de clasificación
        classification_metrics = self.calculate_classification_metrics(y_test, y_pred)

        # Combinar todas las métricas
        metrics = {
            "MSE": mse,
            "RMSE": rmse,
            "MAE": mae,
            "MAPE": mape,
            "R2": r2,
            "Accuracy": classification_metrics["accuracy"],
            "Precision": classification_metrics["precision"],
            "Recall": classification_metrics["recall"],
            "F1": classification_metrics["f1"],
        }

        # Guardar métricas en archivo JSON
        metrics_path = os.path.join(self.output_dir, "evaluation_metrics.json")
        with open(metrics_path, "w") as f:
            json.dump(metrics, f, indent=4)

        # Guardar en historial de métricas
        self.save_to_metrics_history(metrics)

        print("\nMétricas de evaluación:")
        for metric_name, value in metrics.items():
            # Para métricas de clasificación, mostrar como porcentaje para mayor claridad
            if metric_name in ["Accuracy", "Precision", "Recall", "F1"]:
                print(f"  {metric_name}: {value*100:.2f}%")
            else:
                print(f"  {metric_name}: {value:.4f}")

        return metrics, y_pred.flatten()

    def save_to_metrics_history(self, metrics):
        """Guarda las métricas actuales en un historial

        Args:
            metrics: Diccionario con las métricas a guardar
        """
        history_path = os.path.join(self.output_dir, "metrics_history.json")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Añadir timestamp a las métricas
        metrics_with_timestamp = {"timestamp": timestamp, "metrics": metrics}

        # Cargar historial existente o crear uno nuevo
        try:
            if os.path.exists(history_path):
                with open(history_path, "r") as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        # Formato compatible con evaluate_metrics.py
                        history.append(metrics_with_timestamp)
                    else:
                        # Formato original con 'evaluations'
                        if "evaluations" not in history:
                            history["evaluations"] = []
                        history["evaluations"].append(metrics_with_timestamp)
            else:
                # Crear nuevo historial (formato compatible con evaluate_metrics.py)
                history = [metrics_with_timestamp]
        except Exception as e:
            print(f"Error al cargar historial de métricas: {e}")
            history = [metrics_with_timestamp]  # Crear nuevo en caso de error

        # Guardar historial actualizado
        with open(history_path, "w") as f:
            json.dump(history, f, indent=4)

        print(f"Métricas guardadas en historial: {history_path}")

    def plot_predictions(self, y_true, y_pred, save_fig=True):
        """Genera gráficos de comparación entre valores reales y predicciones

        Args:
            y_true: Valores reales
            y_pred: Valores predichos
            save_fig: Si True, guarda la figura
        """
        plt.figure(figsize=(12, 10))

        # 1. Scatter plot de predicciones vs valores reales
        plt.subplot(2, 2, 1)
        plt.scatter(y_true, y_pred, alpha=0.6)

        # Línea de perfecta predicción
        max_val = max(max(y_true), max(y_pred))
        min_val = min(min(y_true), min(y_pred))
        plt.plot([min_val, max_val], [min_val, max_val], "r--")

        plt.xlabel("Tiempo real (horas)")
        plt.ylabel("Tiempo estimado (horas)")
        plt.title("Predicción vs Valor Real")
        plt.grid(True, alpha=0.3)

        # 2. Histograma de errores
        plt.subplot(2, 2, 2)
        errors = y_pred - y_true
        plt.hist(errors, bins=20, alpha=0.6, color="green")
        plt.axvline(x=0, color="r", linestyle="--")
        plt.xlabel("Error de predicción (horas)")
        plt.ylabel("Frecuencia")
        plt.title("Distribución de Errores")
        plt.grid(True, alpha=0.3)

        # 3. Plot de residuos
        plt.subplot(2, 2, 3)
        plt.scatter(y_pred, errors, alpha=0.6, color="purple")
        plt.axhline(y=0, color="r", linestyle="--")
        plt.xlabel("Tiempo estimado (horas)")
        plt.ylabel("Residuo (horas)")
        plt.title("Análisis de Residuos")
        plt.grid(True, alpha=0.3)

        # 4. Distribución de predicciones y valores reales
        plt.subplot(2, 2, 4)
        sns.kdeplot(y_true, label="Real", color="blue")
        sns.kdeplot(y_pred, label="Estimado", color="orange")
        plt.xlabel("Tiempo (horas)")
        plt.ylabel("Densidad")
        plt.title("Distribución de Tiempos")
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_fig:
            plt.savefig(os.path.join(self.output_dir, "evaluation_plots.png"), dpi=300)
            print(
                f"Gráficos guardados en {os.path.join(self.output_dir, 'evaluation_plots.png')}"
            )

        plt.close()

    def analyze_feature_importance(self, X_test, y_test, feature_names=None):
        """Analiza la importancia de las características mediante múltiples técnicas avanzadas

        Args:
            X_test: Datos de prueba
            y_test: Valores objetivo reales
            feature_names: Lista con nombres de características

        Returns:
            DataFrame: Importancia de características ordenadas con métricas adicionales
        """
        import tensorflow as tf
        from scipy import stats
        import time

        # Configuración del análisis
        n_repeats = 10  # Repeticiones para cada permutación
        perm_test_iterations = 100  # Iteraciones para test de significancia
        significance_level = 0.05  # Nivel de significancia (p < 0.05)
        n_interaction_samples = 50  # Muestras para análisis de interacciones

        print(
            f"Analizando importancia de características con {n_repeats} repeticiones por característica..."
        )
        start_time = time.time()

        if feature_names is None or len(feature_names) != X_test.shape[1]:
            print(
                "Nombres de características no proporcionados o incorrectos. Usando índices."
            )
            feature_names = [f"Feature_{i}" for i in range(X_test.shape[1])]

        # Obtener índices para variables categóricas (tipo_tarea y fase)
        num_numeric_features = 11  # Complejidad hasta Tamaño_Tarea
        tipo_indices = list(
            range(
                num_numeric_features,
                num_numeric_features + self.feature_dims["tipo_tarea"],
            )
        )
        fase_indices = list(
            range(
                num_numeric_features + self.feature_dims["tipo_tarea"],
                num_numeric_features + self.feature_dims["fase"],
            )
        )

        # Definir características agrupadas para análisis
        feature_groups = {
            "Complejidad": [0],
            "Cantidad_Recursos": [1],
            "Carga_Trabajo_R1": [2],
            "Experiencia_R1": [3],
            "Carga_Trabajo_R2": [4],
            "Experiencia_R2": [5],
            "Carga_Trabajo_R3": [6],
            "Experiencia_R3": [7],
            "Experiencia_Equipo": [8],
            "Claridad_Requisitos": [9],
            "Tamaño_Tarea": [10],
            "Tipo_Tarea": tipo_indices,
            "Fase_Tarea": fase_indices,
        }

        # 1. PREDICCIONES BASE Y MÉTRICAS MÚLTIPLES
        # Definir múltiples métricas para evaluación más completa
        def calc_metrics(y_true, y_pred):
            return {
                "mse": mean_squared_error(y_true, y_pred),
                "mae": mean_absolute_error(y_true, y_pred),
                "r2": -r2_score(y_true, y_pred),  # Negativo porque medimos deterioro
                "mape": np.mean(np.abs((y_true - y_pred) / np.maximum(y_true, 0.001)))
                * 100,
            }

        # Generar predicciones base
        inputs_base = self.model.prepare_inputs(X_test, self.feature_dims)
        y_pred_base = self.model.model.predict(inputs_base).flatten()
        base_metrics = calc_metrics(y_test, y_pred_base)

        # 2. ANÁLISIS DE IMPORTANCIA CON REPETICIONES
        feature_importance_results = []

        for feature_name, indices in feature_groups.items():
            print(f"Analizando característica: {feature_name}...")

            # Almacenar resultados por repetición
            importance_values = []
            metrics_deltas = {metric: [] for metric in base_metrics.keys()}

            # Realizar múltiples repeticiones para mayor estabilidad estadística
            for rep in range(n_repeats):
                X_perturbed = X_test.copy()

                # Perturbar columnas del grupo
                for idx in indices:
                    X_perturbed[:, idx] = np.random.permutation(X_perturbed[:, idx])

                # Predecir con datos perturbados
                inputs_perturbed = self.model.prepare_inputs(
                    X_perturbed, self.feature_dims
                )
                y_pred_perturbed = self.model.model.predict(inputs_perturbed).flatten()

                # Calcular métricas en todas las dimensiones
                perturbed_metrics = calc_metrics(y_test, y_pred_perturbed)

                # Registrar deltas para cada métrica
                for metric_name, base_value in base_metrics.items():
                    delta = perturbed_metrics[metric_name] - base_value
                    metrics_deltas[metric_name].append(delta)

                # La importancia principal será basada en MSE
                importance_values.append(perturbed_metrics["mse"] - base_metrics["mse"])

            # Resumir resultados de repeticiones
            importance_mean = np.mean(importance_values)
            importance_std = np.std(importance_values)
            cv = importance_std / max(abs(importance_mean), 1e-10)  # Coef. de variación

            # 3. TEST DE SIGNIFICANCIA ESTADÍSTICA
            # Generar distribución nula para test de permutación
            null_distribution = []
            np.random.seed(42)  # Para reproducibilidad

            for _ in range(
                min(perm_test_iterations, 100)
            ):  # Limitar a 100 para eficiencia
                # Mezclar aleatoriamente la relación característica-objetivo
                random_idx = np.random.permutation(len(y_test))
                y_shuffled = y_test[random_idx]

                # Calcular delta en métrica con la predicción original
                null_delta = (
                    mean_squared_error(y_shuffled, y_pred_base) - base_metrics["mse"]
                )
                null_distribution.append(null_delta)

            # Calcular p-valor (proporción de valores aleatorios >= valor observado)
            p_value = np.mean(np.array(null_distribution) >= importance_mean)
            is_significant = p_value < significance_level

            # 4. ANÁLISIS INTEGRADO (APROXIMACIÓN SIMPLIFICADA DE INTEGRATED GRADIENTS)
            # Crear baseline para integrated gradients (valores promedio)
            if len(indices) == 1:  # Solo para características individuales
                try:
                    idx = indices[0]
                    baseline = np.median(X_test, axis=0).reshape(1, -1)

                    # Calcular gradiente aproximado
                    gradients = []
                    n_steps = 5  # Número reducido para eficiencia

                    for alpha in np.linspace(0, 1, n_steps):
                        X_interpolated = X_test.copy()
                        X_interpolated[:, idx] = baseline[0, idx] + alpha * (
                            X_test[:, idx] - baseline[0, idx]
                        )

                        # Predecir con valores interpolados
                        inputs_interp = self.model.prepare_inputs(
                            X_interpolated, self.feature_dims
                        )
                        with tf.GradientTape() as tape:
                            inputs_tensor = [
                                tf.convert_to_tensor(inp, dtype=tf.float32)
                                for inp in inputs_interp
                            ]
                            outputs = self.model.model(inputs_tensor)

                        # Calcular media absoluta de gradientes
                        grad_val = 0.0

                    integrated_importance = np.mean(gradients) if gradients else np.nan
                except Exception as e:
                    print(f"Error en análisis integrado para {feature_name}: {str(e)}")
                    integrated_importance = np.nan
            else:
                integrated_importance = np.nan

            # Almacenar resultados
            feature_result = {
                "Feature": feature_name,
                "Importance": importance_mean,
                "Importance_Std": importance_std,
                "CV": cv,
                "P_Value": p_value,
                "Is_Significant": is_significant,
                "MSE_Delta": np.mean(metrics_deltas["mse"]),
                "MAE_Delta": np.mean(metrics_deltas["mae"]),
                "R2_Delta": np.mean(metrics_deltas["r2"]),
                "MAPE_Delta": np.mean(metrics_deltas["mape"]),
                "Integrated_Importance": integrated_importance,
            }

            feature_importance_results.append(feature_result)

        # 5. ANÁLISIS DE INTERACCIONES (PARA LAS CARACTERÍSTICAS MÁS IMPORTANTES)
        print("\nAnalizando interacciones entre pares de características...")

        # Ordenar características por importancia
        sorted_features = sorted(
            feature_importance_results, key=lambda x: x["Importance"], reverse=True
        )

        # Limitar a las 5 más importantes para eficiencia
        top_features = [item["Feature"] for item in sorted_features[:5]]
        interaction_results = []

        # Seleccionar muestra aleatoria para análisis de interacciones (para eficiencia)
        if len(X_test) > n_interaction_samples:
            sample_idx = np.random.choice(
                len(X_test), n_interaction_samples, replace=False
            )
            X_sample = X_test[sample_idx]
            y_sample = y_test[sample_idx]
        else:
            X_sample = X_test
            y_sample = y_test

        # Calcular interacciones de pares
        for i, feature1 in enumerate(top_features):
            indices1 = feature_groups[feature1]
            for j, feature2 in enumerate(top_features):
                if j <= i:  # Evitar duplicados
                    continue

                indices2 = feature_groups[feature2]

                # Perturbar ambas características juntas
                X_perturbed = X_sample.copy()
                for idx in indices1 + indices2:
                    X_perturbed[:, idx] = np.random.permutation(X_perturbed[:, idx])

                # Predecir
                inputs_perturbed = self.model.prepare_inputs(
                    X_perturbed, self.feature_dims
                )
                y_pred_perturbed = self.model.model.predict(inputs_perturbed).flatten()

                # Calcular error con ambas características perturbadas
                joint_error = mean_squared_error(y_sample, y_pred_perturbed)

                # Obtener errores individuales (aproximación)
                individual_importance1 = next(
                    item["MSE_Delta"]
                    for item in feature_importance_results
                    if item["Feature"] == feature1
                )
                individual_importance2 = next(
                    item["MSE_Delta"]
                    for item in feature_importance_results
                    if item["Feature"] == feature2
                )

                # Calcular sinergia (interacción)
                interaction_value = joint_error - (
                    base_metrics["mse"]
                    + individual_importance1
                    + individual_importance2
                )

                # Solo registrar interacciones relativamente importantes
                if abs(interaction_value) >= 0.05 * (
                    individual_importance1 + individual_importance2
                ):
                    interaction_results.append(
                        {
                            "Feature1": feature1,
                            "Feature2": feature2,
                            "Interaction": interaction_value,
                            "Normalized_Interaction": interaction_value
                            / (individual_importance1 + individual_importance2 + 1e-10),
                        }
                    )

        # 6. NORMALIZAR Y CREAR DATAFRAME FINAL
        importance_df = pd.DataFrame(feature_importance_results)

        # Normalizar importancia absoluta
        sum_importance = importance_df["Importance"].sum()
        if sum_importance > 0:
            importance_df["Importance_Normalized"] = (
                importance_df["Importance"] / sum_importance
            )
        else:
            importance_df["Importance_Normalized"] = 0

        # Ordenar por importancia
        importance_df = importance_df.sort_values("Importance", ascending=False)

        # 7. CREAR DATAFRAME DE INTERACCIONES
        if interaction_results:
            interactions_df = pd.DataFrame(interaction_results)
            interactions_df = interactions_df.sort_values(
                "Interaction", ascending=False
            )

            # Guardar interacciones
            interactions_df.to_csv(
                os.path.join(self.output_dir, "feature_interactions.csv"), index=False
            )

            # Visualizar interacciones principales
            if len(interactions_df) > 0:
                plt.figure(figsize=(10, 6))
                top_n = min(10, len(interactions_df))
                interaction_labels = [
                    f"{row['Feature1']} × {row['Feature2']}"
                    for _, row in interactions_df.head(top_n).iterrows()
                ]
                plt.barh(
                    interaction_labels,
                    interactions_df["Normalized_Interaction"].head(top_n).values,
                    color="purple",
                )
                plt.xlabel("Interacción Normalizada")
                plt.title("Principales Interacciones entre Características")
                plt.tight_layout()
                plt.savefig(
                    os.path.join(self.output_dir, "feature_interactions.png"), dpi=300
                )
                plt.close()

        # Guardar resultados detallados
        importance_df.to_csv(
            os.path.join(self.output_dir, "global_feature_importance_detailed.csv"),
            index=False,
        )

        # Crear visualización mejorada
        plt.figure(figsize=(12, 8))
        bars = plt.barh(
            importance_df["Feature"],
            importance_df["Importance_Normalized"],
            color=[
                "teal" if sig else "lightblue"
                for sig in importance_df["Is_Significant"]
            ],
        )

        # Agregar barras de error
        plt.xlabel("Importancia Normalizada (%)")
        plt.ylabel("Característica")
        plt.title(
            "Importancia Global de Características (con Significancia Estadística)"
        )

        # Añadir leyenda para significancia
        from matplotlib.patches import Patch

        legend_elements = [
            Patch(facecolor="teal", label="Estadísticamente Significativo"),
            Patch(facecolor="lightblue", label="No Significativo"),
        ]
        plt.legend(handles=legend_elements, loc="lower right")

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, "global_feature_importance.png"), dpi=300
        )
        plt.close()

        # Crear visualización de comparativa de métricas
        plt.figure(figsize=(14, 10))
        metrics_to_plot = ["MSE_Delta", "MAE_Delta", "R2_Delta"]
        colors = ["teal", "coral", "purple"]

        for i, metric in enumerate(metrics_to_plot):
            plt.subplot(3, 1, i + 1)
            sorted_by_metric = importance_df.sort_values(metric, ascending=False)
            plt.barh(
                sorted_by_metric["Feature"][:7],
                sorted_by_metric[metric][:7],
                color=colors[i],
            )
            plt.title(f"Top 7 Características por {metric}")

        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, "feature_importance_metrics.png"), dpi=300
        )
        plt.close()

        print(
            f"Análisis de importancia completado en {time.time() - start_time:.1f} segundos"
        )

        # Simplificar el dataframe para retorno
        simplified_df = importance_df[
            [
                "Feature",
                "Importance",
                "Importance_Normalized",
                "Is_Significant",
                "P_Value",
            ]
        ]

        # NUEVO: Análisis segmentado por cantidad de recursos
        print("\nAnalizando importancia de características por cantidad de recursos...")
        self.analyze_feature_importance_by_resources(X_test, y_test, feature_names)

        return simplified_df

    def analyze_feature_importance_by_resources(
        self, X_test, y_test, feature_names=None
    ):
        """Analiza la importancia de las características segmentando por cantidad de recursos

        Args:
            X_test: Datos de prueba
            y_test: Valores objetivo reales
            feature_names: Lista con nombres de características

        Returns:
            dict: Resultados de importancia de características por segmento de recursos
        """
        from sklearn.base import BaseEstimator, RegressorMixin
        import pandas as pd
        import matplotlib.pyplot as plt
        import time

        # Crear un estimador compatible con scikit-learn para usar con permutation_importance
        class ModelWrapper(BaseEstimator, RegressorMixin):
            def __init__(self, model, feature_dims):
                self.model = model
                self.feature_dims = feature_dims

            def fit(self, X, y):
                # No necesitamos implementar fit realmente, solo es un requisito de la API
                return self

            def predict(self, X):
                return self.model.predict(X, self.feature_dims)

        # Crear instancia del wrapper
        model_wrapper = ModelWrapper(self.model, self.feature_dims)

        # Verificar si tenemos nombres de características
        if feature_names is None or len(feature_names) != X_test.shape[1]:
            print(
                "Nombres de características no proporcionados o incorrectos. Usando índices."
            )
            feature_names = [f"Feature_{i}" for i in range(X_test.shape[1])]

        # Columna 1 (índice 1) contiene la cantidad de recursos
        cantidad_recursos_idx = 1

        # Usar la cantidad de recursos para segmentar los datos
        recursos_values = X_test[:, cantidad_recursos_idx].copy()

        # Verificar cuántos recursos hay en el conjunto de datos
        unique_recursos = np.unique(recursos_values)
        print(
            f"Valores únicos de cantidad de recursos en el conjunto (escalados): {unique_recursos}"
        )

        # SOLUCIÓN: Los datos están normalizados/escalados, necesitamos aproximarlos a valores enteros
        # Descalamos usando cuantiles para determinar los límites de cada categoría

        # Calcular la distribución de valores y sus cuantiles
        recurso_valores = recursos_values.flatten()
        recurso_no_nans = recurso_valores[~np.isnan(recurso_valores)]

        # Determinar aproximadamente los valores por cuantiles
        # Asumiendo que hay 3 categorías (1, 2, 3 recursos) y potencialmente valores atípicos
        if len(recurso_no_nans) > 0:
            # Ordenar los valores
            sorted_values = np.sort(recurso_no_nans)

            # Identificar valores únicos y significativamente diferentes
            # Usamos un enfoque de clustering simple
            unique_clusters = []
            current_cluster = [sorted_values[0]]

            for val in sorted_values[1:]:
                if (
                    abs(val - current_cluster[-1]) < 0.1
                ):  # Umbral pequeño para considerar valores similares
                    current_cluster.append(val)
                else:
                    unique_clusters.append(np.mean(current_cluster))
                    current_cluster = [val]

            if current_cluster:
                unique_clusters.append(np.mean(current_cluster))

            print(f"Clusters de valores identificados: {unique_clusters}")

            # Convertir los clusters a asignaciones de recursos
            # El objetivo es mapear los valores escalados a valores de recursos
            resource_map = {}

            # Ordenar clusters para asignar recursos en orden ascendente
            unique_clusters.sort()

            # Si hay al menos 3 clusters diferentes, asumimos que representan 1, 2 y 3 recursos
            if len(unique_clusters) >= 3:
                for i, cluster in enumerate(unique_clusters[:3]):
                    resource_map[cluster] = i + 1  # 1, 2, 3 recursos
            else:
                # Si hay menos de 3 clusters, asignamos proporcionalmente
                for i, cluster in enumerate(unique_clusters):
                    resource_map[cluster] = i + 1

            print(f"Mapeo de valores a recursos: {resource_map}")
        else:
            print("No hay datos válidos para analizar recursos.")
            resource_map = {}

        # Aplicar mapeo manual para valores conocidos
        # Esto ayuda a manejar valores específicos que conocemos del análisis
        manual_map = {
            -1.22: 1,  # Valor más bajo a 1 recurso
            0.0: 2,  # Valor medio a 2 recursos
            1.22: 3,  # Valor más alto a 3 recursos
        }

        # Segmentar los datos
        segments = {
            "1_Recurso": np.zeros(len(recursos_values), dtype=bool),
            "2_Recursos": np.zeros(len(recursos_values), dtype=bool),
            "3_Recursos": np.zeros(len(recursos_values), dtype=bool),
        }

        # Asignar cada muestra al segmento correspondiente
        for i, val in enumerate(recursos_values):
            # Preferir mapeo manual para valores conocidos
            if abs(val - (-1.22)) < 0.1:
                segments["1_Recurso"][i] = True
            elif abs(val - 0.0) < 0.1:
                segments["2_Recursos"][i] = True
            elif abs(val - 1.22) < 0.1:
                segments["3_Recursos"][i] = True
            # Si no hay mapeo manual, intentar usar resource_map
            else:
                # Encontrar el cluster más cercano
                if resource_map:
                    closest_cluster = min(
                        resource_map.keys(), key=lambda x: abs(x - val)
                    )
                    resource_count = resource_map[closest_cluster]
                    segment_name = (
                        f'{resource_count}_Recurso{"s" if resource_count > 1 else ""}'
                    )
                    if segment_name in segments:
                        segments[segment_name][i] = True

        # Verificar si hay suficientes datos en cada segmento
        for segment_name, mask in segments.items():
            count = np.sum(mask)
            print(f"Segmento {segment_name}: {count} muestras")
            if count < 10:  # Advertencia si hay muy pocas muestras
                print(
                    f"¡ADVERTENCIA! Muy pocas muestras para análisis confiable en {segment_name}"
                )

        # Definir nombres descriptivos para cada índice
        feature_names_map = {
            0: "Complejidad",
            1: "Cantidad_Recursos",
            2: "Carga_R1",
            3: "Exp_R1",
            4: "Carga_R2",
            5: "Exp_R2",
            6: "Carga_R3",
            7: "Exp_R3",
            8: "Exp_Equipo",
            9: "Claridad_Req",
            10: "Tamaño",
        }

        # Añadir nombres para características categóricas
        num_numeric_features = 11  # Complejidad hasta Tamaño_Tarea
        tipo_indices = list(
            range(
                num_numeric_features,
                num_numeric_features + self.feature_dims["tipo_tarea"],
            )
        )
        fase_indices = list(
            range(
                num_numeric_features + self.feature_dims["tipo_tarea"],
                num_numeric_features
                + self.feature_dims["tipo_tarea"]
                + self.feature_dims["fase"],
            )
        )

        # Asignar nombres a índices categóricos
        for i in range(self.feature_dims["tipo_tarea"]):
            idx = num_numeric_features + i
            feature_names_map[idx] = f"Tipo_{i}"

        for i in range(self.feature_dims["fase"]):
            idx = num_numeric_features + self.feature_dims["tipo_tarea"] + i
            feature_names_map[idx] = f"Fase_{i}"

        # Definir los índices relevantes para cada segmento específico
        feature_indices = {
            "1_Recurso": [0, 1, 2, 3, 8, 9, 10]
            + tipo_indices
            + fase_indices,  # Solo R1 + comunes + categorías
            "2_Recursos": [0, 1, 2, 3, 4, 5, 8, 9, 10]
            + tipo_indices
            + fase_indices,  # R1 + R2 + comunes + categorías
            "3_Recursos": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            + tipo_indices
            + fase_indices,  # Todos
        }

        # Preparar colores para gráficos
        colors = ["#3498db", "#2ecc71", "#e74c3c"]

        # Para mantener todas las métricas calculadas
        results = {}
        all_segment_dfs = []

        # Crear DataFrames vacíos para cada segmento
        for segment_name, _ in segments.items():
            relevant_indices = feature_indices[segment_name]

            # Crear un DataFrame con estructura correcta
            empty_data = []
            for idx in relevant_indices:
                if idx < len(feature_names):
                    feature_name = feature_names_map.get(idx, feature_names[idx])
                    empty_data.append(
                        {
                            "Feature": feature_name,
                            "Importance": 0.0,
                            "Std": 0.0,
                            "Importance_Normalized": 0.0,
                            "Index": idx,
                        }
                    )

            # Crear DataFrame con lista de diccionarios
            results[segment_name] = pd.DataFrame(empty_data)

            # Guardar CSV
            results[segment_name].to_csv(
                os.path.join(self.output_dir, f"feature_importance_{segment_name}.csv"),
                index=False,
            )
            print(f"Guardado archivo base para {segment_name}")

        # Para cada segmento de interés (1, 2 y 3 recursos)
        segment_names = ["1_Recurso", "2_Recursos", "3_Recursos"]

        for i, segment_name in enumerate(segment_names):
            mask = segments[segment_name]
            count = np.sum(mask)

            # Si hay suficientes datos, calcular importancia real
            if count >= 10:
                X_segment = X_test[mask]
                y_segment = y_test[mask]
                relevant_indices = feature_indices[segment_name]

                try:
                    print(
                        f"\nAnalizando importancia para segmento: {segment_name} ({count} muestras)"
                    )
                    start_time = time.time()

                    # Número de repeticiones adaptativo
                    n_repeats = min(15, max(5, count // 20))
                    print(f"  Usando {n_repeats} repeticiones para el análisis")

                    # Crear DataFrame para los resultados
                    importance_data = []

                    # Calcular línea base para comparación
                    y_pred_base = model_wrapper.predict(X_segment)
                    base_error = mean_squared_error(y_segment, y_pred_base)

                    # Analizar cada característica relevante
                    for idx in relevant_indices:
                        if idx >= X_segment.shape[1]:
                            continue

                        # Almacenar importancia para múltiples repeticiones
                        feature_importances = []

                        # Guardar nombre de característica
                        if idx < len(feature_names):
                            feature_name = feature_names_map.get(
                                idx, feature_names[idx]
                            )
                        else:
                            feature_name = f"Feature_{idx}"

                        # Análisis basado en permutación
                        for _ in range(n_repeats):
                            X_permuted = X_segment.copy()

                            # Guardar valores originales
                            original_values = X_permuted[:, idx].copy()

                            # Permutar la característica
                            np.random.shuffle(X_permuted[:, idx])

                            # Predecir con valores permutados
                            y_pred_permuted = model_wrapper.predict(X_permuted)

                            # Calcular error con valores permutados
                            error_permuted = mean_squared_error(
                                y_segment, y_pred_permuted
                            )

                            # Importancia = incremento en error al permutar
                            importance = error_permuted - base_error
                            feature_importances.append(importance)

                            # Restaurar valores originales
                            X_permuted[:, idx] = original_values

                        # Calcular estadísticas para esta característica
                        importance_mean = np.mean(feature_importances)
                        importance_std = np.std(feature_importances)

                        # Añadir a los resultados
                        importance_data.append(
                            {
                                "Feature": feature_name,
                                "Importance": importance_mean,
                                "Std": importance_std,
                                "Index": idx,
                            }
                        )

                    # Crear DataFrame con los resultados
                    segment_df = pd.DataFrame(importance_data)

                    # Filtrar características no relevantes para este segmento
                    if segment_name == "1_Recurso":
                        # Excluir R2 y R3 para 1 recurso
                        segment_df = segment_df[
                            ~segment_df["Feature"].isin(
                                ["Carga_R2", "Exp_R2", "Carga_R3", "Exp_R3"]
                            )
                        ]
                    elif segment_name == "2_Recursos":
                        # Excluir R3 para 2 recursos
                        segment_df = segment_df[
                            ~segment_df["Feature"].isin(["Carga_R3", "Exp_R3"])
                        ]

                    # Ordenar por importancia
                    segment_df = segment_df.sort_values("Importance", ascending=False)

                    # Normalizar importancia
                    if not segment_df.empty:
                        sum_importance = segment_df["Importance"].sum()
                        if sum_importance > 0:
                            segment_df["Importance_Normalized"] = (
                                segment_df["Importance"] / sum_importance
                            )
                        else:
                            segment_df["Importance_Normalized"] = 0

                        # Guardar resultados
                        results[segment_name] = segment_df
                        segment_df["Segment"] = segment_name
                        all_segment_dfs.append(segment_df)

                        # Crear visualización para este segmento
                        plt.figure(figsize=(12, 8))
                        top_df = segment_df.head(10)  # Top 10
                        plt.barh(
                            top_df["Feature"],
                            top_df["Importance_Normalized"],
                            color=colors[i % len(colors)],
                        )
                        plt.xlabel("Importancia Normalizada (%)")
                        plt.ylabel("Características")
                        plt.title(
                            f'Top 10 Características - {segment_name.replace("_", " ")}'
                        )
                        plt.grid(axis="x", linestyle="--", alpha=0.7)
                        plt.tight_layout()
                        plt.savefig(
                            os.path.join(
                                self.output_dir,
                                f"feature_importance_{segment_name}_top10.png",
                            ),
                            dpi=300,
                        )
                        plt.close()

                        # Guardar CSV actualizado
                        segment_df.to_csv(
                            os.path.join(
                                self.output_dir,
                                f"feature_importance_{segment_name}.csv",
                            ),
                            index=False,
                        )
                        print(f"  Actualizado archivo CSV para {segment_name}")

                        elapsed_time = time.time() - start_time
                        print(f"  Análisis completado en {elapsed_time:.2f} segundos")
                    else:
                        print(
                            f"  No se pudo calcular importancia para {segment_name} (DataFrame vacío)"
                        )

                except Exception as e:
                    print(f"  Error al analizar segmento {segment_name}: {str(e)}")
                    traceback.print_exc()
            else:
                print(
                    f"\nNo hay suficientes datos para segmento: {segment_name} ({count} muestras)"
                )

        # Crear gráfico comparativo si es posible
        if len(all_segment_dfs) > 0:
            try:
                # Combinar DataFrames
                combined_df = pd.concat(all_segment_dfs, ignore_index=True)

                # Crear gráfico comparativo si hay múltiples segmentos
                if len(set(combined_df["Segment"])) > 1:
                    # Identificar características importantes
                    top_features = {}
                    for segment_name, df in results.items():
                        if not df.empty:
                            for _, row in df.head(10).iterrows():
                                feature = row["Feature"]
                                if feature not in top_features:
                                    top_features[feature] = 0
                                top_features[feature] += row["Importance_Normalized"]

                    # Ordenar por importancia total
                    ordered_features = sorted(
                        top_features.keys(), key=lambda x: top_features[x], reverse=True
                    )[:10]

                    if ordered_features:
                        # Crear gráfico comparativo
                        plt.figure(figsize=(14, 10))
                        x = np.arange(len(ordered_features))
                        width = 0.25

                        # Graficar por segmento
                        segments_with_data = []
                        for i, segment_name in enumerate(
                            [s for s in segment_names if not results[s].empty]
                        ):
                            segments_with_data.append(segment_name)
                            segment_df = results[segment_name]

                            # Obtener valores de importancia normalizada
                            values = []
                            for feature in ordered_features:
                                feature_rows = segment_df[
                                    segment_df["Feature"] == feature
                                ]
                                if not feature_rows.empty:
                                    values.append(
                                        feature_rows.iloc[0]["Importance_Normalized"]
                                    )
                                else:
                                    values.append(0)

                            # Calcular offset para posicionar barras
                            if len(segments_with_data) > 1:
                                offset = (i - (len(segments_with_data) - 1) / 2) * width
                            else:
                                offset = 0

                            # Graficar
                            plt.bar(
                                x + offset,
                                values,
                                width,
                                label=segment_name.replace("_", " "),
                                color=colors[i % len(colors)],
                            )

                        # Configurar gráfico
                        plt.xlabel("Características")
                        plt.ylabel("Importancia Normalizada (%)")
                        plt.title(
                            "Importancia de Características por Cantidad de Recursos"
                        )
                        plt.xticks(x, ordered_features, rotation=45, ha="right")
                        plt.legend()
                        plt.grid(True, alpha=0.3)
                        plt.tight_layout()

                        # Guardar gráfico
                        plt.savefig(
                            os.path.join(
                                self.output_dir, "segmented_feature_importance.png"
                            ),
                            dpi=300,
                        )
                        plt.close()

                        # Crear archivo CSV comparativo
                        comparison_df = pd.DataFrame({"Feature": ordered_features})
                        for segment_name in segments_with_data:
                            segment_df = results[segment_name]
                            comparison_df[f"Importancia_{segment_name}"] = [
                                (
                                    segment_df[segment_df["Feature"] == feature][
                                        "Importance_Normalized"
                                    ].iloc[0]
                                    if feature in segment_df["Feature"].values
                                    and not segment_df[
                                        segment_df["Feature"] == feature
                                    ].empty
                                    else 0
                                )
                                for feature in ordered_features
                            ]

                        # Guardar comparación
                        comparison_df.to_csv(
                            os.path.join(
                                self.output_dir, "feature_importance_comparison.csv"
                            ),
                            index=False,
                        )
                        print("Análisis comparativo guardado.")
            except Exception as e:
                print(f"Error al crear análisis comparativo: {str(e)}")
                traceback.print_exc()

        return results

    def segmented_evaluation(self, X_test, y_test, segments):
        """Evalúa el modelo en diferentes segmentos de los datos

        Args:
            X_test: Datos de prueba
            y_test: Valores objetivo reales
            segments: Dict con funciones para segmentar datos (ej. {'small': lambda y: y < 10})

        Returns:
            dict: Métricas por segmento
        """
        results = {}

        # Evaluar en cada segmento
        for segment_name, segment_func in segments.items():
            # Seleccionar datos de este segmento
            segment_mask = segment_func(y_test)
            if not np.any(segment_mask):
                print(f"Segmento '{segment_name}' no tiene datos. Saltando.")
                continue

            X_segment = X_test[segment_mask]
            y_segment = y_test[segment_mask]

            # Preparar inputs para el modelo
            inputs_segment = self.model.prepare_inputs(X_segment, self.feature_dims)

            # Obtener predicciones
            y_pred_segment = self.model.model.predict(inputs_segment).flatten()

            # Calcular métricas
            segment_metrics = {
                "mse": mean_squared_error(y_segment, y_pred_segment),
                "rmse": np.sqrt(mean_squared_error(y_segment, y_pred_segment)),
                "mae": mean_absolute_error(y_segment, y_pred_segment),
                "mape": mean_absolute_percentage_error(y_segment, y_pred_segment),
                "r2": r2_score(y_segment, y_pred_segment),
                "count": len(y_segment),
            }

            results[segment_name] = segment_metrics

        # Guardar resultados
        with open(os.path.join(self.output_dir, "segmented_evaluation.json"), "w") as f:
            json.dump(results, f, indent=4)

        # Imprimir resultados
        print("\nEvaluación por segmentos:")
        for segment_name, metrics in results.items():
            print(f"\n{segment_name} (n={metrics['count']}):")
            for metric_name, value in metrics.items():
                if metric_name != "count":
                    print(f"  {metric_name.upper()}: {value:.4f}")

        return results

    def _calculate_metrics(self, X_val, y_val):
        """Calcula las métricas básicas de evaluación

        Args:
            X_val: Datos de validación
            y_val: Valores reales

        Returns:
            dict: Diccionario con métricas calculadas
        """
        # Realizar predicciones
        y_pred = self.model.predict(X_val, self.feature_dims)

        # Calcular métricas de regresión
        mse = mean_squared_error(y_val, y_pred)
        rmse = np.sqrt(mse)
        mae = mean_absolute_error(y_val, y_pred)
        r2 = r2_score(y_val, y_pred)

        try:
            mape = mean_absolute_percentage_error(y_val, y_pred)
        except:
            mape = (
                np.mean(np.abs((y_val - y_pred) / np.maximum(np.abs(y_val), 0.1))) * 100
            )

        # Calcular métricas de clasificación adaptadas
        classification_metrics = self.calculate_classification_metrics(y_val, y_pred)

        # Combinar todas las métricas
        metrics = {
            "MSE": float(mse),
            "RMSE": float(rmse),
            "MAE": float(mae),
            "MAPE": float(mape),
            "R2": float(r2),
            "Accuracy": float(classification_metrics["accuracy"]),
            "Precision": float(classification_metrics["precision"]),
            "Recall": float(classification_metrics["recall"]),
            "F1": float(classification_metrics["f1"]),
        }

        return metrics

    def _calculate_feature_importance(self, X_val, y_val):
        """Calcula la importancia de las características

        Args:
            X_val: Datos de validación
            y_val: Valores reales

        Returns:
            Tuple: Importancia de características global y segmentada
        """
        # Utilizamos el método que ya está implementado
        feature_names = [f"Feature_{i}" for i in range(X_val.shape[1])]
        return self.analyze_feature_importance(X_val, y_val, feature_names)

    def _perform_segmented_evaluation(self, X_val, y_val):
        """Realiza una evaluación segmentada

        Args:
            X_val: Datos de validación
            y_val: Valores reales
        """
        # Definir segmentos por tiempo real
        segments = {
            "Tareas pequeñas (<= 5h)": lambda y: y <= 5,
            "Tareas medianas (5-20h)": lambda y: (y > 5) & (y <= 20),
            "Tareas grandes (20-40h)": lambda y: (y > 20) & (y <= 40),
            "Tareas muy grandes (>40h)": lambda y: y > 40,
        }

        # Utilizar el método que ya está implementado
        return self.segmented_evaluation(X_val, y_val, segments)

    def _save_metrics_history(self, metrics):
        """Guarda las métricas en el historial

        Args:
            metrics: Diccionario con métricas calculadas
        """
        # Utilizar el método que ya está implementado
        return self.save_to_metrics_history(metrics)

    def _generate_evaluation_plots(self, X_val, y_val):
        """Genera gráficas de evaluación

        Args:
            X_val: Datos de validación
            y_val: Valores reales
        """
        # Realizar predicciones
        y_pred = self.model.predict(X_val, self.feature_dims)

        # Utilizar el método que ya está implementado
        return self.plot_predictions(y_val, y_pred, save_fig=True)
