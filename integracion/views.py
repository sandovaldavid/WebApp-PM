from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
import json

from .models import IntegracionJira, JiraProjectMapping, JiraUserMapping, JiraTaskMapping
from .jira_client import JiraClient
from dashboard.models import Proyecto, Tarea, Requerimiento, Usuario

@login_required
def index(request):
    # Obtener configuraciones de integración del usuario actual
    jira_config = IntegracionJira.objects.filter(idusuario=request.user).first()
    
    # Obtener estadísticas de la integración si existe configuración
    stats = None
    if jira_config:
        try:
            client = JiraClient(config=jira_config)
            
            # Obtener número de proyectos mapeados
            project_mappings = JiraProjectMapping.objects.filter(integracion=jira_config).count()
            
            # Obtener número de tareas mapeadas
            task_mappings = JiraTaskMapping.objects.filter(integracion=jira_config).count()
            
            # Obtener estado de salud
            health_status = client.check_integration_health()
            
            stats = {
                'projects_mapped': project_mappings,
                'tasks_mapped': task_mappings,
                'last_sync': jira_config.ultima_sincronizacion,
                'health_status': health_status.get('overall_status', 'unknown')
            }
        except Exception as e:
            stats = {'error': str(e)}
    
    context = {
        'jira_config': jira_config,
        'integration_stats': stats
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
                'activo': True,
                # Valores predeterminados para opciones adicionales
                'importar_issues': True,
                'exportar_tareas': True,
                'sync_comentarios': True,
                'sincronizar_adjuntos': False
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
@require_POST
def configuracion_avanzada_jira(request):
    """Actualiza configuraciones avanzadas para la integración de Jira"""
    try:
        data = json.loads(request.body)
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        
        # Actualizar configuraciones avanzadas
        jira_config.importar_issues = data.get('importar_issues', jira_config.importar_issues)
        jira_config.exportar_tareas = data.get('exportar_tareas', jira_config.exportar_tareas)
        jira_config.sync_comentarios = data.get('sync_comentarios', jira_config.sync_comentarios)
        jira_config.sincronizar_adjuntos = data.get('sincronizar_adjuntos', jira_config.sincronizar_adjuntos)
        
        jira_config.save()
        
        return JsonResponse({
            'success': True, 
            'message': 'Configuración avanzada actualizada correctamente'
        })
        
    except IntegracionJira.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'No hay configuración de Jira'
        }, status=404)
        
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
        
        # Verificar si hay tareas para sincronizar pero solo advertir, no bloquear
        proyectos_sin_tareas = []
        if jira_config.exportar_tareas:
            for mapping in mappings:
                reqs = Requerimiento.objects.filter(idproyecto__idproyecto=mapping.proyecto_local_id)
                tareas = Tarea.objects.filter(idrequerimiento__in=reqs)
                if tareas.count() == 0:
                    proyectos_sin_tareas.append(mapping.proyecto_local_id)
        
        client = JiraClient(config=jira_config)
        result = client.sync_all_data()
        
        if result:
            # Registrar actividad de sincronización
            try:
                from dashboard.models import Actividad
                mensaje = "Se realizó una sincronización manual con Jira."
                if proyectos_sin_tareas:
                    mensaje += f" Los proyectos {', '.join(map(str, proyectos_sin_tareas))} no tenían tareas para exportar."
                
                Actividad.objects.create(
                    nombre="Sincronización con Jira",
                    descripcion=mensaje,
                    idusuario=request.user,
                    accion="Sincronización",
                    es_automatica=False
                )
            except Exception as e:
                logger.error(f"Error al registrar actividad: {str(e)}")
            
            mensaje_respuesta = 'Sincronización completada correctamente'
            if proyectos_sin_tareas:
                mensaje_respuesta += f". Nota: Los proyectos {', '.join(map(str, proyectos_sin_tareas))} no tenían tareas para exportar, pero se importaron datos desde Jira si existían."
            
            return JsonResponse({
                'success': True,
                'message': mensaje_respuesta,
                'proyectos_sin_tareas': proyectos_sin_tareas
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Error durante la sincronización'
            }, status=500)
        
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

