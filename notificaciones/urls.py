from django.urls import path
from . import views

app_name = 'gestion'
urlpatterns = [
    path('tareas', views.index, name='index'),
]