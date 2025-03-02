from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Max, F
from django.http import JsonResponse
from django.db import transaction  # Añadir esta importación

from dashboard.models import (
    TipoTarea,
    Fase,
    TareaComun,
    TareaTareaComun,
    Tarea
)


# Vista principal de configuración de tareas
@login_required
def configuracion_tareas(request):
    """Vista principal para la configuración de tareas"""
    # Verificar si es admin
    is_admin = (
        request.user.is_staff
        or request.user.is_superuser
        or request.user.rol == "Administrador"
    )
    
    # Obtener estadísticas generales
    total_tipos_tarea = TipoTarea.objects.count()
    total_fases = Fase.objects.count()
    total_tareas_comunes = TareaComun.objects.count()
    
    # Tipos de tarea más utilizados
    tipos_tarea = TipoTarea.objects.annotate(
        num_tareas=Count('tarea')
    ).order_by('-num_tareas')[:5]
    
    # Fases ordenadas
    fases = Fase.objects.all().order_by('orden')
    
    # Tareas comunes más utilizadas (Nuevo)
    # Intentamos primero ordenarlas por uso (relaciones con tareas)
    tareas_comunes = TareaComun.objects.annotate(
        num_usos=Count('tareatareacomun')
    ).select_related('idtipotarea').order_by('-num_usos')[:5]
    
    # Si no hay relaciones, mostrar las más recientes
    if not tareas_comunes.exists() or all(t.num_usos == 0 for t in tareas_comunes):
        tareas_comunes = TareaComun.objects.all().select_related('idtipotarea').order_by('-fechacreacion')[:5]
    
    context = {
        "is_admin": is_admin,
        "total_tipos_tarea": total_tipos_tarea,
        "total_fases": total_fases,
        "total_tareas_comunes": total_tareas_comunes,
        "tipos_tarea": tipos_tarea,
        "fases": fases,
        "tareas_comunes": tareas_comunes,  # Nueva variable de contexto
    }
    
    return render(request, "gestion_tareas/configuracion/index.html", context)

# Vistas de Tipos de Tarea
@login_required
def lista_tipos_tarea(request):
    """Vista para listar tipos de tarea"""
    tipos_tarea = TipoTarea.objects.all().annotate(
        num_tareas=Count('tarea')
    ).order_by('nombre')
    
    context = {
        "tipos_tarea": tipos_tarea,
    }
    
    return render(request, "gestion_tareas/configuracion/tipos_tarea/lista.html", context)

@login_required
def crear_tipo_tarea(request):
    """Vista para crear un nuevo tipo de tarea"""
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:crear_tipo_tarea")
            
            TipoTarea.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                fechacreacion=timezone.now(),
            )
            
            messages.success(request, "Tipo de tarea creado exitosamente")
            return redirect("gestion_tareas:lista_tipos_tarea")
            
        except Exception as e:
            messages.error(request, f"Error al crear el tipo de tarea: {str(e)}")
            return redirect("gestion_tareas:crear_tipo_tarea")
    
    return render(request, "gestion_tareas/configuracion/tipos_tarea/crear.html")

@login_required
def editar_tipo_tarea(request, id):
    """Vista para editar un tipo de tarea"""
    tipo_tarea = get_object_or_404(TipoTarea, idtipotarea=id)
    
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:editar_tipo_tarea", id=id)
            
            tipo_tarea.nombre = nombre
            tipo_tarea.descripcion = descripcion
            tipo_tarea.save()
            
            messages.success(request, "Tipo de tarea actualizado exitosamente")
            return redirect("gestion_tareas:lista_tipos_tarea")
            
        except Exception as e:
            messages.error(request, f"Error al actualizar el tipo de tarea: {str(e)}")
            return redirect("gestion_tareas:editar_tipo_tarea", id=id)
    
    context = {
        "tipo_tarea": tipo_tarea,
    }
    
    return render(request, "gestion_tareas/configuracion/tipos_tarea/editar.html", context)

@login_required
def eliminar_tipo_tarea(request, id):
    """Vista para eliminar un tipo de tarea"""
    if request.method == "POST":
        try:
            tipo_tarea = get_object_or_404(TipoTarea, idtipotarea=id)
            
            # Verificar si hay tareas asociadas
            if Tarea.objects.filter(tipo_tarea=tipo_tarea).exists():
                messages.error(request, "No se puede eliminar el tipo de tarea porque hay tareas asociadas")
                return redirect("gestion_tareas:lista_tipos_tarea")
                
            tipo_tarea.delete()
            messages.success(request, "Tipo de tarea eliminado exitosamente")
            
        except Exception as e:
            messages.error(request, f"Error al eliminar el tipo de tarea: {str(e)}")
            
    return redirect("gestion_tareas:lista_tipos_tarea")

