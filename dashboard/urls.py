from django.urls import path
from . import views

app_name = 'dashboard'
urlpatterns = [
    path('panel/', views.index, name='index'),
]