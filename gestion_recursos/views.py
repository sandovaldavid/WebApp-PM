from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone

from dashboard.models import (
    Recurso,
    Tiporecurso,
    Recursohumano,
    Recursomaterial,
    Proyecto,
    Tarea,
    Tarearecurso,
    Usuario,
    Equipo,
    Miembro,
    Requerimiento
)
from django.db import transaction
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.http import JsonResponse


@login_required
def lista_recursos(request):
    busqueda = request.GET.get("busqueda", "")
    vista = request.GET.get("vista", "grid")
    tipo = request.GET.get("tipo", "")
    page = request.GET.get("page", 1)

    recursos = Recurso.objects.all()

    if busqueda:
        recursos = recursos.filter(nombrerecurso__icontains=busqueda)

    if tipo:
        if tipo == "Humano":
            recursos = recursos.filter(recursohumano__isnull=False)
        elif tipo == "Material":
            recursos = recursos.filter(recursomaterial__isnull=False)

    recursos_con_costos = []
    for recurso in recursos:
        if hasattr(recurso, "recursohumano"):
            costo = f"{recurso.recursohumano.tarifahora}/hora"
            tipo = "Humano"
        elif hasattr(recurso, "recursomaterial"):
            costo = f"{recurso.recursomaterial.costounidad}/unidad"
            tipo = "Material"
        else:
            costo = None
            tipo = "Desconocido"
        recursos_con_costos.append({"recurso": recurso, "costo": costo, "tipo": tipo})

    paginator = Paginator(recursos_con_costos, 9)
    try:
        recursos_paginados = paginator.page(page)
    except PageNotAnInteger:
        recursos_paginados = paginator.page(1)
    except EmptyPage:
        recursos_paginados = paginator.page(paginator.num_pages)

    # Estadísticas
    total_recursos = Recurso.objects.count()
    total_recursos_humanos = Recursohumano.objects.count()
    total_recursos_materiales = Recursomaterial.objects.count()
    recursos_humanos_disponibles = Recursohumano.objects.filter(idrecurso__disponibilidad=True).count()
    recursos_materiales_disponibles = Recursomaterial.objects.filter(idrecurso__disponibilidad=True).count()

    estadisticas = {
        "total_recursos": total_recursos,
        "total_recursos_humanos": total_recursos_humanos,
        "total_recursos_materiales": total_recursos_materiales,
        "recursos_humanos_disponibles": recursos_humanos_disponibles,
        "recursos_materiales_disponibles": recursos_materiales_disponibles,
    }

    proyectos = Proyecto.objects.all()
    context = {
        "recursos": recursos_paginados,
        "vista": vista,
        "filtros": {"busqueda": busqueda, "tipo": tipo},
        "proyectos": proyectos,
        "estadisticas": estadisticas,
    }
    return render(
        request,
        "gestion_recursos/lista_recursos.html",
        context,
    )


@login_required
def detalle_recurso(request, id):
    recurso = get_object_or_404(Recurso, pk=id)
    habilidades = recurso.recursohumano.habilidades.split(',') if recurso.idtiporecurso.idtiporecurso == 1 else []
    context = {
        "recurso": recurso,
        "habilidades": habilidades,
    }
    return render(request, "gestion_recursos/detalle_recurso.html", context)


@login_required
def crear_recurso(request):
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        id_tipo = request.POST.get("tipo_recurso")
        tipo = get_object_or_404(Tiporecurso, pk=id_tipo)

        with transaction.atomic():

            recurso = Recurso.objects.create(
                nombrerecurso=nombre,
                idtiporecurso=tipo,
                disponibilidad=True,
                fechacreacion=timezone.now(),
            )

            if tipo.idtiporecurso == 1:  # Recurso Humano
                cargo = request.POST.get("cargo")
                habilidades = request.POST.get("habilidades")
                tarifahora = request.POST.get("tarifahora")
                id_usuario = request.POST.get("usuario")
                usuario = Usuario.objects.get(pk=id_usuario)
                Recursohumano.objects.create(
                    idrecurso=recurso,
                    cargo=cargo,
                    habilidades=habilidades,
                    tarifahora=tarifahora,
                    idusuario=usuario,
                )
            elif tipo.idtiporecurso == 2:  # Recurso Material
                costounidad = request.POST.get("costounidad")
                fechacompra = request.POST.get("fechacompra")
                Recursomaterial.objects.create(
                    idrecurso=recurso, costounidad=costounidad, fechacompra=fechacompra
                )

        return redirect("gestionRecursos:lista_recursos")

    tipos = Tiporecurso.objects.all()
    usuarios_no_asignados = Usuario.objects.filter(recursohumano__isnull=True)
    return render(
        request,
        "gestion_recursos/crear_recurso.html",
        {"tipos": tipos, "usuarios_no_asignados": usuarios_no_asignados},
    )


