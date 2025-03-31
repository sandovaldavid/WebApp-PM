import os
import sys
import argparse
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from data_processor import DataProcessor
from rnn_model import AdvancedRNNEstimator
from evaluator import ModelEvaluator
import matplotlib.pyplot as plt
import joblib
import json
from datetime import datetime
from django.utils import timezone
import tensorflow as tf
import shutil

def parse_args():
    parser = argparse.ArgumentParser(
        description="Entrenar modelo RNN para estimación de tiempos"
    )
    parser.add_argument(
        "--data-path",
        type=str,
        default="estimacion_tiempos_optimizado.csv",
        help="Ruta al archivo CSV con datos de entrenamiento",
    )
    parser.add_argument(
        "--use-db",
        action="store_true",
        help="Usar categorías de la base de datos en lugar del CSV",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="models",
        help="Directorio para guardar el modelo y resultados",
    )
    parser.add_argument(
        "--epochs", type=int, default=100, help="Número de épocas para entrenar"
    )
    parser.add_argument(
        "--bidirectional", action="store_true", help="Usar capa RNN bidireccional"
    )
    parser.add_argument(
        "--rnn-type",
        type=str,
        default="GRU",
        choices=["GRU", "LSTM"],
        help="Tipo de capa recurrente a usar",
    )
    parser.add_argument(
        "--test-size", type=float, default=0.2, help="Proporción de datos para prueba"
    )
    # Nuevos parámetros para las optimizaciones
    parser.add_argument(
        "--batch-size", type=int, default=32, help="Tamaño de batch para entrenamiento"
    )
    parser.add_argument(
        "--optimizer",
        type=str,
        default="adam",
        choices=["adam", "rmsprop", "nadam", "sgd"],
        help="Optimizador a utilizar",
    )
    parser.add_argument(
        "--learning-rate", type=float, default=0.001, help="Tasa de aprendizaje inicial"
    )
    parser.add_argument(
        "--activation",
        type=str,
        default="relu",
        choices=["relu", "leaky_relu", "prelu", "tanh", "selu"],
        help="Función de activación",
    )
    parser.add_argument(
        "--dropout-rate",
        type=float,
        default=0.3,
        help="Tasa de dropout para regularización",
    )
    parser.add_argument(
        "--use-layer-norm", action="store_true", help="Usar normalización de capas"
    )
    parser.add_argument(
        "--use-residual", action="store_true", help="Usar conexiones residuales"
    )
    parser.add_argument(
        "--tensorboard",
        action="store_true",
        help="Habilitar logs detallados para TensorBoard",
    )
    parser.add_argument(
        "--early-stopping-patience",
        type=int,
        default=30,
        help="Paciencia para early stopping",
    )

    return parser.parse_args()

