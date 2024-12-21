from django.urls import path
from . import views

app_name = 'gestion_tareas'
urlpatterns = [
    path('', views.index, name='index'),
]
