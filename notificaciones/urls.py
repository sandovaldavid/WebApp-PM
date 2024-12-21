from django.urls import path
from . import views

app_name = 'notificaciones'
urlpatterns = [
  path('', views.index, name='index'),
]