@login_required
def listar_usuarios_jira(request):
    """Lista usuarios de Jira y locales para mapeo"""
    try:
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        # Obtener usuarios locales
        local_users = Usuario.objects.all()
        
        # Intentar obtener usuarios de Jira (puede fallar si no hay permisos suficientes)
        try:
            # Modificar esta línea para usar un valor válido en lugar de cadena vacía
            jira_users = client.get_jira_users()  # Usaremos un método personalizado en JiraClient
            jira_users_data = [{
                'accountId': getattr(user, 'accountId', ''),
                'displayName': getattr(user, 'displayName', ''),
                'emailAddress': getattr(user, 'emailAddress', '')
            } for user in jira_users]
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'No se pudieron obtener usuarios de Jira: {str(e)}. Esto puede deberse a restricciones de permisos.'
            }, status=400)
        
        # Obtener mapeos existentes
        user_mappings = JiraUserMapping.objects.filter(integracion=jira_config)
        mapped_users = {
            m.usuario_local_id: {
                'jira_user_id': m.jira_user_id,
                'jira_user_name': m.jira_user_name
            } for m in user_mappings
        }
        
        # Preparar datos de usuarios locales
        local_users_data = [{
            'id': user.idusuario,
            'username': user.nombreusuario,
            'email': user.email,
            'role': user.rol,
            'mapped_to': mapped_users.get(user.idusuario, None)
        } for user in local_users]
        
        return JsonResponse({
            'success': True,
            'local_users': local_users_data,
            'jira_users': jira_users_data
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
def mapear_usuarios_jira(request):
    """Mapea usuarios locales con usuarios de Jira"""
    try:
        data = json.loads(request.body)
        user_mappings = data.get('mappings', [])
        
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        if not user_mappings:
            # Si no se proporcionaron mapeos manuales, intentar mapeo automático
            mappings_created = client.map_jira_users()
            
            return JsonResponse({
                'success': True,
                'message': f'Se mapearon automáticamente {mappings_created} usuarios',
                'mappings_created': mappings_created
            })
        
        # Procesar mapeos manuales
        for mapping in user_mappings:
            JiraUserMapping.objects.update_or_create(
                integracion=jira_config,
                usuario_local_id=mapping['local_user_id'],
                defaults={
                    'jira_user_id': mapping['jira_user_id'],
                    'jira_user_key': mapping.get('jira_user_key', ''),
                    'jira_user_name': mapping['jira_user_name']
                }
            )
        
        return JsonResponse({
            'success': True,
            'message': f'Se han creado/actualizado {len(user_mappings)} mapeos de usuarios'
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
def limpiar_mapeos_huerfanos(request):
    """Limpia mapeos huérfanos de la base de datos"""
    try:
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        result = client.clean_orphaned_mappings()
        
        if result.get('success', False):
            return JsonResponse({
                'success': True,
                'message': result.get('message', 'Limpieza completada'),
                'total_cleaned': result.get('total_cleaned', 0)
            })
        else:
            return JsonResponse({
                'success': False,
                'message': result.get('message', 'Error al limpiar mapeos')
            }, status=500)
        
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
def verificar_salud_integracion(request):
    """Verifica el estado de salud de la integración con Jira"""
    try:
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        health_report = client.check_integration_health()
        
        return JsonResponse({
            'success': True,
            'health_report': health_report
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
def generar_reporte_sincronizacion(request):
    """Genera un reporte completo de sincronización"""
    try:
        days = request.GET.get('days', 30)
        try:
            days = int(days)
        except ValueError:
            days = 30
            
        jira_config = IntegracionJira.objects.get(idusuario=request.user)
        client = JiraClient(config=jira_config)
        
        report = client.generate_sync_report(days_back=days)
        
        return JsonResponse({
            'success': True,
            'report': report
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
def diagnosticar_campos_jira(request):
    """Diagnóstico de campos disponibles en Jira para depuración"""
    try:
        jira_config = IntegracionJira.objects.filter(idusuario=request.user).first()
        
        if not jira_config:
            return JsonResponse({
                'success': False,
                'message': 'No hay configuración de Jira'
            }, status=404)
        
        # Importamos aquí para evitar dependencias circulares
        from .jira_field_inspector import JiraFieldInspector
        
        inspector = JiraFieldInspector(config=jira_config)
        project_key = request.GET.get('project')
        fields_info = inspector.get_available_fields_for_project(project_key)
        
        return JsonResponse({
            'success': True,
            'fields_info': fields_info
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@login_required
def project_mapping_template(request):
    """Vista para el componente de mapeo de proyectos"""
    return render(request, "integracion/components/project_mapping.html")

@login_required
def user_mapping_template(request):
    """Vista para el componente de mapeo de usuarios"""
    return render(request, "integracion/components/user_mapping.html")

@login_required
def health_check_template(request):
    """Vista para el componente de verificación de salud"""
    return render(request, "integracion/components/health_check.html")

@login_required
def sync_report_template(request):
    """Vista para el componente de reporte de sincronización"""
    return render(request, "integracion/components/sync_report.html")
