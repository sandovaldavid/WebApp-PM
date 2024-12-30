from django.urls import path
from . import views

app_name = 'notificaciones'
urlpatterns = [
  path('', views.index, name='index'),
  path('crear-notificacion/', views.crear_notificacion, name='crear_notificacion'),
  path('crear-alerta/', views.crear_alerta, name='crear_alerta'),
  path('dashboard/', views.dashboard, name='dashboard'),
]