# Vistas de Fases
@login_required
def lista_fases(request):
    """Vista para listar fases"""
    fases = Fase.objects.all().order_by('orden')
    
    context = {
        "fases": fases,
    }
    
    return render(request, "gestion_tareas/configuracion/fases/lista.html", context)

@login_required
def crear_fase(request):
    """Vista para crear una nueva fase"""
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            
            # Obtener el orden seleccionado
            orden = int(request.POST.get("orden", 1))
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:crear_fase")
            
            # Desplazar fases existentes
            with transaction.atomic():
                # Obtener todas las fases con orden >= al nuevo orden y actualizar su orden
                Fase.objects.filter(orden__gte=orden).update(orden=F('orden') + 1)
                
                # Crear la nueva fase
                Fase.objects.create(
                    nombre=nombre,
                    descripcion=descripcion,
                    orden=orden,
                    fechacreacion=timezone.now(),
                )
            
            messages.success(request, "Fase creada exitosamente")
            return redirect("gestion_tareas:lista_fases")
            
        except Exception as e:
            messages.error(request, f"Error al crear la fase: {str(e)}")
            return redirect("gestion_tareas:crear_fase")
    
    # Preparar datos para el formulario
    fases = Fase.objects.all().order_by('orden')
    ultimo_orden = fases.aggregate(Max('orden'))['orden__max'] or 0
    siguiente_orden = ultimo_orden + 1
    
    # Crear lista de posiciones disponibles
    posiciones_disponibles = []
    
    # Añadir posiciones para insertar antes de cada fase existente
    for fase in fases:
        posiciones_disponibles.append({
            'orden': fase.orden,
            'fase': fase
        })
    
    # Añadir posición para insertar al final
    posiciones_disponibles.append({
        'orden': siguiente_orden,
        'fase': None
    })
    
    context = {
        "posiciones_disponibles": posiciones_disponibles,
        "siguiente_orden": siguiente_orden,
    }
    
    return render(request, "gestion_tareas/configuracion/fases/crear.html", context)

@login_required
def editar_fase(request, id):
    """Vista para editar una fase"""
    fase = get_object_or_404(Fase, idfase=id)
    
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            
            # Ya no permitimos editar el orden directamente
            # orden = int(request.POST.get("orden", fase.orden))
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:editar_fase", id=id)
            
            fase.nombre = nombre
            fase.descripcion = descripcion
            # fase.orden = orden  # Ya no cambiamos el orden
            fase.save()
            
            messages.success(request, "Fase actualizada exitosamente")
            return redirect("gestion_tareas:lista_fases")
            
        except Exception as e:
            messages.error(request, f"Error al actualizar la fase: {str(e)}")
            return redirect("gestion_tareas:editar_fase", id=id)
    
    context = {
        "fase": fase,
    }
    
    return render(request, "gestion_tareas/configuracion/fases/editar.html", context)

@login_required
def eliminar_fase(request, id):
    """Vista para eliminar una fase"""
    if request.method == "POST":
        try:
            fase = get_object_or_404(Fase, idfase=id)
            
            # Verificar si hay tareas asociadas
            if Tarea.objects.filter(fase=fase).exists():
                messages.error(request, "No se puede eliminar la fase porque hay tareas asociadas")
                return redirect("gestion_tareas:lista_fases")
            
            # Guardar el orden de la fase que vamos a eliminar
            orden_eliminado = fase.orden
            
            # Eliminar la fase y reorganizar los órdenes
            with transaction.atomic():
                # Primero eliminar la fase
                fase.delete()
                
                # Luego actualizar el orden de las fases posteriores
                # Primero mover a valores temporales altos para evitar conflictos de clave única
                fases_posteriores = Fase.objects.filter(orden__gt=orden_eliminado)
                
                # Asignar temporalmente órdenes muy altos
                for i, fase_posterior in enumerate(fases_posteriores):
                    fase_posterior.orden = 10000 + i
                    fase_posterior.save()
                
                # Ahora asignar los órdenes finales (decrementados)
                for i, fase_posterior in enumerate(fases_posteriores, start=orden_eliminado):
                    fase_posterior.orden = i
                    fase_posterior.save()
                
            messages.success(request, "Fase eliminada exitosamente y orden de fases reorganizado")
            
        except Exception as e:
            messages.error(request, f"Error al eliminar la fase: {str(e)}")
            
    return redirect("gestion_tareas:lista_fases")

