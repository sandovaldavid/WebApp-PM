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
# from datetime import datetime
from django.utils import timezone

def parse_args():
    parser = argparse.ArgumentParser(description='Entrenar modelo RNN para estimación de tiempos')
    parser.add_argument('--data-path', type=str, 
                        default='estimacion_tiempos_optimizado.csv',
                        help='Ruta al archivo CSV con datos de entrenamiento')
    parser.add_argument('--use-db', action='store_true',
                        help='Usar categorías de la base de datos en lugar del CSV')
    parser.add_argument('--output-dir', type=str, default='models',
                        help='Directorio para guardar el modelo y resultados')
    parser.add_argument('--epochs', type=int, default=100,
                        help='Número de épocas para entrenar')
    parser.add_argument('--bidirectional', action='store_true',
                        help='Usar capa RNN bidireccional')
    parser.add_argument('--rnn-type', type=str, default='GRU', choices=['GRU', 'LSTM'],
                        help='Tipo de capa recurrente a usar')
    parser.add_argument('--test-size', type=float, default=0.2,
                        help='Proporción de datos para prueba')
                        
    return parser.parse_args()

def main():
    """Función principal para entrenar y evaluar el modelo"""
    
    # Parsear argumentos
    args = parse_args()
    
    # Asegurar que existe el directorio de salida
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    print("\n=== Iniciando proceso de estimación de tiempos con RNN ===")
    print(f"Archivo de datos: {args.data_path}")
    print(f"Usando datos de BD: {args.use_db}")
    print(f"Directorio de salida: {output_dir}")
    print(f"Tipo de RNN: {args.rnn_type} {'bidireccional' if args.bidirectional else 'unidireccional'}")
    
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
    
    # 3. Configurar e inicializar el modelo
    print("\n[3/5] Configurando modelo...")
    model_config = {
        'rnn_units': 64,
        'dense_units': [128, 64, 32],
        'dropout_rate': 0.3,
        'learning_rate': 0.001,
        'l2_reg': 0.001,
        'use_bidirectional': args.bidirectional,
        'rnn_type': args.rnn_type,
        'activation': 'relu',
        'batch_size': 32,
        'epochs': args.epochs
    }
    
    estimator = AdvancedRNNEstimator(model_config)
    estimator.build_model(feature_dims)
    
    # Resumen del modelo
    estimator.model.summary()
    
    # 4. Entrenar el modelo
    print("\n[4/5] Entrenando modelo...")
    history = estimator.train(X_train, y_train, X_val, y_val, feature_dims)

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
    
    # Guardar el modelo
    estimator.save(model_dir=output_dir, name='tiempo_estimator')
    
    # Plot del entrenamiento
    estimator.plot_history(save_path=os.path.join(output_dir, 'training_history.png'))
    
    # 5. Evaluar el modelo
    print("\n[5/5] Evaluando modelo...")
    
    # Crear evaluador
    evaluator = ModelEvaluator(estimator, feature_dims, output_dir)
    
    # Evaluar y obtener métricas
    metrics, y_pred = evaluator.evaluate_model(X_test, y_test)
    
    # Guardar métricas con información de entrenamiento inicial
    metrics_history_path = os.path.join(output_dir, 'metrics_history.json')
    

    # Registrar modelo en la base de datos
    from dashboard.models import Modeloestimacionrnn
    from datetime import datetime

    timestamp = datetime.now().strftime("%Y%m%d")
    modelo, created = Modeloestimacionrnn.objects.update_or_create(
        nombremodelo='RNN Avanzado',
        defaults={
            'descripcionmodelo': 'Modelo de red neuronal recurrente para estimación de tiempo (entrenamiento inicial)',
            'versionmodelo': f"1.0.{timestamp}",
            'precision': metrics.get('r2', 0.8),
            'fechacreacion': timezone.now(),
            'fechamodificacion': timezone.now()
        }
    )

    print(f"Modelo {'creado' if created else 'actualizado'} en la base de datos con ID {modelo.idmodelo}")

    # Corregir el acceso al historial de entrenamiento
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
    
    # Añadir información extra sobre este entrenamiento
    dataset_stats = {
        "total_samples": len(X_train) + len(X_val) + len(X_test),
        "training_samples": len(X_train),
        "validation_samples": len(X_val),
        "test_samples": len(X_test),
    }
    
    training_info = {
        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'metrics': metrics,
        'training_type': 'initial',
        'model_config': model_config,
        'dataset_stats': dataset_stats,
        'epochs_trained': epochs_trained
    }
    
    # Cargar historial existente o crear uno nuevo (formato compatible con evaluate_metrics.py)
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
    
    # Guardar historial actualizado
    with open(metrics_history_path, 'w') as f:
        json.dump(metrics_history, f, indent=4)
    
    # Visualizar predicciones
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
    
    evaluator.analyze_feature_importance(X_test, y_test, feature_names)
    
    # Evaluación por segmentos (tareas pequeñas, medianas, grandes)
    print("\n[Extra] Evaluando por segmentos de tamaño...")
    segments = {
        'Tareas pequeñas': lambda y: y <= 40,
        'Tareas medianas': lambda y: (y > 40) & (y <= 80),
        'Tareas grandes': lambda y: y > 80
    }
    
    evaluator.segmented_evaluation(X_test, y_test, segments)
    
    print("\n=== Proceso completado exitosamente ===")
    print(f"Todos los archivos han sido guardados en: {output_dir}")
    print("\nPara usar el modelo en predicciones, importe las clases necesarias y cargue el modelo:")
    print("  from rnn_model import AdvancedRNNEstimator")
    print("  model = AdvancedRNNEstimator.load('models', 'tiempo_estimator')")
    
    return estimator, processor, evaluator

if __name__ == "__main__":
    main()
