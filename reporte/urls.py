from django.urls import path
from . import views

app_name = 'reportes'
urlpatterns = [
    path('', views.index, name='index'),
]