@login_required
def actualizar_orden_fases(request):
    """Vista para actualizar el orden de las fases via AJAX"""
    if request.method == "POST":
        try:
            orden_fases = request.POST.getlist("orden[]")
            
            with transaction.atomic():
                # Primero actualizar todas las fases a un orden temporal muy alto para evitar conflictos de clave única
                for i, fase_id in enumerate(orden_fases):
                    fase = Fase.objects.get(idfase=int(fase_id))
                    fase.orden = 10000 + i
                    fase.save()
                
                # Luego actualizar a los valores finales
                for i, fase_id in enumerate(orden_fases, 1):
                    fase = Fase.objects.get(idfase=int(fase_id))
                    fase.orden = i
                    fase.save()
                
            return JsonResponse({"status": "success"})
            
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
            
    return JsonResponse({"status": "error", "message": "Método no permitido"})

# Vistas de Tareas Comunes
@login_required
def lista_tareas_comunes(request):
    """Vista para listar tareas comunes"""
    tareas_comunes = TareaComun.objects.all().select_related('idtipotarea').order_by('nombre')
    
    context = {
        "tareas_comunes": tareas_comunes,
    }
    
    return render(request, "gestion_tareas/configuracion/tareas_comunes/lista.html", context)

@login_required
def crear_tarea_comun(request):
    """Vista para crear una nueva tarea común"""
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            tipo_tarea_id = request.POST.get("tipo_tarea")
            tiempo_promedio = request.POST.get("tiempo_promedio") or None
            variabilidad_tiempo = request.POST.get("variabilidad_tiempo") or None
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:crear_tarea_comun")
            
            TareaComun.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                idtipotarea_id=tipo_tarea_id if tipo_tarea_id else None,
                tiempo_promedio=tiempo_promedio,
                variabilidad_tiempo=variabilidad_tiempo,
                fechacreacion=timezone.now(),
            )
            
            messages.success(request, "Tarea común creada exitosamente")
            return redirect("gestion_tareas:lista_tareas_comunes")
            
        except Exception as e:
            messages.error(request, f"Error al crear la tarea común: {str(e)}")
            return redirect("gestion_tareas:crear_tarea_comun")
    
    # Obtener tipos de tarea para el formulario
    tipos_tarea = TipoTarea.objects.all().order_by('nombre')
    
    context = {
        "tipos_tarea": tipos_tarea,
    }
    
    return render(request, "gestion_tareas/configuracion/tareas_comunes/crear.html", context)

@login_required
def editar_tarea_comun(request, id):
    """Vista para editar una tarea común"""
    tarea_comun = get_object_or_404(TareaComun, idtareacomun=id)
    
    if request.method == "POST":
        try:
            nombre = request.POST.get("nombre")
            descripcion = request.POST.get("descripcion", "")
            tipo_tarea_id = request.POST.get("tipo_tarea")
            tiempo_promedio = request.POST.get("tiempo_promedio") or None
            variabilidad_tiempo = request.POST.get("variabilidad_tiempo") or None
            
            if not nombre:
                messages.error(request, "El nombre es obligatorio")
                return redirect("gestion_tareas:editar_tarea_comun", id=id)
            
            tarea_comun.nombre = nombre
            tarea_comun.descripcion = descripcion
            tarea_comun.idtipotarea_id = tipo_tarea_id if tipo_tarea_id else None
            tarea_comun.tiempo_promedio = tiempo_promedio
            tarea_comun.variabilidad_tiempo = variabilidad_tiempo
            tarea_comun.save()
            
            messages.success(request, "Tarea común actualizada exitosamente")
            return redirect("gestion_tareas:lista_tareas_comunes")
            
        except Exception as e:
            messages.error(request, f"Error al actualizar la tarea común: {str(e)}")
            return redirect("gestion_tareas:editar_tarea_comun", id=id)
    
    # Obtener tipos de tarea para el formulario
    tipos_tarea = TipoTarea.objects.all().order_by('nombre')
    
    context = {
        "tarea_comun": tarea_comun,
        "tipos_tarea": tipos_tarea,
    }
    
    return render(request, "gestion_tareas/configuracion/tareas_comunes/editar.html", context)

@login_required
def eliminar_tarea_comun(request, id):
    """Vista para eliminar una tarea común"""
    if request.method == "POST":
        try:
            tarea_comun = get_object_or_404(TareaComun, idtareacomun=id)
            
            # Verificar si hay tareas relacionadas
            if TareaTareaComun.objects.filter(idtareacomun=tarea_comun).exists():
                messages.error(request, "No se puede eliminar la tarea común porque hay tareas asociadas")
                return redirect("gestion_tareas:lista_tareas_comunes")
                
            tarea_comun.delete()
            messages.success(request, "Tarea común eliminada exitosamente")
            
        except Exception as e:
            messages.error(request, f"Error al eliminar la tarea común: {str(e)}")
            
    return redirect("gestion_tareas:lista_tareas_comunes")
