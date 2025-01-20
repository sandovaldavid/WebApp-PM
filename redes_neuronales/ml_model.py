# ml_model.py
from tensorflow.keras.models import Model
from tensorflow.keras.layers import (
    Dense,
    Embedding,
    LSTM,
    Input,
    Concatenate,
    Dropout,
    BatchNormalization,
    Add,
    Bidirectional,
    Multiply,
    Softmax
)
from tensorflow.keras.regularizers import l1_l2
from tensorflow.keras.losses import MeanSquaredError
from tensorflow.keras.preprocessing.text import Tokenizer
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint, ReduceLROnPlateau
import tensorflow as tf
from tensorflow.keras.layers import Reshape
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import KFold
import numpy as np

class EstimacionModel:
    """Modelo para estimar tiempos de proyectos usando RNN"""

    def __init__(self, config):
        """
        Inicializa el modelo con la configuración dada

        Args:
            config (dict): Diccionario con parámetros de configuración
        """
        self.config = config
        self.model = self._build_model()

    def normalize_data(self, X_numeric):
        """
        Normaliza las características numéricas usando StandardScaler
        
        Args:
            X_numeric: Array con features numéricas [complejidad, prioridad, tareas_requerimiento]
        Returns:
            X_normalized: Array normalizado
            scaler: Objeto StandardScaler entrenado
        """
        self.scaler = StandardScaler()
        X_normalized = self.scaler.fit_transform(X_numeric)
        return X_normalized, self.scaler

    def _build_numeric_branch(self):
        """Construye una rama más compleja para características numéricas con regularización"""
        numeric_input = Input(shape=(2,), name="numeric_input")
        req_input = Input(shape=(4,), name="req_input")

        # Rama numérica con regularización L1/L2
        x1 = Dense(
            256,
            activation="relu",
            kernel_regularizer=tf.keras.regularizers.l1_l2(l1=1e-5, l2=1e-4),
            name="numeric_dense_1",
        )(numeric_input)
        x1 = BatchNormalization(momentum=0.9, name="numeric_batch_norm_1")(x1)
        x1 = Dropout(0.4)(x1)

        x1 = Dense(
            128,
            activation="relu",
            kernel_regularizer=tf.keras.regularizers.l1_l2(l1=1e-5, l2=1e-4),
            name="numeric_dense_2",
        )(x1)
        x1 = BatchNormalization(momentum=0.9, name="numeric_batch_norm_2")(x1)
        x1 = Dropout(0.3)(x1)

        # Rama de requerimientos con regularización
        x2 = Dense(
            128,
            activation="relu",
            kernel_regularizer=tf.keras.regularizers.l1_l2(l1=1e-5, l2=1e-4),
            name="req_dense_1",
        )(req_input)
        x2 = BatchNormalization(momentum=0.9, name="req_batch_norm_1")(x2)
        x2 = Dropout(0.4)(x2)

        x2 = Dense(
            64,
            activation="relu",
            kernel_regularizer=tf.keras.regularizers.l1_l2(l1=1e-5, l2=1e-4),
            name="req_dense_2",
        )(x2)
        x2 = BatchNormalization(momentum=0.9, name="req_batch_norm_2")(x2)
        x2 = Dropout(0.3)(x2)

        # Concatenación con nombre único
        x = Concatenate(name="concatenate_numeric")([x1, x2])
        return [numeric_input, req_input], x

    def _build_task_type_branch(self):
        """Construye una rama más compleja para procesar tipos de tareas"""
        task_input = Input(shape=(1,), name="task_input")

        # Embedding más grande
        x = Embedding(self.config["vocab_size"], 128, name="task_embedding")(task_input)

        # Reshape para LSTM
        x = Reshape((1, 128), name="reshape")(x)

        # LSTM bidireccional y más profundo
        lstm_out = x
        lstm_units = [128, 64, 32]

        for i, units in enumerate(lstm_units):
            # Capa LSTM bidireccional
            lstm_layer = Bidirectional(
                LSTM(
                    units,
                    return_sequences=True if i < len(lstm_units) - 1 else False,
                    recurrent_dropout=0.2,
                    name=f"lstm_{i+1}",
                )
            )(lstm_out)

            # Normalización y dropout
            x = BatchNormalization(name=f"lstm_batch_norm_{i+1}")(lstm_layer)
            x = Dropout(0.3)(x)

            # Actualizar entrada para siguiente capa
            lstm_out = x

        # Capas densas adicionales
        x = Dense(32, activation="relu", name="task_dense_1")(lstm_out)
        x = BatchNormalization(name="task_batch_norm_1")(x)
        x = Dropout(0.2)(x)

        x = Dense(16, activation="relu", name="task_dense_2")(x)
        x = BatchNormalization(name="task_batch_norm_2")(x)
        x = Dropout(0.2)(x)

        return task_input, x

    def _build_model(self):
        """Construye el modelo completo mejorado"""
        [numeric_input, req_input], x1 = self._build_numeric_branch()
        task_input, x2 = self._build_task_type_branch()

        # Combinar features
        combined = Concatenate(name="concatenate_features")([x1, x2])

        # Red más profunda para el procesamiento final
        x = Dense(256, activation="relu", name="combined_dense_1")(combined)
        x = BatchNormalization(name="combined_batch_norm_1")(x)
        x = Dropout(0.4)(x)

        x = Dense(128, activation="relu", name="combined_dense_2")(x)
        x = BatchNormalization(name="combined_batch_norm_2")(x)
        x = Dropout(0.3)(x)

        x = Dense(64, activation="relu", name="combined_dense_3")(x)
        x = BatchNormalization(name="combined_batch_norm_3")(x)
        x = Dropout(0.2)(x)

        output = Dense(1, activation="linear", name="output")(x)

        model = Model(inputs=[numeric_input, req_input, task_input], outputs=output)
        model.compile(optimizer="adam", loss="mse", metrics=["mae", "mse"])

        return model

    def cross_validate_model(self, X_num, X_task, X_req, y, n_splits=5):
        """
        Implementa validación cruzada

        Args:
            X_num: Features numéricas
            X_task: Tipos de tarea codificados
            X_req: Información del requerimiento
            y: Valores objetivo (duracion)
            n_splits: Número de divisiones para CV
        """
        kf = KFold(n_splits=n_splits, shuffle=True, random_state=42)
        scores = []

        for train_idx, val_idx in kf.split(X_num):
            # Dividir datos
            X_num_train, X_num_val = X_num[train_idx], X_num[val_idx]
            X_task_train, X_task_val = X_task[train_idx], X_task[val_idx]
            X_req_train, X_req_val = X_req[train_idx], X_req[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]

            # Normalizar datos numéricos
            X_num_train_norm, scaler = self.normalize_data(X_num_train)
            X_num_val_norm = scaler.transform(X_num_val)

            # Entrenar modelo
            history = self.train(
                [X_num_train_norm, X_req_train, X_task_train],
                y_train,
                validation_data=([X_num_val_norm, X_req_val, X_task_val], y_val),
                epochs=100,
            )

            val_score = min(history.history["val_loss"])
            scores.append(val_score)

        return np.mean(scores), np.std(scores)

    def analyze_feature_importance(self, X_num, X_task, X_req, y, feature_names=None):
        """Analiza la importancia de las características"""
        if feature_names is None:
            feature_names = ["Complejidad", "Prioridad", "Info Requerimiento"]

        base_prediction = self.model.predict([X_num, X_req, X_task])
        importance_scores = []

        # Analizar features numéricas
        for i in range(X_num.shape[1]):
            X_modified = X_num.copy()
            X_modified[:, i] = np.mean(X_num[:, i])
            new_prediction = self.model.predict([X_modified, X_req, X_task])
            importance = np.mean(np.abs(base_prediction - new_prediction))
            importance_scores.append((feature_names[i], importance))

        # Analizar importancia de info del requerimiento
        X_req_modified = np.full_like(X_req, np.mean(X_req))
        req_prediction = self.model.predict([X_num, X_req_modified, X_task])
        req_importance = np.mean(np.abs(base_prediction - req_prediction))
        importance_scores.append(("Info Requerimiento", req_importance))

        # Analizar importancia del tipo de tarea
        X_task_modified = np.full_like(X_task, np.mean(X_task))
        task_prediction = self.model.predict([X_num, X_req, X_task_modified])
        task_importance = np.mean(np.abs(base_prediction - task_prediction))
        importance_scores.append(("Tipo de Tarea", task_importance))

        return sorted(importance_scores, key=lambda x: x[1], reverse=True)

    def predict_individual_task(self, X_num, X_task, X_req):
        """Predice considerando el contexto del requerimiento"""
        prediction = self.model.predict([X_num, X_req, X_task])
        return {
            'tiempo_estimado': prediction[0][0],
            'complejidad': X_num[0][0],
            'prioridad': X_num[0][1],
            'tipo_tarea': X_task[0],
            'contexto_req': X_req[0][0]
        }

    def get_callbacks(self):
        return [
            EarlyStopping(
                monitor='val_loss',
                patience=20,
                restore_best_weights=True,
                min_delta=1e-4
            ),
            ReduceLROnPlateau(
                monitor='val_loss',
                factor=0.1,
                patience=10,
                min_lr=1e-6
            ),
            ModelCheckpoint(
                'models/best_model.keras',
                monitor='val_loss',
                save_best_only=True,
                save_weights_only=False
            ),
            tf.keras.callbacks.TensorBoard(
                log_dir='./logs',
                histogram_freq=1
            )
        ]

    def train(self, inputs, targets, validation_data=None, epochs=100):
        """Train model with validation"""
        callbacks = [
            tf.keras.callbacks.EarlyStopping(
                monitor="loss" if validation_data is None else "val_loss",
                patience=10,
                restore_best_weights=True,
            ),
            tf.keras.callbacks.ModelCheckpoint(
                "models/best_model.keras",
                monitor="loss" if validation_data is None else "val_loss",
                save_best_only=True,
            ),
        ]

        return self.model.fit(
            inputs,
            targets,
            validation_data=validation_data,
            epochs=epochs,
            callbacks=callbacks,
            verbose=1,
        )

    def predict(self, X_num, X_task, X_req):
        """Realiza predicciones"""
        return self.model.predict([X_num, X_req, X_task])

    def attention_layer(self, inputs):
        attention_weights = Dense(1, activation="tanh")(inputs)
        attention_weights = Softmax(axis=1)(attention_weights)
        return Multiply()([inputs, attention_weights])

    def _build_temporal_branch(self):
        temporal_input = Input(shape=(7,))  # Características temporales
        x = Dense(64, activation="relu")(temporal_input)
        x = BatchNormalization()(x)
        x = Dropout(0.3)(x)
        return temporal_input, x

    def compile_model(self):
        optimizer = tf.keras.optimizers.Adam(
            learning_rate=self.config.get("learning_rate", 0.001),
            beta_1=0.9,
            beta_2=0.999,
            epsilon=1e-07,
            amsgrad=True,
        )

        loss = tf.keras.losses.Huber(delta=1.0)  # Más robusto que MSE

        self.model.compile(
            optimizer=optimizer,
            loss=loss,
            metrics=["mae", "mse", tf.keras.metrics.RootMeanSquaredError()],
        )

    def augment_data(self, X_num, X_req, y):
        """Genera variaciones sintéticas de los datos"""
        noise_factor = 0.05
        num_samples = len(X_num)

        # Añadir ruido gaussiano
        X_num_noisy = X_num + np.random.normal(0, noise_factor, X_num.shape)
        X_req_noisy = X_req + np.random.normal(0, noise_factor, X_req.shape)

        # Combinar datos originales y aumentados
        X_num_aug = np.concatenate([X_num, X_num_noisy])
        X_req_aug = np.concatenate([X_req, X_req_noisy])
        y_aug = np.concatenate([y, y])

        return X_num_aug, X_req_aug, y_aug


class DataPreprocessor:
    """Clase para preprocesamiento de datos"""

    def __init__(self):
        self.tokenizer = Tokenizer()

    def fit_tokenizer(self, task_types):
        """Entrena el tokenizer con tipos de tarea"""
        self.tokenizer.fit_on_texts(task_types)

    def encode_task_types(self, task_types):
        """Codifica tipos de tarea"""
        return self.tokenizer.texts_to_sequences(task_types)

    def decode_task_types(self, encoded_tasks):
        """Decodifica tipos de tarea"""
        return self.tokenizer.sequences_to_texts(encoded_tasks)
