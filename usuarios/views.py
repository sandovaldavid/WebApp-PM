from django.contrib.auth import authenticate, login as auth_login
from django.shortcuts import render, redirect
from usuarios.forms import LoginForm

# Create your views here.

def index(request):
    return render(request, 'usuarios/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=username, password=password)
            if user is not None:
                auth_login(request, user)
                return redirect('listar_proyectos')
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()
    return render(request, 'usuarios/login.html', {'form': form})