@login_required
def editar_recurso(request, id):
    recurso = get_object_or_404(Recurso, pk=id)
    habilidades = recurso.recursohumano.habilidades.split(',') if recurso.idtiporecurso.idtiporecurso == 1 else []
    if request.method == "POST":
        recurso.nombrerecurso = request.POST.get("nombre")
        recurso.fechamodificacion = timezone.now()
        recurso.save()

        if recurso.idtiporecurso.idtiporecurso == 1:  # Recurso Humano
            recursohumano = get_object_or_404(Recursohumano, pk=id)
            recursohumano.cargo = request.POST.get("cargo")
            recursohumano.habilidades = request.POST.get("habilidades")
            recursohumano.tarifahora = request.POST.get("tarifahora")
            recursohumano.save()
        elif recurso.idtiporecurso.idtiporecurso == 2:  # Recurso Material
            recursomaterial = get_object_or_404(Recursomaterial, pk=id)
            recursomaterial.costounidad = request.POST.get("costounidad")
            recursomaterial.fechacompra = request.POST.get("fechacompra")
            recursomaterial.save()

        return redirect("gestionRecursos:lista_recursos")

    tipos = Tiporecurso.objects.all()
    return render(
        request,
        "gestion_recursos/editar_recurso.html",
        {"recurso": recurso, "tipos": tipos, "habilidades": habilidades},
    )


@login_required
def eliminar_recurso(request, id):
    recurso = get_object_or_404(Recurso, pk=id)

    # Eliminar de las tablas relacionadas
    if hasattr(recurso, "recursohumano"):
        recurso.recursohumano.delete()
    elif hasattr(recurso, "recursomaterial"):
        recurso.recursomaterial.delete()

    recurso.delete()
    return redirect("gestionRecursos:lista_recursos")


@login_required
def asignar_recurso(request):
    if request.method == "POST":
        recurso_id = request.POST.get("recurso")
        tarea_id = request.POST.get("tarea")
        fecha_asignacion = request.POST.get("fecha_asignacion")

        recurso = get_object_or_404(Recurso, pk=recurso_id)
        tarea = get_object_or_404(Tarea, pk=tarea_id)

        # Verificar si ya existe la asignación del recurso a la tarea
        if not Tarearecurso.objects.filter(idtarea=tarea, idrecurso=recurso).exists():
            Tarearecurso.objects.create(idtarea=tarea, idrecurso=recurso, cantidad=1)

        return redirect("gestionRecursos:lista_recursos")

    proyectos = Proyecto.objects.all()
    context = {
        "proyectos": proyectos,
    }
    return render(request, "gestion_recursos/asignar_recurso.html", context)

@login_required
def obtener_requerimientos(request, proyecto_id):
    requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_id)
    data = [{"idrequerimiento": req.idrequerimiento, "descripcion": req.descripcion} for req in requerimientos]
    return JsonResponse(data, safe=False)

@login_required
def obtener_tareas(request, requerimiento_id):
    tareas = Tarea.objects.filter(idrequerimiento=requerimiento_id)
    data = [{"idtarea": tarea.idtarea, "nombretarea": tarea.nombretarea} for tarea in tareas]
    return JsonResponse(data, safe=False)


@login_required
def obtener_recursos(request, proyecto_id):
    proyecto = get_object_or_404(Proyecto, pk=proyecto_id)
    equipo = proyecto.idequipo
    miembros = Miembro.objects.filter(idequipo=equipo)
    recursos = [miembro.idrecurso for miembro in miembros]
    data = [
        {"idrecurso": recurso.idrecurso, "nombrerecurso": recurso.nombrerecurso}
        for recurso in recursos
    ]
    return JsonResponse(data, safe=False)
