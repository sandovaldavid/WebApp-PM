from django.urls import path
from . import views

app_name = 'notificaciones'
urlpatterns = [
  path('crear-notificacion/', views.crear_notificacion, name='crear_notificacion'),
  path('crear-alerta/', views.crear_alerta, name='crear_alerta'),
  path('', views.dashboard, name='index'),
]