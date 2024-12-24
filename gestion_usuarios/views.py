# usuarios/views.py
from django.shortcuts import render, get_object_or_404, redirect
from dashboard.models import Usuario

def lista_usuarios(request):
    usuarios = Usuario.objects.all()
    return render(request, 'gestion_usuarios/lista_usuarios.html', {'usuarios': usuarios})

def crear_usuario(request):
    if request.method == 'POST':
        # Captura los datos enviados desde el formulario
        nombre = request.POST.get('nombreUsuario')
        email = request.POST.get('email')
        contrasena = request.POST.get('contrasena')
        rol = request.POST.get('rol')
        
        # Crea el usuario
        Usuario.objects.create(nombreUsuario=nombre, email=email, contrasena=contrasena, rol=rol)
        return redirect('gestionUsuarios:lista_usuarios')
    return render(request, 'gestion_usuarios/crear_usuario.html')

