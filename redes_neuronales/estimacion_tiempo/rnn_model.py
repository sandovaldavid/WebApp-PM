import os
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.layers import (
    Dense, LSTM, GRU, Input, Dropout, BatchNormalization, 
    Concatenate, Embedding, Flatten, Bidirectional, TimeDistributed,
    LayerNormalization, PReLU, LeakyReLU
)
from tensorflow.keras.callbacks import ModelCheckpoint, EarlyStopping, ReduceLROnPlateau, TensorBoard
from tensorflow.keras.optimizers import Adam, RMSprop, Nadam, SGD
from tensorflow.keras.regularizers import l2, l1, l1_l2
import matplotlib.pyplot as plt
import joblib
import json
import time
from datetime import datetime

class AdvancedRNNEstimator:
    """Modelo de red neuronal recurrente para estimación de tiempos avanzada"""
    
    def __init__(self, config=None):
        """Inicializa el modelo con configuración personalizable
        
        Args:
            config: Diccionario de parámetros de configuración
        """
        # Configuración por defecto mejorada
        self.default_config = {
            'rnn_units': 64,
            'dense_units': [128, 64, 32],
            'dropout_rate': 0.3,
            'learning_rate': 0.001,
            'min_learning_rate': 1e-6,
            'l2_reg': 0.001,
            'l1_reg': 0.0,
            'use_bidirectional': True,
            'rnn_type': 'GRU',  # 'LSTM' o 'GRU'
            'activation': 'relu',  # 'relu', 'leaky_relu', 'prelu', 'tanh', 'selu'
            'batch_size': 32,
            'epochs': 100,
            'optimizer': 'adam',  # 'adam', 'rmsprop', 'nadam', 'sgd'
            'use_layer_norm': False,  # Usar normalización de capas
            'use_batch_norm': True,   # Usar normalización de batch
            'rnn_recurrent_dropout': 0.0,  # Dropout recurrente en RNN
            'reduce_lr_factor': 0.5,  # Factor para ReduceLROnPlateau
            'reduce_lr_patience': 10, # Paciencia para ReduceLROnPlateau
            'early_stopping_patience': 30,  # Paciencia para EarlyStopping
            'clip_norm': 1.0,  # Valor para gradient clipping
            'use_gradient_clipping': True,  # Activar gradient clipping
            'use_residual_connections': False,  # Usar conexiones residuales
            'weight_decay': 0.0001,  # Decaimiento de pesos (especialmente para AdamW)
        }
        
        # Usar configuración proporcionada o la predeterminada
        self.config = config if config is not None else self.default_config
        self.model = None
        self.history = None
        self.tb_log_dir = None
        
    def _get_activation(self, activation_name):
        """Obtiene la función de activación según nombre
        
        Args:
            activation_name: Nombre de la activación
            
        Returns:
            Función de activación o nombre para capas keras
        """
        if activation_name == 'leaky_relu':
            return LeakyReLU(alpha=0.1)
        elif activation_name == 'prelu':
            return PReLU()
        else:
            return activation_name
    
    def _get_optimizer(self, optimizer_name):
        """Obtiene el optimizador según nombre y configuración
        
        Args:
            optimizer_name: Nombre del optimizador
            
        Returns:
            Optimizador configurado
        """
        lr = self.config['learning_rate']
        
        if self.config['use_gradient_clipping']:
            clipnorm = self.config['clip_norm']
        else:
            clipnorm = None
            
        if optimizer_name == 'adam':
            return Adam(learning_rate=lr, clipnorm=clipnorm, weight_decay=self.config['weight_decay'])
        elif optimizer_name == 'rmsprop':
            return RMSprop(learning_rate=lr, clipnorm=clipnorm)
        elif optimizer_name == 'nadam':
            return Nadam(learning_rate=lr, clipnorm=clipnorm)
        elif optimizer_name == 'sgd':
            return SGD(learning_rate=lr, momentum=0.9, nesterov=True, clipnorm=clipnorm)
        else:
            print(f"Optimizador '{optimizer_name}' no reconocido. Usando Adam predeterminado.")
            return Adam(learning_rate=lr, clipnorm=clipnorm)
    
    def build_model(self, feature_dims):
        """Construye el modelo RNN para estimación de tiempo
        
        Args:
            feature_dims: Diccionario con dimensiones de cada tipo de feature
        """
        # Verificar si feature_dims es válido
        if not isinstance(feature_dims, dict) or not all(k in feature_dims for k in ['numeric', 'tipo_tarea', 'fase']):
            raise ValueError("feature_dims debe ser un diccionario con claves 'numeric', 'tipo_tarea', 'fase'")
        
        # 1. Entrada para características numéricas
        numeric_input = Input(shape=(feature_dims['numeric'],), name='numeric_input')
        
        # 2. Reshape para entrada recurrente
        reshaped_numeric = tf.expand_dims(numeric_input, axis=1, name='expand_dims')
        
        # 3. Capas recurrentes - GRU o LSTM según configuración
        if self.config['rnn_type'] == 'LSTM':
            rnn_layer = LSTM
        else:
            rnn_layer = GRU
            
        # Configurar regularización para RNN
        kwargs = {
            'kernel_regularizer': l1_l2(l1=self.config['l1_reg'], l2=self.config['l2_reg']),
            'recurrent_regularizer': l2(self.config['l2_reg']),
            'recurrent_dropout': self.config['rnn_recurrent_dropout'],
        }
        
        if self.config['use_bidirectional']:
            rnn = Bidirectional(
                rnn_layer(
                    self.config['rnn_units'], 
                    return_sequences=False,
                    name='rnn_layer',
                    **kwargs
                )
            )(reshaped_numeric)
        else:
            rnn = rnn_layer(
                self.config['rnn_units'], 
                return_sequences=False,
                name='rnn_layer',
                **kwargs
            )(reshaped_numeric)
            
        # Normalización después de RNN si está configurado
        if self.config['use_layer_norm']:
            rnn = LayerNormalization(name='rnn_layer_norm')(rnn)
        
        # 4. Entrada y procesamiento para tipo de tarea (one-hot)
        tipo_tarea_input = Input(shape=(feature_dims['tipo_tarea'],), name='tipo_tarea_input')
        tipo_tarea_dense = Dense(
            32, 
            activation=self._get_activation(self.config['activation']),
            kernel_regularizer=l1_l2(l1=self.config['l1_reg'], l2=self.config['l2_reg']),
            name='tipo_tarea_dense'
        )(tipo_tarea_input)
        
        # 5. Entrada y procesamiento para fase (one-hot)
        fase_input = Input(shape=(feature_dims['fase'],), name='fase_input')
        fase_dense = Dense(
            32, 
            activation=self._get_activation(self.config['activation']),
            kernel_regularizer=l1_l2(l1=self.config['l1_reg'], l2=self.config['l2_reg']),
            name='fase_dense'
        )(fase_input)
        
        # 6. Concatenar todas las características
        combined = Concatenate(name='concatenate_features')([rnn, tipo_tarea_dense, fase_dense])
        
        # 7. Capas densas con regularización y normalización mejoradas
        x = combined
        prev_layer = combined  # Para conexiones residuales
        
        for i, units in enumerate(self.config['dense_units']):
            # Capa densa con regularización
            dense = Dense(
                units, 
                activation=self._get_activation(self.config['activation']),
                kernel_regularizer=l1_l2(l1=self.config['l1_reg'], l2=self.config['l2_reg']),
                name=f'dense_{i}'
            )(x)
            
            # Conexión residual si está configurada y las dimensiones coinciden
            if self.config['use_residual_connections'] and i > 0 and prev_layer.shape[-1] == units:
                dense = tf.keras.layers.add([dense, prev_layer])
                
            # Normalización (batch o layer)
            if self.config['use_batch_norm']:
                dense = BatchNormalization(name=f'batch_norm_{i}')(dense)
            elif self.config['use_layer_norm']:
                dense = LayerNormalization(name=f'layer_norm_{i}')(dense)
                
            # Dropout
            x = Dropout(self.config['dropout_rate'], name=f'dropout_{i}')(dense)
            prev_layer = x
        
        # 8. Capa de salida para estimación de tiempo
        output = Dense(1, name='output')(x)
        
        # 9. Construir y compilar el modelo
        self.model = Model(
            inputs=[numeric_input, tipo_tarea_input, fase_input],
            outputs=output
        )
        
        # Seleccionar optimizador según configuración
        optimizer = self._get_optimizer(self.config['optimizer'])
        
        self.model.compile(
            optimizer=optimizer,
            loss='mse',
            metrics=['mae', 'mape']
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
        if X.shape[1] != (feature_dims['numeric'] + feature_dims['tipo_tarea'] + feature_dims['fase']):
            raise ValueError(f"Dimensiones de X no coinciden con feature_dims: {X.shape[1]} vs {sum(feature_dims.values())}")
            
        # Separar características por tipo
        numeric_data = X[:, :feature_dims['numeric']]
        tipo_tarea_data = X[:, feature_dims['numeric']:feature_dims['numeric']+feature_dims['tipo_tarea']]
        fase_data = X[:, feature_dims['numeric']+feature_dims['tipo_tarea']:]
        
        return [numeric_data, tipo_tarea_data, fase_data]
    
    def _create_tf_dataset(self, X, y, feature_dims, batch_size=None, shuffle=True, cache=True):
        """Crea un tf.data.Dataset optimizado para entrenamiento
        
        Args:
            X: Datos de entrada
            y: Etiquetas
            feature_dims: Dimensiones de features
            batch_size: Tamaño de batch
            shuffle: Si mezclar los datos
            cache: Si cachear los datos
            
        Returns:
            tf.data.Dataset configurado
        """
        if batch_size is None:
            batch_size = self.config['batch_size']
            
        # Preparar inputs
        inputs = self.prepare_inputs(X, feature_dims)
        
        # Crear dataset
        dataset = tf.data.Dataset.from_tensor_slices((tuple(inputs), y))
        
        # Cachear datos (mejora rendimiento si los datos caben en memoria)
        if cache:
            dataset = dataset.cache()
            
        # Mezclar datos (importante para entrenamiento)
        if shuffle:
            buffer_size = min(len(X), 10000)  # Limitar buffer si hay muchos datos
            dataset = dataset.shuffle(buffer_size=buffer_size, reshuffle_each_iteration=True)
            
        # Configurar batches
        dataset = dataset.batch(batch_size)
        
        # Prefetch (carga anticipada para siguiente batch)
        dataset = dataset.prefetch(tf.data.AUTOTUNE)
        
        return dataset
    
    def train(self, X_train, y_train, X_val=None, y_val=None, feature_dims=None, callbacks=None):
        """Entrena el modelo con los datos proporcionados usando tf.data.Dataset para optimización
        
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
        
        # Crear dataset de entrenamiento optimizado
        train_dataset = self._create_tf_dataset(
            X_train, y_train, feature_dims, 
            batch_size=self.config['batch_size'], 
            shuffle=True, cache=True
        )
        
        # Configurar los datos de validación si se proporcionan
        validation_data = None
        if X_val is not None and y_val is not None:
            validation_data = self._create_tf_dataset(
                X_val, y_val, feature_dims, 
                batch_size=self.config['batch_size'], 
                shuffle=False, cache=True
            )
        
        # Configurar directorio para TensorBoard
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        self.tb_log_dir = f"./logs/fit/{timestamp}"
        
        # Definir callbacks avanzados
        default_callbacks = [
            # Early stopping mejorado
            EarlyStopping(
                monitor='val_loss' if validation_data else 'loss',
                patience=self.config['early_stopping_patience'],
                restore_best_weights=True,
                verbose=1
            ),
            # Learning rate scheduler
            ReduceLROnPlateau(
                monitor='val_loss' if validation_data else 'loss',
                factor=self.config['reduce_lr_factor'],
                patience=self.config['reduce_lr_patience'],
                min_lr=self.config['min_learning_rate'],
                verbose=1
            ),
           # TensorBoard
            TensorBoard(log_dir=self.tb_log_dir, histogram_freq=1, write_graph=True,
                    write_images=True, update_freq='epoch', profile_batch='500,520'),
            # Checkpoint para guardar mejor modelo
            ModelCheckpoint(
                filepath='./checkpoints/model_{epoch:02d}_{val_loss:.4f}.keras' 
                if validation_data else './checkpoints/model_{epoch:02d}_{loss:.4f}.keras',
                save_best_only=True,
                monitor='val_loss' if validation_data else 'loss',
                verbose=1
            )
        ]
       
        # Combinar con callbacks proporcionados
        all_callbacks = default_callbacks.copy()
        if callbacks:
            all_callbacks.extend(callbacks)

        print(f"Iniciando entrenamiento con {self.config['batch_size']} muestras por batch")
        print(f"Optimizador: {self.config['optimizer']}, Learning rate: {self.config['learning_rate']}")
        print(f"TensorBoard: {self.tb_log_dir}")
        
        # Registrar tiempo de inicio
        start_time = time.time()
        
        # Entrenar modelo con datasets optimizados
        history = self.model.fit(
            train_dataset,
            epochs=self.config['epochs'],
            validation_data=validation_data,
            verbose=1,
            callbacks=all_callbacks
        )
        
        # Calcular tiempo de entrenamiento
        training_time = time.time() - start_time
        print(f"Entrenamiento completado en {training_time:.2f} segundos")
        
        # Guardar historia para análisis posterior
        self.history = history
        
        # Registrar métricas finales
        if validation_data:
            final_val_loss = history.history['val_loss'][-1]
            print(f"Pérdida final en validación: {final_val_loss:.4f}")
        
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
            raise ValueError("El modelo no está entrenado. Ejecute build_model y train primero.")
            
        # Preparar dataset para predicción
        batch_size = min(len(X), self.config['batch_size'] * 2)  # Batch más grande para inferencia
        inputs = self.prepare_inputs(X, feature_dims)
        
        # Realizar predicción
        predictions = self.model.predict(inputs, batch_size=batch_size)
        
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
            raise ValueError("El modelo no está entrenado. Ejecute build_model y train primero.")
            
        # Crear dataset optimizado para evaluación
        test_dataset = self._create_tf_dataset(X, y, feature_dims, shuffle=False)
            
        # Evaluar el modelo
        metrics = self.model.evaluate(test_dataset, verbose=1)
        
        # Crear diccionario de métricas
        metrics_dict = {
            'loss': metrics[0],
            'mae': metrics[1],
            'mape': metrics[2]
        }
        
        # Realizar predicciones para análisis adicional
        y_pred = self.predict(X, feature_dims)
        
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
        
        # Guardar historial de entrenamiento si existe
        if self.history is not None:
            history_path = os.path.join(model_dir, f'{name}_history.json')
            history_dict = {
                'loss': [float(val) for val in self.history.history.get('loss', [])],
                'mae': [float(val) for val in self.history.history.get('mae', [])],
                'mape': [float(val) for val in self.history.history.get('mape', [])]
            }
            
            # Añadir métricas de validación si existen
            if 'val_loss' in self.history.history:
                history_dict['val_loss'] = [float(val) for val in self.history.history['val_loss']]
                history_dict['val_mae'] = [float(val) for val in self.history.history['val_mae']]
                history_dict['val_mape'] = [float(val) for val in self.history.history['val_mape']]
                
            # Guardar como JSON
            with open(history_path, 'w') as f:
                json.dump(history_dict, f)
                
            print(f"Historial de entrenamiento guardado en {history_path}")
        
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
            raise FileNotFoundError(f"No se encontraron los archivos del modelo en {model_dir}")
        
        # Cargar configuración
        config = joblib.load(config_path)
        
        # Crear instancia
        instance = cls(config)
        
        # Cargar modelo
        instance.model = load_model(model_path)
        
        # Cargar historial si existe
        history_path = os.path.join(model_dir, f'{name}_history.json')
        if os.path.exists(history_path):
            try:
                with open(history_path, 'r') as f:
                    history_dict = json.load(f)
                    
                # Crear objeto History falso con los datos cargados
                history = type('History', (), {'history': history_dict})
                instance.history = history
            except Exception as e:
                print(f"Error al cargar historial: {e}")
        
        return instance
    
    def plot_history(self, save_path=None, figsize=(15, 10)):
        """Grafica la historia del entrenamiento con métricas adicionales
        
        Args:
            save_path: Ruta donde guardar la gráfica (opcional)
            figsize: Tamaño de la figura
        """
        if self.history is None:
            raise ValueError("No hay historia de entrenamiento. Ejecute train primero.")
            
        # Crear figura
        plt.figure(figsize=figsize)
        
        # 1. Gráfica de pérdida
        plt.subplot(2, 2, 1)
        plt.plot(self.history.history['loss'], label='Train', linewidth=2)
        if 'val_loss' in self.history.history:
            plt.plot(self.history.history['val_loss'], label='Validation', linewidth=2)
        plt.title('Loss (MSE)', fontsize=14)
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('Loss', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # 2. Gráfica de error absoluto medio (MAE)
        plt.subplot(2, 2, 2)
        plt.plot(self.history.history['mae'], label='Train', linewidth=2)
        if 'val_mae' in self.history.history:
            plt.plot(self.history.history['val_mae'], label='Validation', linewidth=2)
        plt.title('Mean Absolute Error', fontsize=14)
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('MAE', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # 3. Gráfica de MAPE
        plt.subplot(2, 2, 3)
        plt.plot(self.history.history['mape'], label='Train', linewidth=2)
        if 'val_mape' in self.history.history:
            plt.plot(self.history.history['val_mape'], label='Validation', linewidth=2)
        plt.title('Mean Absolute Percentage Error', fontsize=14)
        plt.xlabel('Epoch', fontsize=12)
        plt.ylabel('MAPE (%)', fontsize=12)
        plt.legend(fontsize=12)
        plt.grid(True, alpha=0.3)
        
        # 4. Tasa de aprendizaje (si está disponible)
        if 'lr' in self.history.history:
            plt.subplot(2, 2, 4)
            plt.plot(self.history.history['lr'], linewidth=2)
            plt.title('Learning Rate', fontsize=14)
            plt.xlabel('Epoch', fontsize=12)
            plt.ylabel('Learning Rate', fontsize=12)
            plt.yscale('log')  # Escala logarítmica para LR
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Guardar gráfica si se proporciona ruta
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"Gráfica guardada en {save_path}")
            
        plt.show()
        
    def feature_importance(self, X, y, feature_dims, feature_names=None, n_samples=1000):
        """Calcula la importancia de las características usando permutación
        
        Args:
            X: Datos de test
            y: Valores reales
            feature_dims: Dimensiones de features
            feature_names: Lista de nombres de características
            n_samples: Número de muestras para el análisis
            
        Returns:
            DataFrame con importancia de características
        """
        import pandas as pd
        from sklearn.inspection import permutation_importance
        
        # Limitar número de muestras para eficiencia
        if len(X) > n_samples:
            idx = np.random.choice(len(X), n_samples, replace=False)
            X_sample = X[idx]
            y_sample = y[idx]
        else:
            X_sample = X
            y_sample = y
            
        # Crear función de predicción para scikit-learn
        def predict_func(X):
            return self.predict(X, feature_dims)
            
        # Calcular importancia por permutación
        perm_importance = permutation_importance(
            predict_func, X_sample, y_sample,
            n_repeats=10, random_state=42, n_jobs=-1
        )
        
        # Crear DataFrame con resultados
        if feature_names is None:
            feature_names = [f'feature_{i}' for i in range(X.shape[1])]
            
        importance_df = pd.DataFrame({
            'feature': feature_names,
            'importance_mean': perm_importance.importances_mean,
            'importance_std': perm_importance.importances_std
        }).sort_values('importance_mean', ascending=False)
        
        return importance_df
