from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

from .models import IntegracionJira, JiraProjectMapping
from .jira_client import JiraClient
from dashboard.models import Proyecto, Tarea, Requerimiento

@login_required
def index(request):
    # Obtener configuraciones de integración del usuario actual
    jira_config = IntegracionJira.objects.filter(idusuario=request.user).first()
    
    context = {
        'jira_config': jira_config
    }
    
    return render(request, "integracion/index.html", context)

@login_required
@require_POST
def configurar_jira(request):
    """Configura o actualiza la integración con Jira"""
    try:
        data = json.loads(request.body)
        
        # Obtener o crear configuración
        jira_config, created = IntegracionJira.objects.get_or_create(
            idusuario=request.user,
            defaults={
                'url_servidor': data.get('url_servidor'),
                'api_key': data.get('api_key'),
                'usuario_jira': data.get('usuario_jira'),
                'frecuencia_sync': data.get('frecuencia_sync', 'manual'),
                'activo': True
            }
        )
        
        if not created:
            # Actualizar configuración existente
            jira_config.url_servidor = data.get('url_servidor')
            jira_config.api_key = data.get('api_key')
            jira_config.usuario_jira = data.get('usuario_jira')
            jira_config.frecuencia_sync = data.get('frecuencia_sync', 'manual')
            jira_config.save()
        
        # Probar conexión
        client = JiraClient(config=jira_config)
        success, message = client.test_connection()
        
        if success:
            return JsonResponse({'success': True, 'message': 'Configuración guardada correctamente'})
        else:
            return JsonResponse({
                'success': False, 
                'message': f'Error al conectar con Jira: {message}'
            }, status=400)
            
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@login_required
def listar_proyectos_jira(request):
    """Obtiene los proyectos de Jira para mapeo"""
    try:
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        jira_projects = client.get_projects()
        local_projects = Proyecto.objects.all()
        
        # Obtener mapeos existentes
        existing_mappings = JiraProjectMapping.objects.filter(
            integracion=jira_config
        ).values_list('proyecto_local_id', 'jira_project_key')
        
        mappings = {local_id: jira_key for local_id, jira_key in existing_mappings}
        
        jira_projects_data = [
            {'id': p.id, 'key': p.key, 'name': p.name} 
            for p in jira_projects
        ]
        
        local_projects_data = [
            {
                'id': p.idproyecto, 
                'name': p.nombreproyecto,
                'mapped_to': mappings.get(p.idproyecto, None)
            } 
            for p in local_projects
        ]
        
        return JsonResponse({
            'success': True,
            'jira_projects': jira_projects_data,
            'local_projects': local_projects_data
        })
        
    except IntegracionJira.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de Jira'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def mapear_proyecto(request):
    """Mapea un proyecto local con un proyecto de Jira"""
    try:
        data = json.loads(request.body)
        proyecto_local_id = data.get('proyecto_local_id')
        jira_project_key = data.get('jira_project_key')
        jira_project_id = data.get('jira_project_id')
        
        if not all([proyecto_local_id, jira_project_key, jira_project_id]):
            return JsonResponse({
                'success': False,
                'message': 'Faltan datos requeridos'
            }, status=400)
        
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        
        # Crear o actualizar mapeo
        JiraProjectMapping.objects.update_or_create(
            integracion=jira_config,
            proyecto_local_id=proyecto_local_id,
            defaults={
                'jira_project_id': jira_project_id,
                'jira_project_key': jira_project_key,
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Proyecto mapeado correctamente'
        })
        
    except IntegracionJira.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de Jira'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
@require_POST
def sincronizar_jira(request):
    """Inicia sincronización manual con Jira"""
    try:
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        
        # Verificar si hay proyectos mapeados
        mappings = JiraProjectMapping.objects.filter(integracion=jira_config)
        if not mappings.exists():
            return JsonResponse({
                'success': False,
                'message': 'No hay proyectos mapeados para sincronizar'
            }, status=400)
            
        # Verificar si hay tareas para sincronizar
        for mapping in mappings:
            reqs = Requerimiento.objects.filter(idproyecto__idproyecto=mapping.proyecto_local_id)
            tareas = Tarea.objects.filter(idrequerimiento__in=reqs)
            if tareas.count() == 0:
                return JsonResponse({
                    'success': False,
                    'message': f'El proyecto {mapping.proyecto_local_id} no tiene tareas para sincronizar'
                }, status=400)
        
        client = JiraClient(config=jira_config)
        client.sync_all_data()
        
        return JsonResponse({
            'success': True,
            'message': 'Sincronización completada correctamente'
        })
        
    except IntegracionJira.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de Jira'
        }, status=404)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error durante la sincronización: {str(e)}'
        }, status=500)
