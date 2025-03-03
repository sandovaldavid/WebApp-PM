import os
import sys
import argparse
import numpy as np
import pandas as pd
import joblib
from rnn_model import AdvancedRNNEstimator
from data_processor import DataProcessor

def parse_args():
    parser = argparse.ArgumentParser(description='Predecir tiempo con modelo RNN entrenado')
    parser.add_argument('--model-dir', type=str, default='models',
                        help='Directorio donde está guardado el modelo')
    parser.add_argument('--model-name', type=str, default='tiempo_estimator',
                        help='Nombre base del modelo')
    parser.add_argument('--input-file', type=str, 
                        help='Archivo CSV con datos de tareas a predecir')
    parser.add_argument('--output-file', type=str, default='predicciones.csv',
                        help='Archivo CSV donde guardar las predicciones')
                        
    return parser.parse_args()

def predict_from_csv(model, processor, input_file, output_file):
    """Realiza predicciones para datos en un archivo CSV
    
    Args:
        model: Modelo entrenado (AdvancedRNNEstimator)
        processor: Procesador de datos configurado (DataProcessor)
        input_file: Ruta al archivo CSV con datos de entrada
        output_file: Ruta donde guardar las predicciones
    """
    try:
        # Cargar datos
        data = pd.read_csv(input_file)
        print(f"Datos cargados correctamente desde {input_file}")
        print(f"Forma de los datos: {data.shape}")
        
        # Verificar que contiene las columnas necesarias
        required_columns = [
            'Complejidad', 'Tipo_Tarea', 'Fase_Tarea', 'Cantidad_Recursos',
            'Carga_Trabajo_R1', 'Experiencia_R1', 'Experiencia_Equipo',
            'Claridad_Requisitos', 'Tamaño_Tarea'
        ]
        
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            print(f"Error: Faltan columnas necesarias: {missing_columns}")
            return
        
        # Procesar cada registro
        results = []
        for i, row in data.iterrows():
            task_data = {
                'Complejidad': row['Complejidad'],
                'Tipo_Tarea': row['Tipo_Tarea'],
                'Fase_Tarea': row['Fase_Tarea'],
                'Cantidad_Recursos': row['Cantidad_Recursos'],
                'Carga_Trabajo_R1': row.get('Carga_Trabajo_R1', 0),
                'Experiencia_R1': row.get('Experiencia_R1', 0),
                'Carga_Trabajo_R2': row.get('Carga_Trabajo_R2', 0),
                'Experiencia_R2': row.get('Experiencia_R2', 0),
                'Carga_Trabajo_R3': row.get('Carga_Trabajo_R3', 0),
                'Experiencia_R3': row.get('Experiencia_R3', 0),
                'Experiencia_Equipo': row['Experiencia_Equipo'],
                'Claridad_Requisitos': row['Claridad_Requisitos'],
                'Tamaño_Tarea': row['Tamaño_Tarea']
            }
            
            # Procesar datos para el modelo
            X = processor.process_single_task(task_data)
            
            # Realizar la predicción
            prediction = model.predict(X, processor.feature_dims)
            
            # Añadir resultado
            results.append({
                'ID': i,
                'Tiempo_Estimado': prediction[0],
                **task_data
            })
            
        # Crear DataFrame con resultados
        results_df = pd.DataFrame(results)
        
        # Guardar resultados
        results_df.to_csv(output_file, index=False)
        print(f"Predicciones guardadas en {output_file}")
        
        # Mostrar estadísticas
        print("\nEstadísticas de predicciones:")
        print(f"Promedio: {results_df['Tiempo_Estimado'].mean():.2f} horas")
        print(f"Mediana: {results_df['Tiempo_Estimado'].median():.2f} horas")
        print(f"Mínimo: {results_df['Tiempo_Estimado'].min():.2f} horas")
        print(f"Máximo: {results_df['Tiempo_Estimado'].max():.2f} horas")
        
        return results_df
        
    except Exception as e:
        print(f"Error durante la predicción: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def predict_single_task(model, processor, task_data):
    """Realiza una predicción para una única tarea
    
    Args:
        model: Modelo entrenado (AdvancedRNNEstimator)
        processor: Procesador de datos configurado (DataProcessor)
        task_data: Diccionario con datos de la tarea
        
    Returns:
        float: Tiempo estimado en horas
    """
    try:
        # Procesar datos para el modelo
        X = processor.process_single_task(task_data)
        
        # Realizar la predicción
        prediction = model.predict(X, processor.feature_dims)
        
        return prediction[0]
    
    except Exception as e:
        print(f"Error durante la predicción: {str(e)}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    """Función principal para realizar predicciones con modelo entrenado"""
    args = parse_args()
    
    print("\n=== Predicción de tiempos de tareas con RNN ===")
    
    # 1. Cargar el modelo
    try:
        print("[1/3] Cargando modelo...")
        model = AdvancedRNNEstimator.load(args.model_dir, args.model_name)
        print(f"Modelo cargado correctamente desde {args.model_dir}/{args.model_name}_model.keras")
    except Exception as e:
        print(f"Error al cargar el modelo: {str(e)}")
        return
    
    # 2. Cargar los preprocesadores
    try:
        print("[2/3] Cargando preprocesadores...")
        processor = DataProcessor()
        success = processor.load_preprocessors(args.model_dir)
        if not success:
            print("Error al cargar los preprocesadores.")
            return
    except Exception as e:
        print(f"Error al cargar preprocesadores: {str(e)}")
        return
    
    # 3. Realizar predicciones
    if args.input_file:
        print("[3/3] Realizando predicciones desde archivo...")
        results = predict_from_csv(model, processor, args.input_file, args.output_file)
    else:
        print("[3/3] No se proporcionó archivo de entrada para predicciones.")
        print("\nEjemplo de entrada para predecir una tarea:")
        print("  task_data = {")
        print("      'Complejidad': 3,")
        print("      'Tipo_Tarea': 'Backend',")
        print("      'Fase_Tarea': 'Construcción/Desarrollo',")
        print("      'Cantidad_Recursos': 2,")
        print("      'Carga_Trabajo_R1': 0.8,")
        print("      'Experiencia_R1': 4,")
        print("      'Experiencia_Equipo': 3,")
        print("      'Claridad_Requisitos': 0.7,")
        print("      'Tamaño_Tarea': 8")
        print("  }")
        print("  tiempo = predict_single_task(model, processor, task_data)")
    
    print("\n=== Predicción completada ===")
    
    return model, processor

if __name__ == "__main__":
    main()
