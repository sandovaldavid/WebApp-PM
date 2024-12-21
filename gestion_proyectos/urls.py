from django.urls import path
from . import views

app_name = 'gestion_proyectos'
urlpatterns = [
    path('', views.index, name='index'),
]
