from .model_service import EstimacionTiempoService

# Inicializar servicio global
estimacion_service = None

def get_estimacion_service():
    """Obtiene una instancia del servicio de estimación, inicializándola si es necesario"""
    global estimacion_service
    if estimacion_service is None or not estimacion_service.is_initialized:
        estimacion_service = EstimacionTiempoService()
        estimacion_service.initialize()
    return estimacion_service
