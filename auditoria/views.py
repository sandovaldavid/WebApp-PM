from django.shortcuts import render, redirect, get_object_or_404
from dashboard.models import Usuario, Actividad, Alerta
from .forms import ActividadForm
from django.db.models import Q
from django.http import JsonResponse

def registro_actividades(request):
    actividades = Actividad.objects.all()
    busqueda = request.GET.get("busqueda", "")
    filtro = request.GET.get("filtro", "")

    if busqueda:
        actividades = actividades.filter(idusuario__nombreusuario__icontains=busqueda)

    if filtro:
        actividades = actividades.filter(accion=filtro)

    estadisticas = {
        'total_actividades': Actividad.objects.count(),
        'usuarios_activos': Usuario.objects.filter(is_active=True).count(),
        'alertas_activas': Alerta.objects.filter(activa=True).count(),
    }
    datos_actividades_usuario = {
        'labels': [usuario.nombreusuario for usuario in Usuario.objects.all()],
        'data': [Actividad.objects.filter(idusuario=usuario).count() for usuario in Usuario.objects.all()],
    }
    datos_tipos_actividades = {
        'labels': ['Login', 'Logout', 'Creación', 'Modificación', 'Eliminación'],
        'data': [
            Actividad.objects.filter(accion__icontains='Login').count(),
            Actividad.objects.filter(accion__icontains='Logout').count(),
            Actividad.objects.filter(accion__icontains='Creación').count(),
            Actividad.objects.filter(accion__icontains='Modificación').count(),
            Actividad.objects.filter(accion__icontains='Eliminación').count(),
        ],
    }
    return render(
        request, 
        "auditoria/registro_actividades.html", 
        {
            "actividades": actividades,
            "estadisticas": estadisticas,
            "datos_actividades_usuario": datos_actividades_usuario,
            "datos_tipos_actividades": datos_tipos_actividades,
            "filtros": {"busqueda": busqueda, "filtro": filtro},
        }
    )

def intentos_acceso(request):
    intentos = []  # Consulta los intentos desde la base de datos.
    return render(request, "intentos_acceso.html", {"intentos": intentos})

def gestion_roles(request):
    usuarios = Usuario.objects.all()
    # roles = RolModuloAcceso.objects.all()
    return render(request, "gestion_roles.html", {"usuarios": usuarios, "roles": roles})

def crear_actividad(request):
    usuarios = Usuario.objects.all()
    if request.method == "POST":
        form = ActividadForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('auditoria:registro_actividades')
    else:
        form = ActividadForm()
    return render(request, 'auditoria/crear_actividad.html', {'form': form, 'usuarios': usuarios})

def editar_actividad(request, id):
    actividad = get_object_or_404(Actividad, idactividad=id)
    usuarios = Usuario.objects.all()
    if request.method == "POST":
        form = ActividadForm(request.POST, instance=actividad)
        if form.is_valid():
            form.save()
            return redirect('auditoria:registro_actividades')
    else:
        form = ActividadForm(instance=actividad)
    return render(request, 'auditoria/editar_actividad.html', {'form': form, 'actividad': actividad, 'usuarios': usuarios})

def eliminar_actividad(request, id):
    if request.method == 'POST':
        try:
            actividad = get_object_or_404(Actividad, idactividad=id)
            actividad.delete()
            return JsonResponse({'success': True})
        except Actividad.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Actividad no encontrada.'})
    return JsonResponse({'success': False, 'error': 'Método no permitido.'})
