from django.urls import path
from . import views

app_name = 'redes_neuronales'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('estimate/', views.estimate_time, name='estimate_time'),
]
