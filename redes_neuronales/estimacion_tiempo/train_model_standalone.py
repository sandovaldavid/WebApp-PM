import os
import sys
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
import joblib
import matplotlib.pyplot as plt
from rnn_model import AdvancedRNNEstimator


class StandaloneDataProcessor:
    """Versión simplificada del procesador de datos que no depende de Django"""

    def __init__(self, data_path=None):
        """Inicializa el procesador de datos.

        Args:
            data_path: Ruta al archivo CSV de datos
        """
        self.data_path = data_path
        self.scalers = {}
        self.encoders = {}
        self.feature_dims = None

    def load_data(self):
        """Carga datos desde el CSV"""
        try:
            if self.data_path:
                self.data = pd.read_csv(self.data_path)
                print(f"Datos cargados correctamente. Forma: {self.data.shape}")
                return self.data
            else:
                raise ValueError("Ruta de datos no especificada")
        except Exception as e:
            print(f"Error al cargar datos: {e}")
            return None

    def preprocess_data(self, test_size=0.2, val_size=0.0):
        """Procesa los datos para entrenar el modelo

        Args:
            test_size: Proporción del conjunto de datos a usar como prueba/validación (0.0-1.0)
            val_size: No usado en esta versión, para compatibilidad con DataProcessor

        Returns:
            Tupla de (X_train, X_val, y_train, y_val, feature_dims)
        """
        if hasattr(self, 'data') and self.data is not None:
            df = self.data.copy()

            # Verificar columnas requeridas
            required_cols = [
                'Complejidad',
                'Tipo_Tarea',
                'Fase_Tarea',
                'Cantidad_Recursos',
                'Carga_Trabajo_R1',
                'Experiencia_R1',
                'Experiencia_Equipo',
                'Claridad_Requisitos',
                'Tamaño_Tarea',
                'Tiempo_Ejecucion',
            ]

            # Comprobar si las columnas existen, considerando mayúsculas y minúsculas
            df_columns_lower = [col.lower() for col in df.columns]
            missing_cols = []
            column_mapping = {}

            for req_col in required_cols:
                found = False
                for i, col in enumerate(df.columns):
                    if col.lower() == req_col.lower():
                        column_mapping[req_col] = col
                        found = True
                        break
                if not found:
                    missing_cols.append(req_col)

            if missing_cols:
                print(f"Columnas requeridas no encontradas: {missing_cols}")
                print("Columnas disponibles:", df.columns.tolist())
                raise ValueError(f"Columnas faltantes en dataset: {missing_cols}")

            # Renombrar columnas si es necesario
            if column_mapping:
                df = df.rename(columns=column_mapping)

            # Validar y rellenar valores faltantes en cargas de trabajo y experiencia
            for i in range(1, 4):  # Para recursos 1, 2, y 3
                carga_col = f'Carga_Trabajo_R{i}'
                exp_col = f'Experiencia_R{i}'

                # Si existe la columna pero tiene valores nulos
                if carga_col in df.columns:
                    df[carga_col] = df[carga_col].fillna(0)
                else:
                    df[carga_col] = 0

                if exp_col in df.columns:
                    df[exp_col] = df[exp_col].fillna(0)
                else:
                    df[exp_col] = 0

            # Crear encoders para categorías
            tipo_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
            fase_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')

            # Ajustar encoders con todas las categorías posibles
            tipo_encoder.fit(df[['Tipo_Tarea']])
            fase_encoder.fit(df[['Fase_Tarea']])

            # Transformar las categorías
            tipo_encoded = tipo_encoder.transform(df[['Tipo_Tarea']])
            fase_encoded = fase_encoder.transform(df[['Fase_Tarea']])

            # Guardar encoders
            self.encoders['tipo_tarea'] = tipo_encoder
            self.encoders['fase'] = fase_encoder

            # Características numéricas
            numeric_features = [
                'Complejidad',
                'Cantidad_Recursos',
                'Carga_Trabajo_R1',
                'Experiencia_R1',
                'Carga_Trabajo_R2',
                'Experiencia_R2',
                'Carga_Trabajo_R3',
                'Experiencia_R3',
                'Experiencia_Equipo',
                'Claridad_Requisitos',
                'Tamaño_Tarea',
            ]

            # Asegurar que todas las columnas numéricas existen
            for col in numeric_features:
                if col not in df.columns:
                    df[col] = 0

            # Escalar características numéricas
            scaler = StandardScaler()
            numeric_data = df[numeric_features].values
            numeric_scaled = scaler.fit_transform(numeric_data)

            # Guardar el scaler
            self.scalers['numeric'] = scaler

            # Combinar todas las características
            X = np.hstack((numeric_scaled, tipo_encoded, fase_encoded))
            y = df['Tiempo_Ejecucion'].values

            # Guardar dimensiones y nombres de características para referencia
            self.feature_dims = {
                'numeric': len(numeric_features),
                'tipo_tarea': tipo_encoded.shape[1],
                'fase': fase_encoded.shape[1],
            }

            # Dividir en conjuntos de entrenamiento y validación
            X_train, X_val, y_train, y_val = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            print("Preprocesamiento completo.")
            print(f"Dimensiones de features: {self.feature_dims}")
            print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
            print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")

            return X_train, X_val, y_train, y_val, self.feature_dims
        else:
            raise ValueError("No hay datos para procesar. Ejecute load_data primero.")

    def save_preprocessors(self, output_dir='models'):
        """Guarda los preprocessors para uso posterior"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        joblib.dump(self.scalers, os.path.join(output_dir, 'scalers.pkl'))
        joblib.dump(self.encoders, os.path.join(output_dir, 'encoders.pkl'))
        joblib.dump(self.feature_dims, os.path.join(output_dir, 'feature_dims.pkl'))

        print(f"Preprocessors guardados en {output_dir}")


def parse_args():
    parser = argparse.ArgumentParser(
        description='Entrenar modelo RNN para estimación de tiempos (versión standalone)'
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default='estimacion_tiempos_optimizado.csv',
        help='Ruta al archivo CSV con datos de entrenamiento',
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='models',
        help='Directorio para guardar el modelo y resultados',
    )
    parser.add_argument(
        '--epochs', type=int, default=100, help='Número de épocas para entrenar'
    )
    parser.add_argument(
        '--bidirectional', action='store_true', help='Usar capa RNN bidireccional'
    )
    parser.add_argument(
        '--rnn-type',
        type=str,
        default='GRU',
        choices=['GRU', 'LSTM'],
        help='Tipo de capa recurrente a usar',
    )

    return parser.parse_args()


def train_model(X_train, y_train, X_val, y_val, feature_dims, config):
    """Entrena el modelo con los datos proporcionados"""
    # Configurar modelo
    model_config = {
        'rnn_units': 64,
        'dense_units': [128, 64, 32],
        'dropout_rate': 0.3,
        'learning_rate': 0.001,
        'l2_reg': 0.001,
        'use_bidirectional': config.bidirectional,
        'rnn_type': config.rnn_type,
        'activation': 'relu',
        'batch_size': 32,
        'epochs': config.epochs,
    }

    # Inicializar y construir el modelo
    estimator = AdvancedRNNEstimator(model_config)
    estimator.build_model(feature_dims)

    # Entrenar el modelo
    history = estimator.train(X_train, y_train, X_val, y_val, feature_dims)

    # Guardar el modelo
    estimator.save(model_dir=config.output_dir, name='tiempo_estimator')

    return estimator, history


def evaluate_model(estimator, X_val, y_val, feature_dims, output_dir):
    """Evalúa el modelo entrenado"""
    # Preparar inputs
    inputs = estimator.prepare_inputs(X_val, feature_dims)

    # Evaluar modelo
    metrics = estimator.model.evaluate(inputs, y_val, verbose=1)

    # Realizar predicciones
    y_pred = estimator.model.predict(inputs).flatten()

    # Calcular errores
    mse = np.mean((y_val - y_pred) ** 2)
    rmse = np.sqrt(mse)
    mae = np.mean(np.abs(y_val - y_pred))

    # R²
    ss_res = np.sum((y_val - y_pred) ** 2)
    ss_tot = np.sum((y_val - np.mean(y_val)) ** 2)
    r2 = 1 - (ss_res / ss_tot)

    # Guardar métricas
    metrics_dict = {
        'mse': float(mse),
        'rmse': float(rmse),
        'mae': float(mae),
        'r2': float(r2),
    }

    # Guardar resultados
    import json

    with open(os.path.join(output_dir, 'evaluation_metrics.json'), 'w') as f:
        json.dump(metrics_dict, f, indent=4)

    print("\nMétricas de evaluación:")
    for name, value in metrics_dict.items():
        print(f"  {name.upper()}: {value:.4f}")

    # Crear gráficos de comparación
    plt.figure(figsize=(12, 6))

    plt.subplot(1, 2, 1)
    plt.scatter(y_val, y_pred, alpha=0.5)
    plt.plot([min(y_val), max(y_val)], [min(y_val), max(y_val)], 'r--')
    plt.xlabel('Tiempo real')
    plt.ylabel('Tiempo predicho')
    plt.title('Comparación de predicciones')

    plt.subplot(1, 2, 2)
    plt.hist(y_pred - y_val, bins=20, alpha=0.5)
    plt.axvline(x=0, color='r', linestyle='--')
    plt.xlabel('Error de predicción')
    plt.ylabel('Frecuencia')
    plt.title('Distribución de errores')

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'prediction_analysis.png'))
    plt.close()

    # Crear gráfico de historia de entrenamiento
    estimator.plot_history(save_path=os.path.join(output_dir, 'training_history.png'))

    return metrics_dict, y_pred


def main():
    """Función principal para entrenamiento y evaluación"""
    # Parsear argumentos
    args = parse_args()

    print(
        "\n=== Entrenamiento de modelo RNN para estimación de tiempos (standalone) ==="
    )
    print(f"Archivo de datos: {args.data_path}")
    print(f"Directorio de salida: {args.output_dir}")
    print(
        f"Tipo de RNN: {args.rnn_type} {'bidireccional' if args.bidirectional else 'unidireccional'}"
    )

    # Asegurar que existe el directorio de salida
    if not os.path.exists(args.output_dir):
        os.makedirs(args.output_dir)

    # 1. Cargar y procesar datos
    print("\n[1/4] Cargando datos...")
    processor = StandaloneDataProcessor(data_path=args.data_path)
    data = processor.load_data()

    if data is None:
        print("Error: No se pudieron cargar los datos. Verifique la ruta del archivo.")
        return

    # 2. Preprocesar datos
    print("\n[2/4] Preprocesando datos...")
    try:
        X_train, X_val, y_train, y_val, feature_dims = processor.preprocess_data()
        processor.save_preprocessors(output_dir=args.output_dir)
    except Exception as e:
        print(f"Error al preprocesar datos: {str(e)}")
        import traceback

        print(traceback.format_exc())
        return

    # 3. Entrenar modelo
    print("\n[3/4] Entrenando modelo...")
    estimator, history = train_model(X_train, y_train, X_val, y_val, feature_dims, args)

    # 4. Evaluar modelo
    print("\n[4/4] Evaluando modelo...")
    metrics, predictions = evaluate_model(
        estimator, X_val, y_val, feature_dims, args.output_dir
    )

    print("\n=== Entrenamiento completado exitosamente ===")
    print(f"Todos los archivos han sido guardados en: {args.output_dir}")
    print(f"R²: {metrics['r2']:.4f}, RMSE: {metrics['rmse']:.4f}")

    return estimator, processor, metrics


if __name__ == "__main__":
    main()
