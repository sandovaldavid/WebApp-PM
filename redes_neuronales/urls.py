from django.urls import path, include
from . import views

app_name = 'redes_neuronales'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('estimate/', views.estimate_time, name='estimate_time'),
    path('estimacion-avanzada/', views.estimacion_avanzada, name='estimacion_avanzada'),
    path('estimacion/', include('redes_neuronales.estimacion_tiempo.urls')),
]
