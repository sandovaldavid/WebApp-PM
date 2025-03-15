import os
import sys
import json
import glob
import numpy as np
import joblib
import traceback
from datetime import datetime


def generate_evaluation_files(request):
    """Función para generar archivos de evaluación bajo demanda"""
    try:
        # Forzar uso de backend no interactivo para matplotlib
        import matplotlib

        matplotlib.use('Agg')
        os.environ['MPLBACKEND'] = 'Agg'

        from .estimacion_tiempo.generate_evaluation_files import main as generate_files

        # Ejecutar la generación de archivos
        success = generate_files()

        return {
            'success': success,
            'message': (
                'Archivos generados correctamente'
                if success
                else 'Error al generar archivos'
            ),
        }
    except Exception as e:
        traceback.print_exc()
        return {'success': False, 'message': f'Error inesperado: {str(e)}'}


def check_model_files():
    """Verifica los archivos necesarios para el modelo"""
    output_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')

    required_files = [
        'tiempo_estimator_model.keras',
        'tiempo_estimator_config.joblib',
        'feature_dims.pkl',
    ]

    missing_files = []
    for file in required_files:
        if not os.path.exists(os.path.join(output_dir, file)):
            missing_files.append(file)

    return {'all_present': len(missing_files) == 0, 'missing_files': missing_files}


def run_manual_evaluation():
    """Ejecuta evaluación manual del modelo y genera todos los archivos necesarios"""
    try:
        # Configurar backend no interactivo
        import matplotlib

        matplotlib.use('Agg')
        os.environ['MPLBACKEND'] = 'Agg'

        # Ejecutar la generación de archivos
        from .estimacion_tiempo.run_evaluation import run_manual_evaluation as run_eval

        success = run_eval()

        return {
            'success': success,
            'message': (
                'Evaluación manual completada exitosamente'
                if success
                else 'Error durante la evaluación manual'
            ),
        }
    except Exception as e:
        traceback.print_exc()
        return {
            'success': False,
            'message': f'Error durante la evaluación manual: {str(e)}',
        }


def get_model_status():
    """Obtiene el estado actual del modelo"""
    model_dir = os.path.join('redes_neuronales', 'estimacion_tiempo', 'models')

    try:
        # Verificar si existe el modelo principal
        model_path = os.path.join(model_dir, 'tiempo_estimator_model.keras')
        if not os.path.exists(model_path):
            return {
                'status': 'not_found',
                'message': 'No se encontró el modelo principal',
            }

        # Cargar métricas
        metrics_path = os.path.join(model_dir, 'evaluation_metrics.json')
        if os.path.exists(metrics_path):
            with open(metrics_path, 'r') as f:
                metrics = json.load(f)
        else:
            metrics = None

        # Obtener fecha de la última modificación
        modified_time = os.path.getmtime(model_path)
        modified_date = datetime.fromtimestamp(modified_time).strftime(
            '%Y-%m-%d %H:%M:%S'
        )

        # Determinar estado basado en presencia de archivos de evaluación
        evaluation_files = glob.glob(os.path.join(model_dir, '*.json'))
        evaluation_files.extend(glob.glob(os.path.join(model_dir, '*.png')))

        if len(evaluation_files) >= 5:
            status = 'ready'
        else:
            status = 'needs_evaluation'

        return {
            'status': status,
            'message': (
                'Modelo listo para usar'
                if status == 'ready'
                else 'Se recomienda generar archivos de evaluación'
            ),
            'modified': modified_date,
            'metrics': metrics,
        }
    except Exception as e:
        return {
            'status': 'error',
            'message': f'Error al verificar estado del modelo: {str(e)}',
        }


@login_required
def generar_archivos_evaluacion(request):
    """Vista para generar archivos de evaluación para un modelo existente"""
    if request.method == 'POST':
        try:
            # Usar la función utilitaria para generar los archivos
            from .views_utils import generate_evaluation_files, check_model_files

            # Primero verificar si existen los archivos necesarios
            model_check = check_model_files()
            if not model_check['all_present']:
                return JsonResponse(
                    {
                        'success': False,
                        'message': f'Faltan archivos necesarios: {", ".join(model_check["missing_files"][:3])}',
                    }
                )

            # Generar archivos
            result = generate_evaluation_files(request)
            return JsonResponse(result)
        except Exception as e:
            import traceback

            traceback.print_exc()
            return JsonResponse(
                {
                    'success': False,
                    'message': f'Error al generar archivos de evaluación: {str(e)}',
                }
            )

    return JsonResponse({'success': False, 'message': 'Método no permitido.'})
