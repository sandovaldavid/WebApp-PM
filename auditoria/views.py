from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection, models
from dashboard.models import Usuario, Actividad, DetalleActividad, Alerta, ConfiguracionAuditoria
from django.db.models import Q, Count
from django.http import JsonResponse, HttpResponse
from django.core.paginator import Paginator

# Importar modelos disponibles para auditoría
from django.apps import apps


def registro_actividades(request):
    # Obtener filtros
    estado = request.GET.get("filtro", "")
    busqueda = request.GET.get("busqueda", "")

    # Query base
    actividades = Actividad.objects.all().order_by('-fechacreacion')

    # Aplicar filtros
    if estado:
        actividades = actividades.filter(accion=estado)
    if busqueda:
        actividades = actividades.filter(
            Q(idusuario__nombreusuario__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(accion__icontains=busqueda)
        )

    # Obtener tipos únicos de actividades para los filtros
    tipos_actividades = Actividad.objects.values_list('accion', flat=True).distinct()

    # Paginación
    paginator = Paginator(actividades, 10)  # 10 actividades por página
    page = request.GET.get("page", 1)
    actividades_paginadas = paginator.get_page(page)

    estadisticas = {
        "total_actividades": Actividad.objects.count(),
        "usuarios_activos": Usuario.objects.filter(is_active=True).count(),
        "alertas_activas": Alerta.objects.filter(activa=True).count(),
    }
    
    # Obtener usuarios más activos (con más actividades)
    usuarios_activos = (
        Usuario.objects.annotate(
            num_actividades=Count('actividad')
        ).order_by('-num_actividades')[:15]  # Mostrar los 15 usuarios más activos
    )
    
    datos_actividades_usuario = {
        "labels": [usuario.nombreusuario for usuario in usuarios_activos],
        "data": [usuario.num_actividades for usuario in usuarios_activos],
    }
    
    # Obtener todos los tipos de actividades para la gráfica
    tipos_actividades_count = (
        Actividad.objects.values('accion')
                       .annotate(total=Count('idactividad'))
                       .order_by('-total')
    )
    
    # Preparar datos para la gráfica
    datos_tipos_actividades = {
        "labels": [tipo['accion'] for tipo in tipos_actividades_count],
        "data": [tipo['total'] for tipo in tipos_actividades_count],
    }
    
    return render(
        request,
        "auditoria/registro_actividades.html",
        {
            "actividades": actividades_paginadas,
            "estadisticas": estadisticas,
            "datos_actividades_usuario": datos_actividades_usuario,
            "datos_tipos_actividades": datos_tipos_actividades,
            "filtros": {"busqueda": busqueda, "filtro": estado},
            "tipos_actividades": tipos_actividades,
        },
    )


@login_required
def filtrar_actividades(request):
    """Vista para filtrar actividades vía HTMX"""
    try:
        # Obtener filtros
        filtro = request.GET.get("filtro", "")
        busqueda = request.GET.get("busqueda", "")
        
        # Query base
        actividades = Actividad.objects.all().order_by('-fechacreacion')
        
        # Aplicar filtros
        if filtro:
            actividades = actividades.filter(accion=filtro)
        if busqueda:
            actividades = actividades.filter(
                Q(idusuario__nombreusuario__icontains=busqueda) | 
                Q(descripcion__icontains=busqueda) |
                Q(accion__icontains=busqueda)
            )
        
        # Paginación
        paginator = Paginator(actividades, 10)  # 10 actividades por página
        page = request.GET.get("page", 1)
        actividades_paginadas = paginator.get_page(page)
        
        context = {
            "actividades": actividades_paginadas,
            "filtro_activo": filtro,
        }
        
        return render(request, "auditoria/components/lista_actividades.html", context)
    
    except Exception as e:
        return HttpResponse(
            f'<div class="text-red-500 p-4">Error al filtrar actividades: {str(e)}</div>',
            status=500,
        )


# Para soporte AJAX de paginación
@login_required
def lista_actividades(request):
    """API para listar actividades con paginación para AJAX"""
    # Obtener filtros
    filtro = request.GET.get("filtro", "")
    busqueda = request.GET.get("busqueda", "")
    
    # Query base
    actividades = Actividad.objects.all().order_by('-fechacreacion')
    
    # Aplicar filtros
    if filtro:
        actividades = actividades.filter(accion=filtro)
    if busqueda:
        actividades = actividades.filter(
            Q(idusuario__nombreusuario__icontains=busqueda) | 
            Q(descripcion__icontains=busqueda) |
            Q(accion__icontains=busqueda)
        )
    
    # Paginación
    paginator = Paginator(actividades, 10)
    page = request.GET.get("page", 1)
    actividades_page = paginator.get_page(page)
    
    # Formatear actividades para JSON
    actividades_data = []
    for actividad in actividades_page:
        actividades_data.append({
            'idactividad': actividad.idactividad,
            'nombre': actividad.nombre,
            'descripcion': actividad.descripcion,
            'accion': actividad.accion,
            'fechacreacion': actividad.fechacreacion.strftime('%Y-%m-%d %H:%M:%S'),
            'es_automatica': actividad.es_automatica,
            'idusuario': {
                'idusuario': actividad.idusuario.idusuario,
                'nombreusuario': actividad.idusuario.nombreusuario
            }
        })
    
    return JsonResponse({
        'actividades': actividades_data,
        'current_page': actividades_page.number,
        'total_pages': paginator.num_pages,
        'has_previous': actividades_page.has_previous(),
        'has_next': actividades_page.has_next(),
        'total_count': paginator.count
    })


def intentos_acceso(request):
    intentos = []  # Consulta los intentos desde la base de datos.
    return render(request, "intentos_acceso.html", {"intentos": intentos})


def gestion_roles(request):
    usuarios = Usuario.objects.all()
    # roles = RolModuloAcceso.objects.all()
    return render(request, "gestion_roles.html", {"usuarios": usuarios, "roles": []})


def crear_actividad(request):
    usuarios = Usuario.objects.all()
    if request.method == "POST":
        try:
            # Procesar los datos del formulario manualmente
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            fechacreacion = request.POST.get('fechacreacion')
            idusuario = request.POST.get('idusuario')
            accion = request.POST.get('accion')
            
            # Validar datos
            if not nombre or not idusuario or not accion:
                messages.error(request, "Todos los campos requeridos deben ser completados.")
                return render(request, "auditoria/crear_actividad.html", {"usuarios": usuarios})
                
            # Crear la actividad
            usuario = Usuario.objects.get(idusuario=idusuario)
            actividad = Actividad.objects.create(
                nombre=nombre,
                descripcion=descripcion,
                idusuario=usuario,
                accion=accion,
                es_automatica=False
            )
            
            if fechacreacion:
                actividad.fechacreacion = fechacreacion
                actividad.save()
                
            messages.success(request, "Actividad creada exitosamente.")
            return redirect("auditoria:registro_actividades")
        except Exception as e:
            messages.error(request, f"Error al crear la actividad: {str(e)}")
            
    return render(request, "auditoria/crear_actividad.html", {"usuarios": usuarios})


def editar_actividad(request, id):
    actividad = get_object_or_404(Actividad, idactividad=id)
    usuarios = Usuario.objects.all()
    
    if request.method == "POST":
        try:
            # Procesar los datos del formulario manualmente
            nombre = request.POST.get('nombre')
            descripcion = request.POST.get('descripcion')
            fechacreacion = request.POST.get('fechacreacion')
            idusuario = request.POST.get('idusuario')
            accion = request.POST.get('accion')
            
            # Validar datos
            if not nombre or not idusuario or not accion:
                messages.error(request, "Todos los campos requeridos deben ser completados.")
                return render(request, "auditoria/editar_actividad.html", {"actividad": actividad, "usuarios": usuarios})
            
            # Actualizar la actividad
            usuario = Usuario.objects.get(idusuario=idusuario)
            actividad.nombre = nombre
            actividad.descripcion = descripcion
            actividad.idusuario = usuario
            actividad.accion = accion
            
            if fechacreacion:
                actividad.fechacreacion = fechacreacion
                
            actividad.save()
            messages.success(request, "Actividad actualizada exitosamente.")
            return redirect("auditoria:registro_actividades")
        except Exception as e:
            messages.error(request, f"Error al actualizar la actividad: {str(e)}")
            
    return render(
        request,
        "auditoria/editar_actividad.html",
        {"actividad": actividad, "usuarios": usuarios},
    )


def eliminar_actividad(request, id):
    if request.method == "POST":
        try:
            actividad = get_object_or_404(Actividad, idactividad=id)
            actividad.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    return JsonResponse({"success": False, "error": "Método no permitido."})


# Función para ver detalles de una actividad
@login_required
def detalle_actividad(request, id):
    actividad = get_object_or_404(Actividad, idactividad=id)
    detalles = DetalleActividad.objects.filter(idactividad=actividad)
    
    # Determinar nivel de detalle según la configuración
    nivel_detalle = 2  # Valor predeterminado - detallado
    
    # Si es actividad de modificación y hay entidad_tipo, buscar la configuración
    if actividad.accion == 'MODIFICACION' and actividad.entidad_tipo:
        config = ConfiguracionAuditoria.objects.filter(
            modelo=actividad.entidad_tipo,
            campo__isnull=True
        ).first()
        
        if config:
            nivel_detalle = config.nivel_detalle
    
    # Para nivel 1, no mostramos detalles (aunque existan)
    if nivel_detalle == 1:
        detalles_filtrados = []
    else:
        # Para nivel 2 y 3, mostramos todos los detalles
        detalles_filtrados = detalles
    
    # Si la actividad es de nivel 3, intentar obtener más información sobre la entidad
    entidad_relacionada = None
    if nivel_detalle == 3 and actividad.entidad_tipo and actividad.entidad_id:
        entidad_relacionada = obtener_entidad_relacionada(actividad.entidad_tipo, actividad.entidad_id)
    
    # Mejoramos la presentación de los detalles para campos con prefijo de modelo
    detalles_formateados = []
    for detalle in detalles_filtrados:
        nombre_campo = detalle.nombre_campo
        # Si el nombre del campo contiene un punto, es un campo de un modelo relacionado
        if '.' in nombre_campo:
            partes = nombre_campo.split('.')
            if len(partes) == 2:
                modelo, campo = partes
                # Formateamos el nombre para mostrar el modelo y campo
                detalle.nombre_campo = f"{modelo} - {campo}"
        detalles_formateados.append(detalle)
    
    return render(
        request, 
        'auditoria/detalle_actividad.html', 
        {
            'actividad': actividad,
            'detalles': detalles_formateados,  # Usamos la lista formateada
            'nivel_detalle': nivel_detalle,
            'entidad_relacionada': entidad_relacionada,
            'es_nivel_detallado': nivel_detalle >= 2
        }
    )

def obtener_entidad_relacionada(modelo, id):
    """
    Obtiene la entidad relacionada con la actividad para mostrar información adicional
    """
    try:
        # Importar los modelos necesarios (añade al inicio del archivo si prefieres)
        from dashboard.models import (
            Proyecto, Tarea, Recurso, Usuario, 
            Equipo, Requerimiento, Notificacion, Alerta  # Añadimos estos dos modelos
        )
        
        # Mapeo de nombres de modelos a clases reales
        model_map = {
            'Proyecto': Proyecto,
            'Tarea': Tarea,
            'Recurso': Recurso,
            'Usuario': Usuario,
            'Equipo': Equipo,
            'Requerimiento': Requerimiento,
            'Notificacion': Notificacion,  # Añadimos Notificacion
            'Alerta': Alerta,             # Añadimos Alerta
        }
        
        # Mapeo específico de nombres de campos de clave primaria
        pk_fields = {
            'Proyecto': 'idproyecto',
            'Tarea': 'idtarea',
            'Recurso': 'idrecurso',
            'Usuario': 'idusuario',
            'Equipo': 'idequipo',
            'Requerimiento': 'idrequerimiento',
            'Notificacion': 'idnotificacion',  # Añadimos campo PK
            'Alerta': 'idalerta',             # Añadimos campo PK
        }
        
        if modelo in model_map:
            # Usar el mapeo específico de pk en lugar de la generación dinámica
            pk_field = pk_fields.get(modelo)
            if not pk_field:
                print(f"No se encontró el campo de clave primaria para el modelo {modelo}")
                return None
                
            # Construir el filtro dinámicamente
            filter_kwargs = {pk_field: id}
            
            # Obtener la instancia
            instance = model_map[modelo].objects.filter(**filter_kwargs).first()
            print(f"Buscando {modelo} con {pk_field}={id}: {'Encontrado' if instance else 'No encontrado'}")
            return instance
    except Exception as e:
        print(f"Error al obtener entidad relacionada: {e}")
        import traceback
        traceback.print_exc()
    
    return None

# Funciones para gestionar las configuraciones de auditoría
@login_required
def configuracion_auditoria(request):
    configuraciones = ConfiguracionAuditoria.objects.all()
    
    # Obtener configuración de navegación
    from dashboard.models import ConfiguracionGeneralAuditoria
    navegacion_config = ConfiguracionGeneralAuditoria.objects.filter(nombre="registrar_navegacion").first()
    navegacion_habilitada = True  # Valor predeterminado
    if navegacion_config:
        navegacion_habilitada = navegacion_config.valor.lower() in ('true', '1', 'yes', 'si')

    # Obtener todos los modelos de la aplicación
    app_models = []
    for app_config in apps.get_app_configs():
        for model in app_config.get_models():
            # Excluir algunos modelos del sistema Django
            if model.__name__ not in ['Session', 'LogEntry', 'ContentType', 'Permission']:
                app_models.append(model.__name__)
    
    app_models.sort()  # Ordenar alfabéticamente
    
    return render(request, 'auditoria/configuracion_auditoria.html', {
        'configuraciones': configuraciones,
        'available_models': app_models,
        'navegacion_habilitada': navegacion_habilitada
    })


@login_required
def crear_configuracion(request):
    if request.method == 'POST':
        try:
            modelo = request.POST.get('modelo')
            campo = request.POST.get('campo', None)
            if (campo == ''):
                campo = None
                
            auditar_crear = 'auditar_crear' in request.POST
            auditar_modificar = 'auditar_modificar' in request.POST
            auditar_eliminar = 'auditar_eliminar' in request.POST
            nivel_detalle = int(request.POST.get('nivel_detalle', 1))
            
            # Validar datos
            if not modelo:
                messages.error(request, "Debe seleccionar un modelo para auditar.")
                return redirect('auditoria:configuracion_auditoria')
                
            # Comprobar si ya existe esta configuración
            existing_config = ConfiguracionAuditoria.objects.filter(modelo=modelo, campo=campo).first()
            if existing_config:
                messages.error(request, f"Ya existe una configuración para {modelo}" + 
                              (f" campo {campo}" if campo else ""))
                return redirect('auditoria:configuracion_auditoria')
                
            # Crear la configuración
            ConfiguracionAuditoria.objects.create(
                modelo=modelo,
                campo=campo,
                auditar_crear=auditar_crear,
                auditar_modificar=auditar_modificar,
                auditar_eliminar=auditar_eliminar,
                nivel_detalle=nivel_detalle
            )
            
            messages.success(request, "Configuración creada exitosamente.")
            
        except Exception as e:
            messages.error(request, f"Error al crear la configuración: {str(e)}")
            
    return redirect('auditoria:configuracion_auditoria')


@login_required
def editar_configuracion(request, id):
    configuracion = get_object_or_404(ConfiguracionAuditoria, idconfiguracion=id)
    
    if request.method == 'POST':
        try:
            # Actualizar la configuración
            configuracion.auditar_crear = 'auditar_crear' in request.POST
            configuracion.auditar_modificar = 'auditar_modificar' in request.POST
            configuracion.auditar_eliminar = 'auditar_eliminar' in request.POST
            configuracion.nivel_detalle = int(request.POST.get('nivel_detalle', 1))
            
            configuracion.save()
            messages.success(request, "Configuración actualizada exitosamente.")
            return redirect('auditoria:configuracion_auditoria')
            
        except Exception as e:
            messages.error(request, f"Error al actualizar la configuración: {str(e)}")
    
    return render(request, 'auditoria/editar_configuracion.html', {
        'configuracion': configuracion
    })


@login_required
def eliminar_configuracion(request, id):
    if request.method == 'POST':
        try:
            configuracion = get_object_or_404(ConfiguracionAuditoria, idconfiguracion=id)
            configuracion.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
            
    return JsonResponse({"success": False, "error": "Método no permitido."})


@login_required
def actualizar_config_navegacion(request):
    """Actualiza la configuración de registro de navegación"""
    if request.method == 'POST':
        try:
            # Verificar si hay un valor explícito en el campo registrar_navegacion
            valor_explicito = request.POST.get('registrar_navegacion')
            if valor_explicito is not None:
                if valor_explicito.lower() == 'true':
                    registrar_navegacion = True
                elif valor_explicito.lower() == 'false':
                    registrar_navegacion = False
                else:
                    # Si no es true/false explícito, usar la presencia del campo para determinar el valor
                    registrar_navegacion = 'registrar_navegacion' in request.POST
            else:
                # Sin valor explícito, usar presencia del campo
                registrar_navegacion = 'registrar_navegacion' in request.POST
            
            # Obtener o crear la configuración
            from dashboard.models import ConfiguracionGeneralAuditoria
            config, created = ConfiguracionGeneralAuditoria.objects.get_or_create(
                nombre="registrar_navegacion",
                defaults={
                    'valor': 'true' if registrar_navegacion else 'false',
                    'descripcion': 'Determina si se registra la navegación de los usuarios'
                }
            )
            
            # Si ya existía, actualizar el valor
            if not created:
                config.valor = 'true' if registrar_navegacion else 'false'
                config.save()
            
            messages.success(request, "Configuración de navegación actualizada con éxito")
        except Exception as e:
            messages.error(request, f"Error al actualizar configuración: {str(e)}")
    
    # Determinar de dónde vino la solicitud para redirigir correctamente
    referer = request.META.get('HTTP_REFERER', '')
    if 'configuracion-global' in referer:
        return redirect('auditoria:configuracion_global_auditoria')
    else:
        return redirect('auditoria:configuracion_auditoria')

# Funciones para la configuración global de auditoría
@login_required
def configuracion_global_auditoria(request):
    from dashboard.models import ConfiguracionGeneralAuditoria
    configuraciones = ConfiguracionGeneralAuditoria.objects.all()
    
    # Configuraciones sugeridas
    configuraciones_sugeridas = [
        {"nombre": "registrar_navegacion", "valor": "true", "descripcion": "Determina si se registran las actividades de navegación"},
        {"nombre": "periodo_retencion_logs", "valor": "90", "descripcion": "Días que se conservan los logs antes de eliminarlos"},
        {"nombre": "limite_registros_diarios", "valor": "10000", "descripcion": "Número máximo de registros de auditoría por día"},
        {"nombre": "nivel_detalle_global", "valor": "2", "descripcion": "Nivel de detalle predeterminado para todas las auditorías"},
        {"nombre": "ips_excluidas", "valor": "127.0.0.1,192.168.1.5", "descripcion": "IPs que no se auditan (separadas por comas)"}
    ]
    
    # Filtrar las configuraciones sugeridas que no existan ya
    nombres_existentes = set(configuraciones.values_list('nombre', flat=True))
    sugerencias_filtradas = [cfg for cfg in configuraciones_sugeridas if cfg["nombre"] not in nombres_existentes]
    
    return render(request, 'auditoria/configuracion_global_auditoria.html', {
        'configuraciones': configuraciones,
        'configuraciones_sugeridas': sugerencias_filtradas
    })

@login_required
def crear_configuracion_global(request):
    if request.method == 'POST':
        try:
            from dashboard.models import ConfiguracionGeneralAuditoria
            
            nombre = request.POST.get('nombre')
            valor = request.POST.get('valor')
            descripcion = request.POST.get('descripcion')
            
            # Validar datos
            if not nombre or not valor:
                messages.error(request, "El nombre y valor son obligatorios.")
                return redirect('auditoria:configuracion_global_auditoria')
            
            # Verificar si ya existe
            if ConfiguracionGeneralAuditoria.objects.filter(nombre=nombre).exists():
                messages.error(request, f"Ya existe una configuración con el nombre '{nombre}'.")
                return redirect('auditoria:configuracion_global_auditoria')
            
            # Crear la configuración
            ConfiguracionGeneralAuditoria.objects.create(
                nombre=nombre,
                valor=valor,
                descripcion=descripcion
            )
            
            messages.success(request, "Configuración global creada exitosamente.")
        except Exception as e:
            messages.error(request, f"Error al crear la configuración: {str(e)}")
        
    return redirect('auditoria:configuracion_global_auditoria')

@login_required
def editar_configuracion_global(request, id):
    from dashboard.models import ConfiguracionGeneralAuditoria
    configuracion = get_object_or_404(ConfiguracionGeneralAuditoria, idconfiguracion=id)
    
    if request.method == 'POST':
        try:
            valor = request.POST.get('valor')
            descripcion = request.POST.get('descripcion')
            
            if not valor:
                messages.error(request, "El valor es obligatorio.")
                return render(request, 'auditoria/editar_configuracion_global.html', {'configuracion': configuracion})
            
            configuracion.valor = valor
            configuracion.descripcion = descripcion
            configuracion.save()
            
            messages.success(request, "Configuración global actualizada exitosamente.")
            return redirect('auditoria:configuracion_global_auditoria')
        except Exception as e:
            messages.error(request, f"Error al actualizar la configuración: {str(e)}")
    
    return render(request, 'auditoria/editar_configuracion_global.html', {
        'configuracion': configuracion
    })

@login_required
def eliminar_configuracion_global(request, id):
    if request.method == 'POST':
        try:
            from dashboard.models import ConfiguracionGeneralAuditoria
            configuracion = get_object_or_404(ConfiguracionGeneralAuditoria, idconfiguracion=id)
            configuracion.delete()
            return JsonResponse({"success": True})
        except Exception as e:
            return JsonResponse({"success": False, "error": str(e)})
    
    return JsonResponse({"success": False, "error": "Método no permitido."})


