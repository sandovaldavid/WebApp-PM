from django.urls import path, include
from . import views

app_name = 'redes_neuronales'

urlpatterns = [
    # Rutas para dashboard y estimación
    path('dashboard/', views.dashboard, name='redes_dashboard'),
    path('estimate-time/', views.estimate_time, name='estimate_time'),
    path('estimacion-avanzada/', views.estimacion_avanzada, name='estimacion_avanzada'),
    
    # Rutas para entrenamiento de modelos
    path('entrenar-modelo/', views.entrenar_modelo, name='entrenar_modelo'),
    path('iniciar-entrenamiento/', views.iniciar_entrenamiento, name='iniciar_entrenamiento'),
    path('monitor-entrenamiento/', views.monitor_entrenamiento, name='monitor_entrenamiento'),
    path('generar-archivos-evaluacion/', views.generar_archivos_evaluacion, name='generar_archivos_evaluacion'),
    path('evaluar-modelo/', views.evaluar_modelo, name='evaluar_modelo'),
    
    # Endpoints de diagnóstico y estado
    path('diagnosticar-entrenamiento/', views.diagnosticar_entrenamiento, name='diagnosticar_entrenamiento'),
    path('model-status/', views.model_status, name='model_status'),
    
    # Rutas para acceder a archivos de evaluación (estáticas y seguras)
    # Estas rutas serán manejadas por el servidor web en producción
    path('estimacion/', include('redes_neuronales.estimacion_tiempo.urls')),
]
