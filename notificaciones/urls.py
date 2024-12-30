from django.urls import path
from . import views

app_name = "notificaciones"
urlpatterns = [
    path("crear-notificacion/", views.crear_notificacion, name="crear_notificacion"),
    path("crear-alerta/", views.crear_alerta, name="crear_alerta"),
    path("", views.dashboard, name="index"),
    path("notificacion/<int:id>/", views.detalle_notificacion, name="detalle_notificacion"),
    path('alerta/<int:id>/', views.detalle_alerta, name='detalle_alerta'),
    path('notificacion/<int:id>/marcar/', views.marcar_notificacion, name='marcar_notificacion'),
]