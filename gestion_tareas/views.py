from django.shortcuts import render

# Create your views here.

def index(request):
    return render(request, 'gestion_tareas/index.html')

def tareas_programadas(request):
    return render(request, 'gestion_tareas_programadas/index.html')