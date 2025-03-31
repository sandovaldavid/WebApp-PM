import os
import sys
import joblib
import numpy as np

# Asegurarse de que podemos importar desde el directorio padre
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

# Directorios y archivos
MODEL_DIR = os.path.join(os.path.dirname(__file__), 'models')
MODEL_NAME = 'tiempo_estimator'

def run_manual_evaluation():
    """Ejecuta una evaluación manual del modelo guardado"""
    try:
        print(f"Ejecutando evaluación manual desde {os.path.abspath(__file__)}")
        
        # Cargar recursos necesarios
        print(f"Cargando modelo desde {MODEL_DIR}...")
        
        # 1. Cargar feature_dims
        feature_dims_path = os.path.join(MODEL_DIR, 'feature_dims.pkl')
        if not os.path.exists(feature_dims_path):
            print(f"No se encuentra feature_dims en {feature_dims_path}")
            return False
            
        feature_dims = joblib.load(feature_dims_path)
        print(f"Feature dimensions: {feature_dims}")
        
        # 2. Cargar modelo
        from rnn_model import AdvancedRNNEstimator
        model_path = os.path.join(MODEL_DIR, f'{MODEL_NAME}_model.keras')
        if not os.path.exists(model_path):
            print(f"No se encuentra el modelo en {model_path}")
            return False
            
        try:
            estimator = AdvancedRNNEstimator.load(MODEL_DIR, MODEL_NAME)
            print("Modelo cargado correctamente")
        except Exception as e:
            print(f"Error al cargar el modelo: {e}")
            return False
        
        # 3. Generar datos de prueba o cargar datos guardados
        try:
            # Intentar cargar datos de prueba si existen
            X_val_path = os.path.join(MODEL_DIR, 'X_val.npy')
            y_val_path = os.path.join(MODEL_DIR, 'y_val.npy')
            
            if os.path.exists(X_val_path) and os.path.exists(y_val_path):
                print("Cargando datos de validación guardados...")
                X_val = np.load(X_val_path)
                y_val = np.load(y_val_path)
            else:
                # Crear datos de prueba aleatorios
                print("Creando datos de prueba aleatorios...")
                total_dims = sum(feature_dims.values())
                X_val = np.random.randn(100, total_dims) * 0.5
                y_val = np.random.rand(100) * 20 + 10
                
                # Guardar para uso futuro
                np.save(X_val_path, X_val)
                np.save(y_val_path, y_val)
        except Exception as e:
            print(f"Error al preparar datos de validación: {e}")
            return False
        
        # 4. Crear evaluador y ejecutar evaluación
        from evaluator import ModelEvaluator
        print("Creando ModelEvaluator...")
        evaluator = ModelEvaluator(estimator, feature_dims, MODEL_DIR)
        
        print(f"Ejecutando evaluación con {len(X_val)} registros...")
        metrics, y_pred = evaluator.evaluate_model(X_val, y_val)
        
        print("\nEvaluación completada con éxito!")
        print(f"R²: {metrics.get('R2', 0):.4f}")
        print(f"MAE: {metrics.get('MAE', 0):.4f}")
        print(f"Accuracy: {metrics.get('Accuracy', 0):.4f}")
        
        # Listar archivos generados
        print("\nArchivos generados:")
        for file in os.listdir(MODEL_DIR):
            if file.endswith('.csv') or file.endswith('.json') or file.endswith('.png'):
                print(f" - {file}")
        
        return True
        
    except Exception as e:
        print(f"Error durante ejecución manual: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Ejecutar evaluación manual
    success = run_manual_evaluation()
    print(f"\nEjecución {'exitosa' if success else 'fallida'}")
