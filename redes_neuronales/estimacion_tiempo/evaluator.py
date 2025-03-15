import os
import numpy as np
import pandas as pd
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


class ModelEvaluator:
    """Clase para evaluar el rendimiento de los modelos de estimación de tiempo"""

    def __init__(self, model, feature_dims, output_dir='models'):
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
            'accuracy': min(max(accuracy, 0), 1),
            'precision': min(max(precision, 0), 1),
            'recall': min(max(recall, 0), 1),
            'f1': min(max(f1, 0), 1),
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
            'MSE': mse,
            'RMSE': rmse,
            'MAE': mae,
            'MAPE': mape,
            'R2': r2,
            'Accuracy': classification_metrics['accuracy'],
            'Precision': classification_metrics['precision'],
            'Recall': classification_metrics['recall'],
            'F1': classification_metrics['f1'],
        }

        # Guardar métricas en archivo JSON
        metrics_path = os.path.join(self.output_dir, 'evaluation_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)

        # Guardar en historial de métricas
        self.save_to_metrics_history(metrics)

        print("\nMétricas de evaluación:")
        for metric_name, value in metrics.items():
            # Para métricas de clasificación, mostrar como porcentaje para mayor claridad
            if metric_name in ['Accuracy', 'Precision', 'Recall', 'F1']:
                print(f"  {metric_name}: {value*100:.2f}%")
            else:
                print(f"  {metric_name}: {value:.4f}")

        return metrics, y_pred.flatten()

    def save_to_metrics_history(self, metrics):
        """Guarda las métricas actuales en un historial

        Args:
            metrics: Diccionario con las métricas a guardar
        """
        history_path = os.path.join(self.output_dir, 'metrics_history.json')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Añadir timestamp a las métricas
        metrics_with_timestamp = {'timestamp': timestamp, 'metrics': metrics}

        # Cargar historial existente o crear uno nuevo
        try:
            if os.path.exists(history_path):
                with open(history_path, 'r') as f:
                    history = json.load(f)
                    if isinstance(history, list):
                        # Formato compatible con evaluate_metrics.py
                        history.append(metrics_with_timestamp)
                    else:
                        # Formato original con 'evaluations'
                        if 'evaluations' not in history:
                            history['evaluations'] = []
                        history['evaluations'].append(metrics_with_timestamp)
            else:
                # Crear nuevo historial (formato compatible con evaluate_metrics.py)
                history = [metrics_with_timestamp]
        except Exception as e:
            print(f"Error al cargar historial de métricas: {e}")
            history = [metrics_with_timestamp]  # Crear nuevo en caso de error

        # Guardar historial actualizado
        with open(history_path, 'w') as f:
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
        plt.plot([min_val, max_val], [min_val, max_val], 'r--')

        plt.xlabel('Tiempo real (horas)')
        plt.ylabel('Tiempo estimado (horas)')
        plt.title('Predicción vs Valor Real')
        plt.grid(True, alpha=0.3)

        # 2. Histograma de errores
        plt.subplot(2, 2, 2)
        errors = y_pred - y_true
        plt.hist(errors, bins=20, alpha=0.6, color='green')
        plt.axvline(x=0, color='r', linestyle='--')
        plt.xlabel('Error de predicción (horas)')
        plt.ylabel('Frecuencia')
        plt.title('Distribución de Errores')
        plt.grid(True, alpha=0.3)

        # 3. Plot de residuos
        plt.subplot(2, 2, 3)
        plt.scatter(y_pred, errors, alpha=0.6, color='purple')
        plt.axhline(y=0, color='r', linestyle='--')
        plt.xlabel('Tiempo estimado (horas)')
        plt.ylabel('Residuo (horas)')
        plt.title('Análisis de Residuos')
        plt.grid(True, alpha=0.3)

        # 4. Distribución de predicciones y valores reales
        plt.subplot(2, 2, 4)
        sns.kdeplot(y_true, label='Real', color='blue')
        sns.kdeplot(y_pred, label='Estimado', color='orange')
        plt.xlabel('Tiempo (horas)')
        plt.ylabel('Densidad')
        plt.title('Distribución de Tiempos')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        if save_fig:
            plt.savefig(os.path.join(self.output_dir, 'evaluation_plots.png'), dpi=300)
            print(
                f"Gráficos guardados en {os.path.join(self.output_dir, 'evaluation_plots.png')}"
            )

        plt.show()

    def analyze_feature_importance(self, X_test, y_test, feature_names=None):
        """Analiza la importancia de las características mediante perturbación

        Args:
            X_test: Datos de prueba
            y_test: Valores objetivo reales
            feature_names: Lista con nombres de características

        Returns:
            DataFrame: Importancia de características ordenadas
        """
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
                num_numeric_features + self.feature_dims['tipo_tarea'],
            )
        )
        fase_indices = list(
            range(
                num_numeric_features + self.feature_dims['tipo_tarea'],
                num_numeric_features
                + self.feature_dims['tipo_tarea']
                + self.feature_dims['fase'],
            )
        )

        # Definir características agrupadas para análisis
        feature_groups = {
            'Complejidad': [0],
            'Cantidad_Recursos': [1],
            'Carga_Trabajo_R1': [2],
            'Experiencia_R1': [3],
            'Carga_Trabajo_R2': [4],
            'Experiencia_R2': [5],
            'Carga_Trabajo_R3': [6],
            'Experiencia_R3': [7],
            'Experiencia_Equipo': [8],
            'Claridad_Requisitos': [9],
            'Tamaño_Tarea': [10],
            'Tipo_Tarea': tipo_indices,
            'Fase_Tarea': fase_indices,
        }

        # Predicciones base
        inputs_base = self.model.prepare_inputs(X_test, self.feature_dims)
        y_pred_base = self.model.model.predict(inputs_base).flatten()
        base_error = mean_squared_error(y_test, y_pred_base)

        # Obtener la columna de cantidad de recursos (escalada)
        recursos_scaled = X_test[:, 1]

        # Verificar distribución de valores únicos
        valores_unicos, conteo = np.unique(recursos_scaled, return_counts=True)
        print("\nDistribución de cantidad de recursos en los datos de prueba:")
        for valor, count in zip(valores_unicos, conteo):
            print(f"  Recursos = {valor}: {count} registros")

        # Identificar los valores escalados correspondientes a 1, 2, 3 recursos
        # Tomamos los valores únicos ordenados y asumimos que corresponden a 1, 2, 3 recursos
        valores_ordenados = np.sort(valores_unicos)

        if len(valores_ordenados) >= 3:
            # Podemos asignar los valores ordenados a 1, 2, 3+ recursos
            valor_1_recurso = valores_ordenados[0]
            valor_2_recursos = valores_ordenados[1]
            valor_3_recursos = valores_ordenados[2]

            print(f"\nValores escalados identificados:")
            print(f"  1 Recurso: {valor_1_recurso}")
            print(f"  2 Recursos: {valor_2_recursos}")
            print(f"  3 o más Recursos: {valor_3_recursos}")

            # Crear segmentos por cantidad de recursos
            resource_segments = {
                '1 Recurso': np.isclose(recursos_scaled, valor_1_recurso, rtol=1e-5),
                '2 Recursos': np.isclose(recursos_scaled, valor_2_recursos, rtol=1e-5),
                '3 o más Recursos': np.isclose(
                    recursos_scaled, valor_3_recursos, rtol=1e-5
                ),
            }
        elif len(valores_ordenados) == 2:
            # Solo hay datos para 2 valores diferentes
            print(f"\nValores escalados identificados (solo 2 valores):")
            print(f"  Valor más bajo (posible 1 Recurso): {valores_ordenados[0]}")
            print(f"  Valor más alto (posible 2+ Recursos): {valores_ordenados[1]}")

            resource_segments = {
                'Recursos Menores': np.isclose(
                    recursos_scaled, valores_ordenados[0], rtol=1e-5
                ),
                'Recursos Mayores': np.isclose(
                    recursos_scaled, valores_ordenados[1], rtol=1e-5
                ),
            }
        else:
            # Hay menos de 2 valores únicos
            print(
                "\nNo hay suficientes valores diferentes para crear segmentos por recursos."
            )
            resource_segments = {}

        # Para cada segmento, calcular importancia de características relevantes
        segment_results = {}

        for segment_name, segment_mask in resource_segments.items():
            count = np.sum(segment_mask)
            if count < 5:
                print(
                    f"Solo {count} registros para el segmento '{segment_name}'. Saltando por insuficiencia de datos."
                )
                continue

            print(f"Analizando segmento '{segment_name}' con {count} registros.")
            X_segment = X_test[segment_mask]
            y_segment = y_test[segment_mask]

            # Determinar características relevantes según el número de recursos
            relevant_features = list(feature_groups.keys())

            if '1 Recurso' in segment_name or 'Recursos Menores' in segment_name:
                # Excluir información de recursos 2 y 3
                relevant_features = [
                    f for f in relevant_features if 'R2' not in f and 'R3' not in f
                ]
            elif '2 Recursos' in segment_name:
                # Excluir información del recurso 3
                relevant_features = [f for f in relevant_features if 'R3' not in f]

            print(
                f"Características consideradas para '{segment_name}': {relevant_features}"
            )

            # Calcular importancia para cada característica o grupo de características
            importance_scores = []

            # Predicciones base para este segmento
            inputs_segment_base = self.model.prepare_inputs(
                X_segment, self.feature_dims
            )
            y_pred_segment_base = self.model.model.predict(
                inputs_segment_base
            ).flatten()
            segment_base_error = mean_squared_error(y_segment, y_pred_segment_base)

            for feature_name in relevant_features:
                indices = feature_groups[feature_name]

                # Copiar datos y perturbar la característica o grupo de características
                X_perturbed = X_segment.copy()

                # Perturbar todas las columnas del grupo
                for idx in indices:
                    X_perturbed[:, idx] = np.random.permutation(X_perturbed[:, idx])

                # Predecir con datos perturbados
                inputs_perturbed = self.model.prepare_inputs(
                    X_perturbed, self.feature_dims
                )
                y_pred_perturbed = self.model.model.predict(inputs_perturbed).flatten()

                # Calcular incremento en error
                perturbed_error = mean_squared_error(y_segment, y_pred_perturbed)
                importance = perturbed_error - segment_base_error

                # Usar valor absoluto para importancia
                importance = abs(importance)

                importance_scores.append((feature_name, importance))

            # Ordenar por importancia
            importance_scores.sort(key=lambda x: x[1], reverse=True)

            # Crear DataFrame
            importance_df = pd.DataFrame(
                importance_scores, columns=['Feature', 'Importance']
            )

            # Normalización más representativa: dividir por la suma total
            sum_importance = importance_df['Importance'].sum()
            if sum_importance > 0:
                importance_df['Importance_Normalized'] = (
                    importance_df['Importance'] / sum_importance
                )
            else:
                importance_df['Importance_Normalized'] = 0

            segment_results[segment_name] = importance_df

        # También calcular importancia global (todos los datos)
        global_importance_scores = []

        # Usar las características agrupadas para todos los datos
        for feature_name, indices in feature_groups.items():
            # Copiar datos y perturbar la característica o grupo
            X_perturbed = X_test.copy()

            # Perturbar todas las columnas del grupo
            for idx in indices:
                X_perturbed[:, idx] = np.random.permutation(X_perturbed[:, idx])

            # Predecir con datos perturbados
            inputs_perturbed = self.model.prepare_inputs(X_perturbed, self.feature_dims)
            y_pred_perturbed = self.model.model.predict(inputs_perturbed).flatten()

            # Calcular incremento en error
            perturbed_error = mean_squared_error(y_test, y_pred_perturbed)
            importance = abs(perturbed_error - base_error)

            global_importance_scores.append((feature_name, importance))

        # Ordenar por importancia
        global_importance_scores.sort(key=lambda x: x[1], reverse=True)

        # Crear DataFrame global
        global_importance_df = pd.DataFrame(
            global_importance_scores, columns=['Feature', 'Importance']
        )

        # Normalizar de manera más representativa
        sum_importance = global_importance_df['Importance'].sum()
        if sum_importance > 0:
            global_importance_df['Importance_Normalized'] = (
                global_importance_df['Importance'] / sum_importance
            )
        else:
            global_importance_df['Importance_Normalized'] = 0

        # Guardar resultados globales
        global_importance_df.to_csv(
            os.path.join(self.output_dir, 'global_feature_importance.csv'), index=False
        )

        # Visualizar importancia global
        plt.figure(figsize=(12, 8))
        plt.barh(
            global_importance_df['Feature'],
            global_importance_df['Importance_Normalized'],
            color='teal',
        )
        plt.xlabel('Importancia Normalizada')
        plt.ylabel('Característica')
        plt.title('Importancia Global de Características')
        plt.tight_layout()
        plt.savefig(
            os.path.join(self.output_dir, 'global_feature_importance.png'), dpi=300
        )

        # Crear un plot con subplots para cada segmento
        n_segments = len(segment_results)
        if n_segments > 0:
            fig, axes = plt.subplots(n_segments, 1, figsize=(12, 6 * n_segments))

            # Si solo hay un segmento, axes no será un array
            if n_segments == 1:
                axes = [axes]

            for i, (segment_name, importance_df) in enumerate(segment_results.items()):
                # Guardar resultados por segmento
                importance_df.to_csv(
                    os.path.join(
                        self.output_dir,
                        f'feature_importance_{segment_name.replace(" ", "_")}.csv',
                    ),
                    index=False,
                )

                # Visualizar
                axes[i].barh(
                    importance_df['Feature'],
                    importance_df['Importance_Normalized'],
                    color='royalblue',
                )
                axes[i].set_xlabel('Importancia Normalizada')
                axes[i].set_ylabel('Característica')
                axes[i].set_title(f'Importancia de Características - {segment_name}')

            plt.tight_layout()
            plt.savefig(
                os.path.join(self.output_dir, 'segmented_feature_importance.png'),
                dpi=300,
            )
        else:
            print(
                "\nNo se encontraron suficientes datos para hacer análisis por segmentos de recursos."
            )

        plt.close('all')  # Cerrar todas las figuras para evitar mostrarlas en Jupyter

        print(
            f"\nAnálisis de importancia completado. Resultados guardados en {self.output_dir}"
        )

        # Mostrar gráficas individualmente para visualización interactiva
        # Importancia global
        plt.figure(figsize=(12, 8))
        plt.barh(
            global_importance_df['Feature'],
            global_importance_df['Importance_Normalized'],
            color='teal',
        )
        plt.xlabel('Importancia Normalizada')
        plt.ylabel('Característica')
        plt.title('Importancia Global de Características')
        plt.tight_layout()
        plt.show()

        # Mostrar cada segmento en una gráfica separada
        for segment_name, importance_df in segment_results.items():
            plt.figure(figsize=(10, 6))
            plt.barh(
                importance_df['Feature'],
                importance_df['Importance_Normalized'],
                color='royalblue',
            )
            plt.xlabel('Importancia Normalizada')
            plt.ylabel('Característica')
            plt.title(f'Importancia de Características - {segment_name}')
            plt.tight_layout()
            plt.show()

        return global_importance_df, segment_results

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
                'mse': mean_squared_error(y_segment, y_pred_segment),
                'rmse': np.sqrt(mean_squared_error(y_segment, y_pred_segment)),
                'mae': mean_absolute_error(y_segment, y_pred_segment),
                'mape': mean_absolute_percentage_error(y_segment, y_pred_segment),
                'r2': r2_score(y_segment, y_pred_segment),
                'count': len(y_segment),
            }

            results[segment_name] = segment_metrics

        # Guardar resultados
        with open(os.path.join(self.output_dir, 'segmented_evaluation.json'), 'w') as f:
            json.dump(results, f, indent=4)

        # Imprimir resultados
        print("\nEvaluación por segmentos:")
        for segment_name, metrics in results.items():
            print(f"\n{segment_name} (n={metrics['count']}):")
            for metric_name, value in metrics.items():
                if metric_name != 'count':
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
            'MSE': float(mse),
            'RMSE': float(rmse),
            'MAE': float(mae),
            'MAPE': float(mape),
            'R2': float(r2),
            'Accuracy': float(classification_metrics['accuracy']),
            'Precision': float(classification_metrics['precision']),
            'Recall': float(classification_metrics['recall']),
            'F1': float(classification_metrics['f1']),
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
            'Tareas pequeñas (<= 5h)': lambda y: y <= 5,
            'Tareas medianas (5-20h)': lambda y: (y > 5) & (y <= 20),
            'Tareas grandes (20-40h)': lambda y: (y > 20) & (y <= 40),
            'Tareas muy grandes (>40h)': lambda y: y > 40,
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
