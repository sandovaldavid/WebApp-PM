from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from dashboard.models import Equipo, Miembro, Recurso, Tiporecurso
from django.db.models import Prefetch, Count, Q
from django.utils import timezone


@login_required
def index(request):
    """Vista principal de gestión de equipos"""
    # Obtener parámetros de la URL
    vista = request.GET.get("vista", "grid")
    busqueda = request.GET.get("busqueda", "")
    page = request.GET.get("page", 1)

    # Query base
    equipos = Equipo.objects.all()

    # Aplicar búsqueda si existe
    if busqueda:
        equipos = equipos.filter(
            Q(nombreequipo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    # Añadir datos relacionados para optimizar queries
    equipos = (
        equipos.prefetch_related(
            "miembro_set",
            "proyecto_set",
            "miembro_set__idrecurso",
            Prefetch(
                "miembro_set__idrecurso",
                queryset=Recurso.objects.select_related("idtiporecurso"),
            ),
        )
        .annotate(total_miembros=Count("miembro"), total_proyectos=Count("proyecto"))
        .order_by("-fechacreacion")
    )

    # Paginación
    paginator = Paginator(equipos, 9)  # 9 equipos por página
    try:
        equipos_paginados = paginator.page(page)
    except PageNotAnInteger:
        equipos_paginados = paginator.page(1)
    except EmptyPage:
        equipos_paginados = paginator.page(paginator.num_pages)

    # Estadísticas
    estadisticas = {
        "total_equipos": Equipo.objects.count(),
        "miembros_activos": Miembro.objects.filter(
            idrecurso__tarearecurso__idtarea__estado="En Progreso"
        )
        .distinct()
        .count(),
        "equipos_con_proyectos": Equipo.objects.filter(proyecto__isnull=False)
        .distinct()
        .count(),
    }

    context = {
        "equipos": equipos_paginados,
        "vista": vista,
        "filtros": {"busqueda": busqueda},
        "estadisticas": estadisticas,
    }

    return render(request, "gestion_equipos/index.html", context)


@login_required
def crear_equipo(request):
    """Vista para crear un nuevo equipo"""
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion")

            # Validaciones
            if not nombre:
                messages.error(request, "El nombre del equipo es requerido")
                return redirect("gestion_equipos:crear_equipo")

            # Crear equipo
            equipo = Equipo.objects.create(
                nombreequipo=nombre,
                descripcion=descripcion,
                fechacreacion=timezone.now(),
                fechamodificacion=timezone.now(),
            )

            messages.success(request, "Equipo creado exitosamente")
            return redirect("gestion_equipos:index")

        except Exception as e:
            messages.error(request, f"Error al crear el equipo: {str(e)}")
            return redirect("gestion_equipos:crear_equipo")

    return render(request, "gestion_equipos/crear_equipo.html")


@login_required
def eliminar_equipo(request, equipo_id):
    """Vista para eliminar un equipo"""
    if request.method == "POST":
        try:
            equipo = get_object_or_404(Equipo, idequipo=equipo_id)

            # Verificar si tiene proyectos activos
            if equipo.proyecto_set.filter(estado="En Progreso").exists():
                messages.error(
                    request, "No se puede eliminar un equipo con proyectos activos"
                )
                return redirect("gestion_equipos:index")

            # Eliminar equipo y sus relaciones
            equipo.delete()
            messages.success(request, "Equipo eliminado exitosamente")

        except Exception as e:
            messages.error(request, f"Error al eliminar el equipo: {str(e)}")

    return redirect("gestion_equipos:index")


@login_required
def editar_equipo(request, equipo_id):
    """Vista para editar un equipo"""
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)

    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion")

            # Validaciones
            if not nombre:
                messages.error(request, "El nombre del equipo es requerido")
                return redirect("gestion_equipos:editar_equipo", equipo_id=equipo_id)

            # Actualizar equipo
            equipo.nombreequipo = nombre
            equipo.descripcion = descripcion
            equipo.fechamodificacion = timezone.now()
            equipo.save()

            messages.success(request, "Equipo actualizado exitosamente")
            return redirect("gestion_equipos:index")

        except Exception as e:
            messages.error(request, f"Error al actualizar el equipo: {str(e)}")
            return redirect("gestion_equipos:editar_equipo", equipo_id=equipo_id)

    return render(request, "gestion_equipos/editar_equipo.html", {"equipo": equipo})


@login_required
def gestionar_miembros(request, equipo_id):
    """Vista para gestionar los miembros de un equipo"""
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)

    # Obtener parámetros
    vista = request.GET.get("vista", "grid")  # default: vista de tarjetas
    tipo = request.GET.get("tipo", "todos")
    busqueda = request.GET.get("busqueda", "")

    # Query base con relaciones necesarias
    miembros = equipo.miembro_set.select_related(
        "idrecurso",
        "idrecurso__idtiporecurso",
        "idrecurso__recursohumano",
        "idrecurso__recursomaterial",
    )

    # Aplicar filtros
    if busqueda:
        miembros = miembros.filter(idrecurso__nombrerecurso__icontains=busqueda)

    if tipo != "todos":
        if tipo == "humano":
            miembros = miembros.filter(idrecurso__idtiporecurso=1)
        elif tipo == "material":
            miembros = miembros.filter(idrecurso__idtiporecurso=2)

    context = {
        "equipo": equipo,
        "miembros": miembros,
        "vista": vista,
        "filtros": {"tipo": tipo, "busqueda": busqueda},
    }

    return render(request, "gestion_equipos/gestionar_miembros.html", context)