def main():
    """Función principal para entrenar y evaluar el modelo"""
    
    # Parsear argumentos
    args = parse_args()
    
    # Asegurar que existe el directorio de salida
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Crear directorio para checkpoints
    checkpoint_dir = os.path.join(output_dir, "checkpoints")
    if not os.path.exists(checkpoint_dir):
        os.makedirs(checkpoint_dir)

    # Crear directorio para logs de TensorBoard
    log_dir = os.path.join(output_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    print("\n=== Iniciando proceso de estimación de tiempos con RNN Optimizada ===")
    print(f"Archivo de datos: {args.data_path}")
    print(f"Usando datos de BD: {args.use_db}")
    print(f"Directorio de salida: {output_dir}")
    print(
        f"Tipo de RNN: {args.rnn_type} {'bidireccional' if args.bidirectional else 'unidireccional'}"
    )
    print(f"Optimizador: {args.optimizer}, Learning Rate: {args.learning_rate}")
    print(f"Batch Size: {args.batch_size}, Épocas máximas: {args.epochs}")
    print(f"Activación: {args.activation}, Dropout: {args.dropout_rate}")

    # 1. Cargar y procesar datos
    print("\n[1/5] Cargando y procesando datos...")
    processor = DataProcessor(data_path=args.data_path, use_db=args.use_db)
    data = processor.load_data()
    
    if data is None:
        print("Error: No se pudieron cargar los datos. Verifique la ruta del archivo.")
        return
    
    # 2. Preprocesar los datos
    print("\n[2/5] Preprocesando datos...")
    try:
        X_train, X_val, y_train, y_val, feature_dims = processor.preprocess_data()
        processor.save_preprocessors(output_dir=output_dir)
    except Exception as e:
        print(f"Error al preprocesar datos: {str(e)}")
        return

    # 3. Configurar e inicializar el modelo con parámetros optimizados
    print("\n[3/5] Configurando modelo avanzado...")

    # Configuración avanzada del modelo usando los argumentos
    model_config = {
        "rnn_units": 64,
        "dense_units": [128, 64, 32],
        "dropout_rate": args.dropout_rate,
        "learning_rate": args.learning_rate,
        "min_learning_rate": 1e-6,
        "l2_reg": 0.001,
        "l1_reg": 0.0001,  # Añadir regularización L1 suave
        "use_bidirectional": args.bidirectional,
        "rnn_type": args.rnn_type,
        "activation": args.activation,
        "batch_size": args.batch_size,
        "epochs": args.epochs,
        "optimizer": args.optimizer,
        "use_layer_norm": args.use_layer_norm,
        "use_batch_norm": not args.use_layer_norm,  # Si no usa layer_norm, usar batch_norm
        "rnn_recurrent_dropout": 0.1,  # Añadir dropout recurrente
        "reduce_lr_factor": 0.5,
        "reduce_lr_patience": 10,
        "early_stopping_patience": args.early_stopping_patience,
        "clip_norm": 1.0,
        "use_gradient_clipping": True,
        "use_residual_connections": args.use_residual,
        "weight_decay": 0.0001,
    }

    # Crear estimador con configuración optimizada
    estimator = AdvancedRNNEstimator(model_config)
    estimator.build_model(feature_dims)
    
    # Resumen del modelo
    estimator.model.summary()

    # 4. Entrenar el modelo con optimizaciones
    print("\n[4/5] Entrenando modelo optimizado...")

    # Callbacks personalizados
    callbacks = []

    # Añadir callback para escribir pesos del modelo cada n épocas
    if args.tensorboard:
        # Agregar visualización de pesos y gradientes en TensorBoard
        callbacks.append(
            tf.keras.callbacks.TensorBoard(
                log_dir=os.path.join(
                    log_dir, f'run_{datetime.now().strftime("%Y%m%d-%H%M%S")}'
                ),
                histogram_freq=1,  # Graficar distribuciones de activaciones y pesos
                write_graph=True,
                write_images=True,  # Graficar modelo como imagen
                update_freq="epoch",  # Actualizar métricas cada época
                profile_batch=2,  # Perfilar performance (second batch)
                embeddings_freq=0,  # No calcular embeddings
            )
        )

        # Callback para guardar el mejor modelo
        callbacks.append(
            tf.keras.callbacks.ModelCheckpoint(
                filepath=os.path.join(checkpoint_dir, "best_model.keras"),
                save_best_only=True,
                monitor="val_loss",
                verbose=1,
            )
        )

    # Entrenar con las optimizaciones
    history = estimator.train(
        X_train, y_train, X_val, y_val, feature_dims, callbacks=callbacks
    )

    # División final de datos de prueba
    X_train_full, X_test, y_train_full, y_test = train_test_split(
        np.concatenate([X_train, X_val]),
        np.concatenate([y_train, y_val]),
        test_size=args.test_size,
        random_state=42
    )

    print("[4/5] Guardando datos de validación...")
    validation_data = {
        'X_val': X_val,
        'y_val': y_val,
        'X_test': X_test,
        'y_test': y_test
    }
    validation_path = os.path.join(output_dir, 'validation_data.joblib')
    joblib.dump(validation_data, validation_path)
    
    # También guardar como archivos individuales para compatibilidad
    np.save(os.path.join(output_dir, 'X_val.npy'), X_val)
    np.save(os.path.join(output_dir, 'y_val.npy'), y_val)
    np.save(os.path.join(output_dir, 'X_test.npy'), X_test)
    np.save(os.path.join(output_dir, 'y_test.npy'), y_test)
    
    print(f"Datos de validación guardados en {validation_path}")

    # Si hay un modelo guardado como checkpoint, verificar si es mejor
    best_model_path = os.path.join(checkpoint_dir, "best_model.keras")
    if os.path.exists(best_model_path):
        print("Verificando si el modelo guardado en checkpoints es mejor...")
        # Cargar el mejor modelo
        best_model = tf.keras.models.load_model(best_model_path)

        # Evaluar ambos modelos
        best_metrics = best_model.evaluate(
            estimator.prepare_inputs(X_val, feature_dims), y_val, verbose=0
        )
        current_metrics = estimator.model.evaluate(
            estimator.prepare_inputs(X_val, feature_dims), y_val, verbose=0
        )

        # Si el modelo del checkpoint es mejor, usarlo
        if best_metrics[0] < current_metrics[0]:  # Comparar pérdida
            print(
                f"Usando el mejor modelo guardado (Loss: {best_metrics[0]:.4f} vs {current_metrics[0]:.4f})"
            )
            estimator.model = best_model
        else:
            print(
                f"El modelo actual es mejor (Loss: {current_metrics[0]:.4f} vs {best_metrics[0]:.4f})"
            )

    # Guardar el modelo final
    estimator.save(model_dir=output_dir, name="tiempo_estimator")

    # Plot del entrenamiento con visualización mejorada
    estimator.plot_history(
        save_path=os.path.join(output_dir, "training_history.png"), figsize=(15, 10)
    )

    # 5. Evaluar el modelo
    print("\n[5/5] Evaluando modelo optimizado...")

    # Crear evaluador
    evaluator = ModelEvaluator(estimator, feature_dims, output_dir)
    
    # Evaluar y obtener métricas
    metrics, y_pred = evaluator.evaluate_model(X_test, y_test)
    
    # Guardar métricas con información de entrenamiento inicial
    metrics_history_path = os.path.join(output_dir, "metrics_history.json")

    # Registrar modelo en la base de datos
    from dashboard.models import Modeloestimacionrnn

    timestamp = datetime.now().strftime("%Y%m%d")
    modelo, created = Modeloestimacionrnn.objects.update_or_create(
        nombremodelo="RNN Avanzado Optimizado",
        defaults={
            "descripcionmodelo": f"Modelo RNN optimizado ({args.rnn_type}, {args.optimizer}, LR={args.learning_rate})",
            "versionmodelo": f"2.0.{timestamp}",
            "precision": metrics.get("r2", 0.8),
            "fechacreacion": timezone.now(),
            "fechamodificacion": timezone.now(),
        },
    )

    print(f"Modelo {'creado' if created else 'actualizado'} en la base de datos con ID {modelo.idmodelo}")

    # Obtener información detallada del entrenamiento
    try:
        # Intentar obtener el número de épocas entrenadas
        if hasattr(estimator, 'history') and estimator.history is not None:
            if hasattr(estimator.history, 'params') and 'epochs' in estimator.history.params:
                epochs_trained = estimator.history.params['epochs']
            elif hasattr(estimator.history, 'history') and len(estimator.history.history.get('loss', [])) > 0:
                epochs_trained = len(estimator.history.history['loss'])
            else:
                epochs_trained = args.epochs
        else:
            epochs_trained = args.epochs
    except Exception as e:
        print(f"No se pudo determinar el número de épocas entrenadas: {e}")
        epochs_trained = args.epochs

    # Añadir información detallada sobre este entrenamiento
    dataset_stats = {
        "total_samples": len(X_train) + len(X_val) + len(X_test),
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
        "test_samples": len(X_test),
    }

    # Calcular estadísticas de tiempos de ejecución para reporting
    training_info = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "metrics": metrics,
        "training_type": "optimized",
        "model_config": model_config,
        "dataset_stats": dataset_stats,
        "epochs_trained": epochs_trained,
        "tensorboard_enabled": args.tensorboard,
        "hardware_info": {
            "gpu_available": len(tf.config.list_physical_devices("GPU")) > 0,
            "gpu_devices": [
                device.name for device in tf.config.list_physical_devices("GPU")
            ],
        },
    }

    # Cargar historial existente o crear uno nuevo
    try:
        if os.path.exists(metrics_history_path):
            with open(metrics_history_path, 'r') as f:
                metrics_history = json.load(f)
                if not isinstance(metrics_history, list):
                    # Convertir al nuevo formato
                    if 'evaluations' in metrics_history:
                        metrics_history = metrics_history['evaluations'] 
                    else:
                        metrics_history = []
        else:
            metrics_history = []
    except Exception as e:
        print(f"Error al cargar historial de métricas: {e}")
        metrics_history = []
    
    # Añadir esta evaluación al historial
    metrics_history.append(training_info)

    # Guardar historial actualizado con formato mejorado
    with open(metrics_history_path, "w") as f:
        json.dump(metrics_history, f, indent=4)

    # Visualizar predicciones con gráficos mejorados
    evaluator.plot_predictions(y_test, y_pred)
    
    # Analizar importancia de características
    print("\n[Extra] Analizando importancia de características...")
    # Lista simplificada de nombres de características
    feature_names = (
        ['Complejidad', 'Cantidad_Recursos', 'Carga_R1', 'Exp_R1', 'Carga_R2', 'Exp_R2',
         'Carga_R3', 'Exp_R3', 'Exp_Equipo', 'Claridad_Req', 'Tamaño']
        + [f'Tipo_{i}' for i in range(feature_dims['tipo_tarea'])]
        + [f'Fase_{i}' for i in range(feature_dims['fase'])]
    )

    # Usar el método avanzado de importancia de características de la clase AdvancedRNNEstimator
    try:
        importance_df = estimator.feature_importance(
            X_test, y_test, feature_dims, feature_names
        )
        print("\nImportancia de características:")
        print(importance_df.head(10))

        # Guardar resultados de importancia
        importance_path = os.path.join(output_dir, "feature_importance.csv")
        importance_df.to_csv(importance_path, index=False)
        print(f"Importancia de características guardada en {importance_path}")

        # Graficar importancia
        plt.figure(figsize=(12, 8))
        plt.barh(
            importance_df["feature"].head(15), importance_df["importance_mean"].head(15)
        )
        plt.xlabel("Importancia Media")
        plt.title("Importancia de Características (Top 15)")
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, "feature_importance.png"), dpi=300)
        plt.close()
    except Exception as e:
        print(f"Error al calcular importancia de características: {e}")

    # Evaluación por segmentos (tareas pequeñas, medianas, grandes)
    print("\n[Extra] Evaluando por segmentos de tamaño...")
    segments = {
        'Tareas pequeñas': lambda y: y <= 40,
        'Tareas medianas': lambda y: (y > 40) & (y <= 80),
        'Tareas grandes': lambda y: y > 80
    }
    
    evaluator.segmented_evaluation(X_test, y_test, segments)

    # Añadir información sobre TensorBoard si está habilitado
    if args.tensorboard:
        print(f"\nDatos de TensorBoard disponibles en: {log_dir}")
        print("Para visualizar, ejecute: tensorboard --logdir={}".format(log_dir))

    # Comprimir modelos y resultados para facilitar distribución
    try:
        archive_name = f"modelo_rnn_optimizado_{timestamp}"
        shutil.make_archive(os.path.join(output_dir, archive_name), "zip", output_dir)
        print(
            f"\nSe ha creado un archivo ZIP con el modelo y resultados: {archive_name}.zip"
        )
    except Exception as e:
        print(f"Error al crear archivo ZIP: {e}")

    print("\n=== Proceso completado exitosamente ===")
    print(f"Todos los archivos han sido guardados en: {output_dir}")
    print("\nPara usar el modelo en predicciones, importe las clases necesarias y cargue el modelo:")
    print("  from rnn_model import AdvancedRNNEstimator")
    print("  model = AdvancedRNNEstimator.load('models', 'tiempo_estimator')")
    
    return estimator, processor, evaluator

if __name__ == "__main__":
    main()
