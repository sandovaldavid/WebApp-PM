from django.shortcuts import render
from dashboard.models import Usuario, Actividad


def registro_actividades(request):
    actividades = (
        Actividad.objects.all()
    )  # Obtén los datos necesarios desde la base de datos.
    return render(
        request, "auditoria/registro_actividades.html", {"actividades": actividades}
    )


def intentos_acceso(request):
    intentos = []  # Consulta los intentos desde la base de datos.
    return render(request, "intentos_acceso.html", {"intentos": intentos})


def gestion_roles(request):
    usuarios = Usuario.objects.all()
    # roles = RolModuloAcceso.objects.all()
    return render(request, "gestion_roles.html", {"usuarios": usuarios, "roles": roles})