@login_required
def lista_miembros(request, equipo_id):
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)
    vista = request.GET.get("vista", "grid")  # default a vista de tarjetas
    tipo = request.GET.get("tipo", "todos")
    busqueda = request.GET.get("busqueda", "")

    # Query base con relaciones necesarias
    miembros = equipo.miembro_set.select_related(
        "idrecurso",
        "idrecurso__recursohumano",
        "idrecurso__recursomaterial",
        "idrecurso__idtiporecurso",
    )

    # Aplicar filtros
    if busqueda:
        miembros = miembros.filter(idrecurso__nombrerecurso__icontains=busqueda)

    if tipo != "todos":
        if tipo == "humano":
            miembros = miembros.filter(idrecurso__idtiporecurso=1)
        elif tipo == "material":
            miembros = miembros.filter(idrecurso__idtiporecurso=2)

    context = {
        "equipo": equipo,
        "miembros": miembros,
        "vista": vista,
        "filtros": {"tipo": tipo, "busqueda": busqueda},
    }

    return render(request, "components/lista_miembros.html", context)


@login_required
def lista_equipos(request):
    """Vista para listar todos los equipos con filtros y paginación"""

    # Obtener parámetros de la URL
    vista = request.GET.get("vista", "grid")  # Default: vista de tarjetas
    busqueda = request.GET.get("busqueda", "")
    page = request.GET.get("page", 1)

    # Query base
    equipos = Equipo.objects.all()

    # Aplicar búsqueda si existe
    if busqueda:
        equipos = equipos.filter(
            Q(nombreequipo__icontains=busqueda) | Q(descripcion__icontains=busqueda)
        )

    # Añadir datos relacionados para optimizar queries
    equipos = (
        equipos.prefetch_related(
            "miembro_set",
            "proyecto_set",
            "miembro_set__idrecurso",
            "miembro_set__idrecurso__idtiporecurso",
        )
        .annotate(total_miembros=Count("miembro"), total_proyectos=Count("proyecto"))
        .order_by("-fechacreacion")
    )

    # Paginación
    paginator = Paginator(equipos, 9)  # 9 equipos por página
    try:
        equipos_paginados = paginator.page(page)
    except:
        equipos_paginados = paginator.page(1)

    # Estadísticas
    estadisticas = {
        "total_equipos": Equipo.objects.count(),
        "miembros_activos": Miembro.objects.filter(
            idrecurso__tarearecurso__idtarea__estado="En Progreso"
        )
        .distinct()
        .count(),
        "equipos_con_proyectos": Equipo.objects.filter(proyecto__isnull=False)
        .distinct()
        .count(),
    }

    context = {
        "equipos": equipos_paginados,
        "vista": vista,
        "filtros": {"busqueda": busqueda},
        "estadisticas": estadisticas,
    }

    return render(request, "gestion_equipos/lista_equipos.html", context)


@login_required
def detalle_equipo(request, equipo_id):
    """Vista para mostrar el detalle de un equipo"""
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)

    # Calcular métricas
    tareas_pendientes = 0
    for proyecto in equipo.proyecto_set.all():
        for requerimiento in proyecto.requerimiento_set.all():
            tareas_pendientes += requerimiento.tarea_set.filter(
                estado="Pendiente"
            ).count()

    # Obtener proyectos activos
    proyectos_activos = equipo.proyecto_set.filter(estado="En Progreso").count()

    context = {
        "equipo": equipo,
        "tareas_pendientes": tareas_pendientes,
        "proyectos_activos": proyectos_activos,
    }

    return render(request, "gestion_equipos/detalle_equipo.html", context)


