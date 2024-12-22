from django.shortcuts import render, redirect
from usuarios.forms import LoginForm

# Create your views here.

def index(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('listar_proyectos')
    else:
        form = LoginForm()
    return render(request, 'usuarios/index.html', {'form': form})