from django.urls import path, include
from . import views

app_name = 'redes_neuronales'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('estimate/', views.estimate_time, name='estimate_time'),
    path('estimacion-avanzada/', views.estimacion_avanzada, name='estimacion_avanzada'),
    path('entrenar-modelo/', views.entrenar_modelo, name='entrenar_modelo'),
    path('iniciar-entrenamiento/', views.iniciar_entrenamiento, name='iniciar_entrenamiento'),
    path('monitor-entrenamiento/', views.monitor_entrenamiento, name='monitor_entrenamiento'),
    path('model-status/', views.model_status, name='model_status'),
    path('estimacion/', include('redes_neuronales.estimacion_tiempo.urls')),
    path('evaluar-modelo/', views.evaluar_modelo, name='evaluar_modelo'),
    path('generar-archivos-evaluacion/', views.generar_archivos_evaluacion, name='generar_archivos_evaluacion'),
    # Nueva ruta para diagnóstico de logs de época
    path('diagnosticar-entrenamiento/', views.diagnosticar_entrenamiento, name='diagnosticar_entrenamiento'),
]