@login_required
def crear_miembro(request, equipo_id):
    """Vista para agregar un nuevo miembro al equipo"""
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)

    if request.method == "POST":
        try:
            tipo_recurso = request.POST.get("tipo_recurso")
            recurso_id = request.POST.get("recurso")

            # Validaciones
            if not recurso_id:
                messages.error(request, "Debe seleccionar un recurso")
                return redirect("gestion_equipos:crear_miembro", equipo_id=equipo_id)

            # Verificar que el recurso no esté ya asignado
            if Miembro.objects.filter(idrecurso_id=recurso_id).exists():
                messages.error(request, "Este recurso ya está asignado a un equipo")
                return redirect("gestion_equipos:crear_miembro", equipo_id=equipo_id)

            # Crear miembro
            miembro = Miembro.objects.create(idequipo=equipo, idrecurso_id=recurso_id)

            messages.success(request, "Miembro agregado exitosamente")
            return redirect("gestion_equipos:gestionar_miembros", equipo_id=equipo_id)

        except Exception as e:
            messages.error(request, f"Error al agregar miembro: {str(e)}")
            return redirect("gestion_equipos:crear_miembro", equipo_id=equipo_id)

    # GET: Mostrar formulario
    context = {
        "equipo": equipo,
        "tipos_recurso": Tiporecurso.objects.all(),
        "recursos_disponibles": Recurso.objects.filter(miembro__isnull=True),
    }

    return render(request, "gestion_equipos/crear_miembro.html", context)


@login_required
def agregar_miembro(request, equipo_id):
    """Vista para agregar un nuevo miembro al equipo"""
    equipo = get_object_or_404(Equipo, idequipo=equipo_id)

    if request.method == "POST":
        try:
            tipo_recurso = request.POST.get("tipo_recurso")
            recurso_id = request.POST.get("recurso")

            # Validaciones
            if not recurso_id:
                messages.error(request, "Debe seleccionar un recurso")
                return redirect("gestion_equipos:agregar_miembro", equipo_id=equipo_id)

            # Verificar que el recurso no esté ya asignado
            if Miembro.objects.filter(idrecurso_id=recurso_id).exists():
                messages.error(request, "Este recurso ya está asignado a un equipo")
                return redirect("gestion_equipos:agregar_miembro", equipo_id=equipo_id)

            # Obtener el recurso
            recurso = get_object_or_404(Recurso, idrecurso=recurso_id)

            # Verificar que el tipo de recurso coincida
            if (
                tipo_recurso
                and str(recurso.idtiporecurso.idtiporecurso) != tipo_recurso
            ):
                messages.error(request, "El tipo de recurso seleccionado no coincide")
                return redirect("gestion_equipos:agregar_miembro", equipo_id=equipo_id)

            # Crear miembro
            miembro = Miembro.objects.create(idequipo=equipo, idrecurso=recurso)

            # Actualizar disponibilidad del recurso
            recurso.disponibilidad = False
            recurso.fechamodificacion = timezone.now()
            recurso.save()

            messages.success(
                request, f"Se agregó '{recurso.nombrerecurso}' al equipo exitosamente"
            )
            return redirect("gestion_equipos:gestionar_miembros", equipo_id=equipo_id)

        except Recurso.DoesNotExist:
            messages.error(request, "El recurso seleccionado no existe")
            return redirect("gestion_equipos:agregar_miembro", equipo_id=equipo_id)
        except Exception as e:
            messages.error(request, f"Error al agregar miembro: {str(e)}")
            return redirect("gestion_equipos:agregar_miembro", equipo_id=equipo_id)

    # GET: Mostrar formulario
    tipos_recurso = Tiporecurso.objects.all()
    recursos_disponibles = (
        Recurso.objects.filter(disponibilidad=True)
        .select_related("idtiporecurso", "recursohumano", "recursomaterial")
        .exclude(miembro__isnull=False)
    )

    context = {
        "equipo": equipo,
        "tipos_recurso": tipos_recurso,
        "recursos_disponibles": recursos_disponibles,
        "total_miembros": equipo.miembro_set.count(),
        "proyectos_activos": equipo.proyecto_set.filter(estado="En Progreso").count(),
    }

    return render(request, "gestion_equipos/agregar_miembro.html", context)


@login_required
def eliminar_miembro(request, miembro_id):
    """Vista para eliminar un miembro del equipo"""
    if request.method == "POST":
        try:
            miembro = get_object_or_404(Miembro, idmiembro=miembro_id)
            equipo_id = miembro.idequipo.idequipo

            # Actualizar disponibilidad del recurso
            recurso = miembro.idrecurso
            recurso.disponibilidad = True
            recurso.fechamodificacion = timezone.now()
            recurso.save()

            # Eliminar miembro
            miembro.delete()

            messages.success(request, "Miembro eliminado exitosamente")
            return redirect("gestion_equipos:gestionar_miembros", equipo_id=equipo_id)

        except Exception as e:
            messages.error(request, f"Error al eliminar miembro: {str(e)}")
            return redirect("gestion_equipos:index")

    return redirect("gestion_equipos:index")
