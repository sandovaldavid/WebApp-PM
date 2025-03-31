from django.urls import path
from . import views_integration

urlpatterns = [
    path('api/estimacion/tarea', views_integration.estimate_task_api, name='api_estimacion_tarea'),
    path('api/estimacion/tarea/reestimar', views_integration.reestimate_task_api, name='api_reestimacion_tarea'),
    path('api/estimacion/proyecto/<int:proyecto_id>', views_integration.project_estimation_api, name='api_estimacion_proyecto'),
]
