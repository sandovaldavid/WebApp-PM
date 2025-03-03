import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    mean_squared_error, mean_absolute_error, r2_score,
    mean_absolute_percentage_error
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
        
        # Calcular métricas
        metrics = {
            'mse': mean_squared_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'mae': mean_absolute_error(y_test, y_pred),
            'mape': mean_absolute_percentage_error(y_test, y_pred),
            'r2': r2_score(y_test, y_pred)
        }
        
        # Guardar métricas en archivo JSON
        metrics_path = os.path.join(self.output_dir, 'evaluation_metrics.json')
        with open(metrics_path, 'w') as f:
            json.dump(metrics, f, indent=4)
            
        print("\nMétricas de evaluación:")
        for metric_name, value in metrics.items():
            print(f"  {metric_name.upper()}: {value:.4f}")
            
        return metrics, y_pred.flatten()
    
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
            print(f"Gráficos guardados en {os.path.join(self.output_dir, 'evaluation_plots.png')}")
            
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
            print("Nombres de características no proporcionados o incorrectos. Usando índices.")
            feature_names = [f"Feature_{i}" for i in range(X_test.shape[1])]
            
        # Predicciones base
        inputs_base = self.model.prepare_inputs(X_test, self.feature_dims)
        y_pred_base = self.model.model.predict(inputs_base).flatten()
        base_error = mean_squared_error(y_test, y_pred_base)
        
        # Calcular importancia mediante perturbación
        importance_scores = []
        
        for i in range(X_test.shape[1]):
            # Copiar datos y perturbar una característica
            X_perturbed = X_test.copy()
            X_perturbed[:, i] = np.random.permutation(X_perturbed[:, i])
            
            # Predecir con datos perturbados
            inputs_perturbed = self.model.prepare_inputs(X_perturbed, self.feature_dims)
            y_pred_perturbed = self.model.model.predict(inputs_perturbed).flatten()
            
            # Calcular incremento en error
            perturbed_error = mean_squared_error(y_test, y_pred_perturbed)
            importance = perturbed_error - base_error
            
            importance_scores.append((feature_names[i], importance))
        
        # Ordenar por importancia
        importance_scores.sort(key=lambda x: x[1], reverse=True)
        importance_df = pd.DataFrame(importance_scores, columns=['Feature', 'Importance'])
        
        # Normalizar importancia
        importance_df['Importance_Normalized'] = importance_df['Importance'] / importance_df['Importance'].max()
        
        # Guardar resultados
        importance_df.to_csv(os.path.join(self.output_dir, 'feature_importance.csv'), index=False)
        
        # Visualizar importancia
        plt.figure(figsize=(10, 6))
        plt.barh(importance_df['Feature'], importance_df['Importance_Normalized'])
        plt.xlabel('Importancia Normalizada')
        plt.ylabel('Característica')
        plt.title('Importancia de Características')
        plt.tight_layout()
        plt.savefig(os.path.join(self.output_dir, 'feature_importance.png'), dpi=300)
        plt.show()
        
        return importance_df
    
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
                'count': len(y_segment)
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