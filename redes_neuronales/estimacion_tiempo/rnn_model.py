import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.layers import (
    Dense,
    LSTM,
    GRU,
    Input,
    Dropout,
    BatchNormalization,
    Concatenate,
    Embedding,
    Flatten,
    Bidirectional,
    TimeDistributed,
)
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
import matplotlib.pyplot as plt
import joblib


class AdvancedRNNEstimator:
    """Modelo de red neuronal recurrente para estimación de tiempos avanzada"""

    def __init__(self, config=None):
        """Inicializa el modelo con configuración personalizable

        Args:
            config: Diccionario de parámetros de configuración
        """
        # Configuración por defecto
        self.default_config = {
            'rnn_units': 64,
            'dense_units': [128, 64, 32],
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'l2_reg': 0.001,
            'use_bidirectional': True,
            'rnn_type': 'GRU',  # 'LSTM' o 'GRU'
            'activation': 'relu',
            'batch_size': 32,
            'epochs': 100,
        }

        # Usar configuración proporcionada o la predeterminada
        self.config = config if config is not None else self.default_config
        self.model = None
        self.history = None

    def build_model(self, feature_dims):
        """Construye el modelo RNN para estimación de tiempo

        Args:
            feature_dims: Diccionario con dimensiones de cada tipo de feature
        """
        # Verificar si feature_dims es válido
        if not isinstance(feature_dims, dict) or not all(
            k in feature_dims for k in ['numeric', 'tipo_tarea', 'fase']
        ):
            raise ValueError(
                "feature_dims debe ser un diccionario con claves 'numeric', 'tipo_tarea', 'fase'"
            )

        # 1. Entrada para características numéricas
        numeric_input = Input(shape=(feature_dims['numeric'],), name='numeric_input')

        # 2. Reshape para entrada recurrente
        reshaped_numeric = tf.expand_dims(numeric_input, axis=1, name='expand_dims')

        # 3. Capas recurrentes - GRU o LSTM según configuración
        if self.config['rnn_type'] == 'LSTM':
            rnn_layer = LSTM
        else:
            rnn_layer = GRU

        if self.config['use_bidirectional']:
            rnn = Bidirectional(
                rnn_layer(
                    self.config['rnn_units'],
                    return_sequences=False,
                    kernel_regularizer=l2(self.config['l2_reg']),
                    recurrent_regularizer=l2(self.config['l2_reg']),
                    name='bidirectional_rnn',
                )
            )(reshaped_numeric)
        else:
            rnn = rnn_layer(
                self.config['rnn_units'],
                return_sequences=False,
                kernel_regularizer=l2(self.config['l2_reg']),
                recurrent_regularizer=l2(self.config['l2_reg']),
                name='rnn',
            )(reshaped_numeric)

        # 4. Entrada y procesamiento para tipo de tarea (one-hot)
        tipo_tarea_input = Input(
            shape=(feature_dims['tipo_tarea'],), name='tipo_tarea_input'
        )
        tipo_tarea_dense = Dense(
            32,
            activation=self.config['activation'],
            kernel_regularizer=l2(self.config['l2_reg']),
            name='tipo_tarea_dense',
        )(tipo_tarea_input)

        # 5. Entrada y procesamiento para fase (one-hot)
        fase_input = Input(shape=(feature_dims['fase'],), name='fase_input')
        fase_dense = Dense(
            32,
            activation=self.config['activation'],
            kernel_regularizer=l2(self.config['l2_reg']),
            name='fase_dense',
        )(fase_input)

        # 6. Concatenar todas las características
        combined = Concatenate(name='concatenate_features')(
            [rnn, tipo_tarea_dense, fase_dense]
        )

        # 7. Capas densas con regularización y normalización
        x = combined
        for i, units in enumerate(self.config['dense_units']):
            x = Dense(
                units,
                activation=self.config['activation'],
                kernel_regularizer=l2(self.config['l2_reg']),
                name=f'dense_{i}',
            )(x)
            x = BatchNormalization(name=f'batch_norm_{i}')(x)
            x = Dropout(self.config['dropout_rate'], name=f'dropout_{i}')(x)

        # 8. Capa de salida para estimación de tiempo
        output = Dense(1, name='output')(x)

        # 9. Construir y compilar el modelo
        self.model = Model(
            inputs=[numeric_input, tipo_tarea_input, fase_input], outputs=output
        )

        self.model.compile(
            optimizer=Adam(learning_rate=self.config['learning_rate']),
            loss='mse',
            metrics=['mae', 'mape'],
        )

        return self.model

    def prepare_inputs(self, X, feature_dims):
        """Prepara los inputs separados para el modelo a partir de X

        Args:
            X: Array con todas las características concatenadas
            feature_dims: Diccionario con dimensiones de cada tipo de feature

        Returns:
            lista de arrays numpy para cada input del modelo
        """
        # Verificar dimensiones
        if X.shape[1] != (
            feature_dims['numeric'] + feature_dims['tipo_tarea'] + feature_dims['fase']
        ):
            raise ValueError(
                f"Dimensiones de X no coinciden con feature_dims: {X.shape[1]} vs {sum(feature_dims.values())}"
            )

        # Separar características por tipo
        numeric_data = X[:, : feature_dims['numeric']]
        tipo_tarea_data = X[
            :,
            feature_dims['numeric'] : feature_dims['numeric']
            + feature_dims['tipo_tarea'],
        ]
        fase_data = X[:, feature_dims['numeric'] + feature_dims['tipo_tarea'] :]

        return [numeric_data, tipo_tarea_data, fase_data]

    def train(
        self,
        X_train,
        y_train,
        X_val=None,
        y_val=None,
        feature_dims=None,
        callbacks=None,
    ):
        """Entrena el modelo con los datos proporcionados

        Args:
            X_train: Datos de entrenamiento
            y_train: Etiquetas de entrenamiento
            X_val: Datos de validación
            y_val: Etiquetas de validación
            feature_dims: Diccionario con dimensiones de características
            callbacks: Lista de callbacks para usar durante el entrenamiento

        Returns:
            History object con datos de entrenamiento
        """
        if self.model is None:
            self.build_model(feature_dims)

        # Preparar los inputs
        train_inputs = self.prepare_inputs(X_train, feature_dims)

        # Configurar los datos de validación si se proporcionan
        validation_data = None
        if X_val is not None and y_val is not None:
            val_inputs = self.prepare_inputs(X_val, feature_dims)
            validation_data = (val_inputs, y_val)

        # Definir callbacks por defecto con mayor patience para EarlyStopping
        default_callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=30,  # Aumentado de 15 a 30 para permitir más épocas
                restore_best_weights=True,
                verbose=1,  # Añadido para ver cuando se activa
            ),
            # Añadir más callbacks por defecto para mejor monitoreo
            tf.keras.callbacks.ReduceLROnPlateau(
                monitor='val_loss' if validation_data else 'loss',
                factor=0.5,
                patience=10,
                min_lr=1e-6,
                verbose=1,
            ),
        ]

        # Combinar con callbacks proporcionados por el usuario, priorizando estos últimos
        all_callbacks = default_callbacks.copy()
        if callbacks:
            # Asegurarnos que los callbacks del usuario se ejecutan después
            all_callbacks.extend(callbacks)

        # Entrenar modelo
        history = self.model.fit(
            train_inputs,
            y_train,
            epochs=self.config.get('epochs', 100),
            batch_size=self.config.get('batch_size', 32),
            validation_data=validation_data,
            verbose=1,
            callbacks=all_callbacks,
        )

        # Guardar historia para análisis posterior
        self.history = history

        return history

    def predict(self, X, feature_dims):
        """Realiza predicciones con el modelo entrenado

        Args:
            X: Datos para predicción
            feature_dims: Diccionario con dimensiones de features

        Returns:
            Predicciones del modelo
        """
        if self.model is None:
            raise ValueError(
                "El modelo no está entrenado. Ejecute build_model y train primero."
            )

        # Preparar inputs
        inputs = self.prepare_inputs(X, feature_dims)

        # Realizar predicción
        predictions = self.model.predict(inputs)

        return predictions.flatten()

    def evaluate(self, X, y, feature_dims):
        """Evalúa el modelo con datos de test

        Args:
            X: Datos de test
            y: Valores objetivo reales
            feature_dims: Diccionario con dimensiones de features

        Returns:
            Diccionario con métricas de evaluación
        """
        if self.model is None:
            raise ValueError(
                "El modelo no está entrenado. Ejecute build_model y train primero."
            )

        # Preparar inputs
        inputs = self.prepare_inputs(X, feature_dims)

        # Evaluar el modelo
        metrics = self.model.evaluate(inputs, y, verbose=1)

        # Crear diccionario de métricas
        metrics_dict = {'loss': metrics[0], 'mae': metrics[1], 'mape': metrics[2]}

        # Realizar predicciones para análisis adicional
        y_pred = self.model.predict(inputs).flatten()

        # Calcular error cuadrático medio (MSE)
        mse = np.mean((y - y_pred) ** 2)
        metrics_dict['mse'] = mse

        # Calcular raíz del error cuadrático medio (RMSE)
        rmse = np.sqrt(mse)
        metrics_dict['rmse'] = rmse

        # R²
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot)
        metrics_dict['r2'] = r2

        return metrics_dict

    def save(self, model_dir='models', name='rnn_estimator'):
        """Guarda el modelo y la configuración

        Args:
            model_dir: Directorio para guardar el modelo
            name: Nombre base para los archivos
        """
        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # Guardar modelo
        model_path = os.path.join(model_dir, f'{name}_model.keras')
        self.model.save(model_path)

        # Guardar configuración
        config_path = os.path.join(model_dir, f'{name}_config.joblib')
        joblib.dump(self.config, config_path)

        print(f"Modelo guardado en {model_path}")
        print(f"Configuración guardada en {config_path}")

    @classmethod
    def load(cls, model_dir='models', name='rnn_estimator'):
        """Carga un modelo previamente guardado

        Args:
            model_dir: Directorio donde está guardado el modelo
            name: Nombre base de los archivos

        Returns:
            Instancia de AdvancedRNNEstimator con el modelo cargado
        """
        model_path = os.path.join(model_dir, f'{name}_model.keras')
        config_path = os.path.join(model_dir, f'{name}_config.joblib')

        # Verificar que los archivos existen
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            raise FileNotFoundError(
                f"No se encontraron los archivos del modelo en {model_dir}"
            )

        # Cargar configuración
        config = joblib.load(config_path)

        # Crear instancia
        instance = cls(config)

        # Cargar modelo
        instance.model = load_model(model_path)

        return instance

    def plot_history(self, save_path=None):
        """Grafica la historia del entrenamiento

        Args:
            save_path: Ruta donde guardar la gráfica (opcional)
        """
        if self.history is None:
            raise ValueError("No hay historia de entrenamiento. Ejecute train primero.")

        # Crear figura
        plt.figure(figsize=(12, 5))

        # Gráfica de pérdida
        plt.subplot(1, 2, 1)
        plt.plot(self.history.history['loss'], label='Train')
        if 'val_loss' in self.history.history:
            plt.plot(self.history.history['val_loss'], label='Validation')
        plt.title('Loss')
        plt.xlabel('Epoch')
        plt.ylabel('Loss')
        plt.legend()
        plt.grid(True, alpha=0.3)

        # Gráfica de error absoluto medio (MAE)
        plt.subplot(1, 2, 2)
        plt.plot(self.history.history['mae'], label='Train')
        if 'val_mae' in self.history.history:
            plt.plot(self.history.history['val_mae'], label='Validation')
        plt.title('Mean Absolute Error')
        plt.xlabel('Epoch')
        plt.ylabel('MAE')
        plt.legend()
        plt.grid(True, alpha=0.3)

        plt.tight_layout()

        # Guardar gráfica si se proporciona ruta
        if save_path:
            plt.savefig(save_path)
            print(f"Gráfica guardada en {save_path}")

        plt.show()
