import logging
from jira import JIRA
from django.utils import timezone
from django.conf import settings
from django.db import transaction
from django.db.models import Q

from .models import (
    IntegracionJira, JiraProjectMapping, JiraTaskMapping, 
    JiraUserMapping, JiraComentarioMapping
)
from dashboard.models import (
    Proyecto, Tarea, Requerimiento, Usuario, Actividad, 
    DetalleActividad, Recurso, Recursohumano, Tarearecurso
)

logger = logging.getLogger(__name__)

class JiraClient:
    def __init__(self, integracion_id=None, config=None):
        if integracion_id:
            try:
                self.config = IntegracionJira.objects.get(pk=integracion_id)
            except IntegracionJira.DoesNotExist:
                raise ValueError(f"No existe configuración de Jira con ID {integracion_id}")
        elif config:
            self.config = config
        else:
            raise ValueError("Se requiere ID de integración o configuración")
            
        self.jira = self._connect_to_jira()
        
        # Mapeo de estados entre sistemas
        self.estado_jira_to_local = {
            'To Do': 'Pendiente',
            'In Progress': 'En Progreso',
            'In Review': 'En Revisión',
            'Done': 'Completada',
            'Canceled': 'Cancelada',
        }
        
        self.estado_local_to_jira = {v: k for k, v in self.estado_jira_to_local.items()}
        
        # Mapeo de prioridades
        self.prioridad_jira_to_local = {
            'Highest': 5,
            'High': 4,
            'Medium': 3,
            'Low': 2,
            'Lowest': 1
        }
        
        self.prioridad_local_to_jira = {
            5: 'Highest',
            4: 'High',
            3: 'Medium',
            2: 'Low',
            1: 'Lowest'
        }
        
    def _connect_to_jira(self):
        """Establece conexión con Jira usando la configuración guardada"""
        try:
            options = {'server': self.config.url_servidor}
            return JIRA(options, basic_auth=(self.config.usuario_jira, self.config.api_key))
        except Exception as e:
            logger.error(f"Error conectando a Jira: {str(e)}")
            raise ConnectionError(f"No se pudo conectar a Jira: {str(e)}")
    
    def test_connection(self):
        """Prueba la conexión a Jira"""
        try:
            self.jira.projects()
            return True, "Conexión exitosa"
        except Exception as e:
            return False, str(e)
    
    def get_projects(self):
        """Obtiene proyectos de Jira"""
        try:
            return self.jira.projects()
        except Exception as e:
            logger.error(f"Error al obtener proyectos: {str(e)}")
            return []
    
    def get_issues(self, project_key, updated_since=None, max_results=500):
        """Obtiene issues de un proyecto específico"""
        try:
            jql = f'project={project_key}'
            
            # Si hay fecha de última sincronización, solo traer actualizados desde entonces
            if updated_since:
                # Formatear fecha para JQL
                date_str = updated_since.strftime('%Y-%m-%d %H:%M')
                jql += f' AND updated >= "{date_str}"'
                
            # Obtener todos los issues paginando
            all_issues = []
            start_at = 0
            
            while True:
                issues_batch = self.jira.search_issues(jql, startAt=start_at, maxResults=max_results)
                all_issues.extend(issues_batch)
                
                if len(issues_batch) < max_results:
                    break
                    
                start_at += max_results
                
            return all_issues
            
        except Exception as e:
            logger.error(f"Error al obtener issues: {str(e)}")
            return []
    
    def get_issue_comments(self, issue_key):
        """Obtiene comentarios de un issue específico"""
        try:
            issue = self.jira.issue(issue_key)
            return self.jira.comments(issue)
        except Exception as e:
            logger.error(f"Error al obtener comentarios del issue {issue_key}: {str(e)}")
            return []
            
    def add_comment_to_issue(self, issue_key, comment_text):
        """Agrega un comentario a un issue de Jira"""
        try:
            issue = self.jira.issue(issue_key)
            return self.jira.add_comment(issue, comment_text)
        except Exception as e:
            logger.error(f"Error al añadir comentario al issue {issue_key}: {str(e)}")
            return None
            
    def get_issue_with_fields(self, issue_key):
        """Obtiene un issue con todos sus campos"""
        try:
            return self.jira.issue(issue_key, expand='changelog,comments,transitions')
        except Exception as e:
            logger.error(f"Error al obtener issue {issue_key}: {str(e)}")
            return None
    
    def create_issue(self, tarea):
        """Crea un issue en Jira basado en una tarea local"""
        try:
            # Obtener el mapeo del proyecto
            proyecto_local = tarea.idrequerimiento.idproyecto
            try:
                project_mapping = JiraProjectMapping.objects.get(
                    integracion=self.config,
                    proyecto_local_id=proyecto_local.idproyecto
                )
            except JiraProjectMapping.DoesNotExist:
                logger.error(f"No hay mapeo para el proyecto {proyecto_local.idproyecto}")
                return None
            
            # Solo usar campos básicos obligatorios
            issue_dict = {
                'project': {'key': project_mapping.jira_project_key},
                'summary': tarea.nombretarea,
                'description': tarea.descripcion or 'Sin descripción',
                'issuetype': {'name': 'Task'},
            }
            
            # Crear issue con solo los campos básicos
            issue = self.jira.create_issue(fields=issue_dict)
            
            # Guardar mapeo
            JiraTaskMapping.objects.create(
                integracion=self.config,
                tarea_local_id=tarea.idtarea,
                jira_issue_id=issue.id,
                jira_issue_key=issue.key
            )
            
            logger.info(f"Tarea {tarea.idtarea} creada exitosamente en Jira como {issue.key}")
            return issue
        except Exception as e:
            logger.error(f"Error al crear issue en Jira: {str(e)}")
            return None
    
    def update_issue(self, tarea):
        """Actualiza un issue en Jira basado en cambios locales"""
        try:
            # Obtener el mapeo de la tarea
            try:
                task_mapping = JiraTaskMapping.objects.get(
                    integracion=self.config,
                    tarea_local_id=tarea.idtarea
                )
            except JiraTaskMapping.DoesNotExist:
                logger.error(f"No hay mapeo para la tarea {tarea.idtarea}")
                return self.create_issue(tarea)
            
            # Obtener el issue de Jira
            issue = self.jira.issue(task_mapping.jira_issue_key)
            
            # Actualizar solo campos básicos permitidos
            update_dict = {}
            
            if issue.fields.summary != tarea.nombretarea:
                update_dict['summary'] = tarea.nombretarea
                
            if getattr(issue.fields, 'description', '') != tarea.descripcion:
                update_dict['description'] = tarea.descripcion or 'Sin descripción'
            
            # Aplicar actualizaciones de campos básicos si hay cambios
            if update_dict:
                issue.update(fields=update_dict)
                logger.info(f"Campos básicos actualizados para la tarea {tarea.idtarea} en Jira")
            
            # Actualizar estado mediante transición (esto funciona separado del update de campos)
            if tarea.estado:
                jira_status = self.estado_local_to_jira.get(tarea.estado, 'To Do')
                self._update_issue_status(issue, jira_status)
            
            # Sincronizar comentarios si está activado
            if self.config.sync_comentarios:
                self._sync_comments_to_jira(tarea, task_mapping.jira_issue_key)
            
            return issue
        except Exception as e:
            logger.error(f"Error al actualizar issue en Jira: {str(e)}")
            return None
    
    def _sync_comments_to_jira(self, tarea, jira_issue_key):
        """Sincroniza comentarios de una tarea local hacia Jira"""
        try:
            # Obtener actividades/comentarios de la tarea local que no están en Jira
            activities = Actividad.objects.filter(
                entidad_tipo='Tarea',
                entidad_id=tarea.idtarea,
                descripcion__isnull=False
            ).exclude(
                idactividad__in=JiraComentarioMapping.objects.filter(
                    integracion=self.config
                ).values_list('actividad_local_id', flat=True)
            )
            
            for actividad in activities:
                # Crear comentario en Jira
                comment_text = f"{actividad.idusuario.nombreusuario}: {actividad.descripcion}"
                comment = self.add_comment_to_issue(jira_issue_key, comment_text)
                
                if comment:
                    # Guardar mapeo
                    JiraComentarioMapping.objects.create(
                        integracion=self.config,
                        actividad_local_id=actividad.idactividad,
                        jira_comment_id=comment.id,
                        jira_issue_key=jira_issue_key
                    )
        except Exception as e:
            logger.error(f"Error al sincronizar comentarios a Jira: {str(e)}")
    
    def _map_status_to_jira(self, estado_local):
        """Mapea estados locales a estados de Jira"""
        return self.estado_local_to_jira.get(estado_local, 'To Do')
    
    def _update_issue_status(self, issue, target_status):
        """Intenta actualizar el estado del issue usando transiciones"""
        try:
            # Primero verificamos el estado actual
            current_status = issue.fields.status.name
            if current_status == target_status:
                return True  # Ya está en el estado deseado
                
            # Obtener transiciones disponibles
            transitions = self.jira.transitions(issue)
            available_transitions = [t['name'] for t in transitions]
            logger.info(f"Transiciones disponibles para {issue.key}: {available_transitions}")
            
            # Buscar la transición adecuada
            transition_id = None
            for t in transitions:
                if (t['name'].lower() == target_status.lower() or 
                    t['to']['name'].lower() == target_status.lower()):
                    transition_id = t['id']
                    break
            
            if transition_id:
                self.jira.transition_issue(issue, transition_id)
                logger.info(f"Issue {issue.key} transicionado a {target_status}")
                return True
            else:
                # No mostrar como error, solo como advertencia
                logger.warning(f"No se encontró transición a estado {target_status} para el issue {issue.key}")
                return False
                    
        except Exception as e:
            logger.error(f"Error al actualizar estado en Jira: {str(e)}")
            return False
    
    def sync_all_data(self):
        """Sincroniza datos bidireccionalmente entre la aplicación local y Jira"""
        try:
            logger.info("Iniciando sincronización completa con Jira...")

            # SOLUCIÓN: Refrescar la configuración de la base de datos para capturar
            # nuevos mapeos de proyectos que se hayan creado recientemente
            self.config.refresh_from_db()
            
            # Primero importar de Jira a local si está activada esta opción
            if hasattr(self.config, 'importar_issues') and self.config.importar_issues:
                logger.info("Importando datos desde Jira...")
                self.sync_from_jira()
            
            # Luego exportar de local a Jira si está activada esta opción
            if not hasattr(self.config, 'exportar_tareas') or self.config.exportar_tareas:
                logger.info("Exportando datos a Jira...")
                self.sync_to_jira()
                
            # Actualizar timestamp de última sincronización
            self.config.ultima_sincronizacion = timezone.now()
            self.config.save()
            
            logger.info("Sincronización completada con éxito")
            return True
            
        except Exception as e:
            logger.error(f"Error en la sincronización: {str(e)}")
            return False
    
    def sync_from_jira(self):
        """Importa datos desde Jira a la aplicación local"""
        try:
            # Obtener proyectos mapeados
            project_mappings = JiraProjectMapping.objects.filter(integracion=self.config)
            
            if not project_mappings.exists():
                logger.warning("No hay proyectos mapeados para importar desde Jira")
                return
                
            # Fecha desde la que sincronizar (última sincronización o 30 días atrás)
            sync_since = self.config.ultima_sincronizacion or (
                timezone.now() - timezone.timedelta(days=30)
            )
            
            total_issues_procesados = 0
            total_comentarios_procesados = 0
            
            for mapping in project_mappings:
                logger.info(f"Importando issues del proyecto Jira {mapping.jira_project_key}")
                
                # Obtener issues de Jira para este proyecto
                issues = self.get_issues(
                    mapping.jira_project_key,
                    updated_since=sync_since
                )
                
                if not issues:
                    logger.info(f"No hay issues para importar del proyecto {mapping.jira_project_key}")
                    continue
                    
                logger.info(f"Se encontraron {len(issues)} issues para importar")
                
                # Obtener el proyecto local correspondiente
                try:
                    proyecto_local = Proyecto.objects.get(idproyecto=mapping.proyecto_local_id)
                except Proyecto.DoesNotExist:
                    logger.error(f"No existe el proyecto local con ID {mapping.proyecto_local_id}")
                    continue
                    
                # Buscar o crear un requerimiento genérico para el proyecto
                requerimiento_default, created = Requerimiento.objects.get_or_create(
                    idproyecto=proyecto_local,
                    nombre="Integración Jira",  # Añadir este criterio para identificación única
                    defaults={
                        'descripcion': f"Requerimiento para integración con Jira ({mapping.jira_project_key})",
                        'fechacreacion': timezone.now()
                    }
                )
                
                # Procesar cada issue
                for issue in issues:
                    self._import_issue(issue, proyecto_local, requerimiento_default)
                    total_issues_procesados += 1
                    
                    # Importar comentarios si está activado
                    if hasattr(self.config, 'sync_comentarios') and self.config.sync_comentarios:
                        comentarios_importados = self._import_issue_comments(issue)
                        total_comentarios_procesados += comentarios_importados
            
            logger.info(f"Importación completada: {total_issues_procesados} issues y {total_comentarios_procesados} comentarios procesados")
            return True
                    
        except Exception as e:
            logger.error(f"Error al importar desde Jira: {str(e)}")
            return False
    
    def _import_issue(self, issue, proyecto_local, requerimiento_default):
        """Importa un issue de Jira como tarea local"""
        try:
            # Verificar si ya existe mapeo para este issue
            task_mapping = JiraTaskMapping.objects.filter(
                integracion=self.config,
                jira_issue_id=issue.id
            ).first()
            
            # Mapear datos de Jira a formato local
            datos_tarea = {
                'nombretarea': issue.fields.summary,
                'descripcion': getattr(issue.fields, 'description', '') or '',
                'estado': self.estado_jira_to_local.get(
                    issue.fields.status.name,
                    'Pendiente'  # Estado por defecto
                )
            }
            
            # Mapear prioridad si existe
            if hasattr(issue.fields, 'priority') and issue.fields.priority:
                datos_tarea['prioridad'] = self.prioridad_jira_to_local.get(
                    issue.fields.priority.name,
                    3  # Prioridad media por defecto
                )
                
            # Mapear fechas si existen
            if hasattr(issue.fields, 'duedate') and issue.fields.duedate:
                from datetime import datetime
                try:
                    datos_tarea['fechainicio'] = datetime.strptime(
                        issue.fields.duedate, 
                        '%Y-%m-%d'
                    ).date()
                except (ValueError, TypeError):
                    pass
            
            # Si ya existe la tarea, actualizarla; si no, crearla
            if task_mapping:
                try:
                    tarea_local = Tarea.objects.get(idtarea=task_mapping.tarea_local_id)
                    
                    # Actualizar campos
                    for key, value in datos_tarea.items():
                        setattr(tarea_local, key, value)
                    
                    tarea_local.fechamodificacion = timezone.now()
                    tarea_local.save()
                    
                    logger.info(f"Actualizada tarea local ID {tarea_local.idtarea} desde issue {issue.key}")
                    return tarea_local
                    
                except Tarea.DoesNotExist:
                    # El mapeo existe pero la tarea no, eliminar mapeo
                    task_mapping.delete()
                    task_mapping = None
            
            if not task_mapping:
                # Crear nueva tarea local
                datos_tarea.update({
                    'idrequerimiento': requerimiento_default,
                    'fechacreacion': timezone.now(),
                    'fechamodificacion': timezone.now()
                })
                
                tarea_local = Tarea.objects.create(**datos_tarea)
                
                # Crear nuevo mapeo
                JiraTaskMapping.objects.create(
                    integracion=self.config,
                    tarea_local_id=tarea_local.idtarea,
                    jira_issue_id=issue.id,
                    jira_issue_key=issue.key
                )
                
                logger.info(f"Creada tarea local ID {tarea_local.idtarea} desde issue {issue.key}")
                
                # Registrar actividad
                self._registrar_actividad_importacion(tarea_local, issue.key)
                
                return tarea_local
                
        except Exception as e:
            logger.error(f"Error al importar issue {issue.key}: {str(e)}")
            return None
    
    def _import_issue_comments(self, issue):
        """Importa comentarios de un issue como actividades"""
        try:
            # Obtener mapeo de tarea
            task_mapping = JiraTaskMapping.objects.filter(
                integracion=self.config,
                jira_issue_id=issue.id
            ).first()
            
            if not task_mapping:
                logger.warning(f"No hay tarea local mapeada para el issue {issue.key}, no se importarán comentarios")
                return 0
                
            # Obtener comentarios del issue
            comments = self.get_issue_comments(issue.key)
            if not comments:
                return 0
                
            # Obtener IDs de comentarios ya importados
            imported_comment_ids = set(JiraComentarioMapping.objects.filter(
                integracion=self.config,
                jira_issue_key=issue.key
            ).values_list('jira_comment_id', flat=True))
            
            # Filtrar solo comentarios nuevos
            new_comments = [c for c in comments if c.id not in imported_comment_ids]
            
            if not new_comments:
                return 0
            
            comentarios_importados = 0
            
            # Obtener la tarea local
            try:
                tarea_local = Tarea.objects.get(idtarea=task_mapping.tarea_local_id)
            except Tarea.DoesNotExist:
                logger.error(f"No existe la tarea local con ID {task_mapping.tarea_local_id}")
                return 0
            
            # Obtener usuario por defecto para los comentarios (admin o el que configura la integración)
            usuario_comentarios = self.config.idusuario
            
            # Importar cada comentario nuevo
            for comment in new_comments:
                # Crear actividad (comentario) en el sistema local
                actividad = Actividad.objects.create(
                    nombre=f"Comentario importado de Jira",
                    descripcion=comment.body,
                    idusuario=usuario_comentarios,
                    accion="Comentario",
                    entidad_tipo="Tarea",
                    entidad_id=tarea_local.idtarea,
                    es_automatica=True
                )
                
                # Guardar mapeo del comentario
                JiraComentarioMapping.objects.create(
                    integracion=self.config,
                    actividad_local_id=actividad.idactividad,
                    jira_comment_id=comment.id,
                    jira_issue_key=issue.key
                )
                
                comentarios_importados += 1
            
            return comentarios_importados
                
        except Exception as e:
            logger.error(f"Error al importar comentarios del issue {issue.key}: {str(e)}")
            return 0
    
    def _registrar_actividad_importacion(self, tarea, jira_key):
        """Registra una actividad cuando se importa una tarea desde Jira"""
        try:
            Actividad.objects.create(
                nombre=f"Tarea importada desde Jira",
                descripcion=f"Esta tarea fue importada desde el issue {jira_key} en Jira",
                idusuario=self.config.idusuario,
                accion="Importación",
                entidad_tipo="Tarea",
                entidad_id=tarea.idtarea,
                es_automatica=True
            )
        except Exception as e:
            logger.warning(f"No se pudo registrar actividad de importación: {str(e)}")
    
    def sync_to_jira(self):
        """Exporta datos desde la aplicación local a Jira"""
        try:
            logger.info("Iniciando sincronización hacia Jira")
            
            # Para cada proyecto mapeado
            project_mappings = JiraProjectMapping.objects.filter(integracion=self.config)
            
            if not project_mappings.exists():
                logger.warning("No hay proyectos mapeados para exportar a Jira")
                return
            
            total_tareas_creadas = 0
            total_tareas_actualizadas = 0
            
            for mapping in project_mappings:
                logger.info(f"Sincronizando proyecto local {mapping.proyecto_local_id} con proyecto Jira {mapping.jira_project_key}")
                
                # Obtener requerimientos para el proyecto correctamente
                requerimientos = Requerimiento.objects.filter(idproyecto=mapping.proyecto_local_id)
                
                logger.info(f"Requerimientos encontrados para proyecto {mapping.proyecto_local_id}: {requerimientos.count()}")
                
                # Obtener IDs de tareas ya mapeadas con Jira
                tareas_mapeadas_ids = JiraTaskMapping.objects.filter(
                    integracion=self.config
                ).values_list('tarea_local_id', flat=True)
                
                # SOLUCIÓN MEJORADA: Obtener dos conjuntos de tareas:
                # 1. Tareas modificadas desde la última sincronización (si hay fecha de última sincronización)
                # 2. Tareas que nunca se han mapeado con Jira (no tienen registro en JiraTaskMapping)
                if self.config.ultima_sincronizacion:
                    # Tareas modificadas recientemente
                    tareas_modificadas = Tarea.objects.filter(
                        idrequerimiento__in=requerimientos,
                        fechamodificacion__gte=self.config.ultima_sincronizacion
                    )
                    
                    # Tareas sin mapeo previo
                    tareas_sin_mapeo = Tarea.objects.filter(
                        idrequerimiento__in=requerimientos
                    ).exclude(idtarea__in=tareas_mapeadas_ids)
                    
                    # Combinar ambos conjuntos sin duplicados
                    tareas = (tareas_modificadas | tareas_sin_mapeo).distinct()
                else:
                    # Si es la primera sincronización, obtener todas las tareas
                    tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
                
                tareas_count = tareas.count()
                logger.info(f"Encontradas {tareas_count} tareas para sincronizar en el proyecto {mapping.proyecto_local_id}")
                
                if tareas_count == 0:
                    # Solo registrar advertencia, no detener la sincronización
                    logger.warning(f"No hay tareas para sincronizar en el proyecto {mapping.proyecto_local_id}")
                    # Crear un issue informativo en el proyecto Jira si está vacío
                    self._crear_issue_informativo_si_necesario(mapping.jira_project_key)
                    continue
                
                for tarea in tareas:
                    # Verificar si ya existe mapeo
                    task_mapping = JiraTaskMapping.objects.filter(
                        integracion=self.config, 
                        tarea_local_id=tarea.idtarea
                    ).first()
                    
                    if task_mapping:
                        logger.info(f"Actualizando tarea {tarea.idtarea} en Jira")
                        result = self.update_issue(tarea)
                        if result:
                            total_tareas_actualizadas += 1
                            logger.info(f"Tarea actualizada exitosamente con key {result.key}")
                        else:
                            logger.error(f"Error al actualizar tarea {tarea.idtarea} en Jira")
                    else:
                        logger.info(f"Creando tarea {tarea.idtarea} en Jira")
                        result = self.create_issue(tarea)
                        if result:
                            total_tareas_creadas += 1
                            logger.info(f"Tarea creada exitosamente con key {result.key}")
                        else:
                            logger.error(f"Error al crear tarea {tarea.idtarea} en Jira")
            
            logger.info(f"Exportación completada: {total_tareas_creadas} tareas creadas y {total_tareas_actualizadas} actualizadas")
            return True
                
        except Exception as e:
            logger.error(f"Error al exportar a Jira: {str(e)}")
            return False
    
    def _crear_issue_informativo_si_necesario(self, jira_project_key):
        """
        Crea un issue informativo en el proyecto Jira si no hay tareas para sincronizar
        o si el proyecto está vacío.
        """
        try:
            # Verificar si ya existe un issue informativo
            jql = f'project={jira_project_key} AND summary ~ "Proyecto sin tareas para sincronizar"'
            issues = self.jira.search_issues(jql)
            
            if issues:
                # Ya existe un issue informativo, actualizarlo
                issue = issues[0]
                update_dict = {
                    'description': f'Este proyecto no tiene tareas para sincronizar desde la aplicación local. ' +
                                  f'Última verificación: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}'
                }
                issue.update(fields=update_dict)
                logger.info(f"Issue informativo actualizado en proyecto {jira_project_key}")
                return issue
            else:
                # Crear un nuevo issue informativo
                issue_dict = {
                    'project': {'key': jira_project_key},
                    'summary': 'Proyecto sin tareas para sincronizar',
                    'description': f'Este proyecto no tiene tareas para sincronizar desde la aplicación local. ' +
                                  f'Última verificación: {timezone.now().strftime("%d/%m/%Y %H:%M:%S")}',
                    'issuetype': {'name': 'Task'},  # Usar el tipo adecuado según la instancia de Jira
                    'labels': ['info', 'automático', 'sin-tareas']
                }
                
                issue = self.jira.create_issue(fields=issue_dict)
                logger.info(f"Issue informativo creado en proyecto {jira_project_key} con key {issue.key}")
                return issue
                
        except Exception as e:
            logger.warning(f"No se pudo crear/actualizar el issue informativo en {jira_project_key}: {str(e)}")
            return None

    def _get_custom_field_id_by_name(self, field_name):
        """Obtiene el ID de un campo personalizado en Jira por su nombre"""
        try:
            # Obtener todos los campos disponibles
            fields = self.jira.fields()
            
            # Buscar el campo por nombre
            for field in fields:
                if field['name'].lower() == field_name.lower():
                    return field['id']
            
            logger.warning(f"No se encontró el campo personalizado: {field_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error al obtener campo personalizado: {str(e)}")
            return None
    
    def map_jira_users(self):
        """Mapea usuarios de Jira con usuarios locales"""
        try:
            # Esta función es más compleja ya que necesita permisos adicionales
            # y la API de usuarios de Jira puede ser restrictiva
            
            # Obtener usuarios de Jira (requiere permisos especiales)
            jira_users = self.jira.search_users(query='')
            
            # Obtener usuarios locales
            local_users = Usuario.objects.all()
            
            mappings_created = 0
            
            for local_user in local_users:
                # Intentar encontrar coincidencia por email o nombre de usuario
                for jira_user in jira_users:
                    if (hasattr(jira_user, 'emailAddress') and 
                        jira_user.emailAddress and 
                        jira_user.emailAddress.lower() == local_user.email.lower()):
                        
                        # Crear o actualizar mapeo
                        JiraUserMapping.objects.update_or_create(
                            integracion=self.config,
                            usuario_local_id=local_user.idusuario,
                            defaults={
                                'jira_user_id': jira_user.accountId,
                                'jira_user_key': getattr(jira_user, 'key', ''),
                                'jira_user_name': jira_user.displayName
                            }
                        )
                        mappings_created += 1
                        break
            
            logger.info(f"Se mapearon {mappings_created} usuarios entre sistemas")
            return mappings_created
            
        except Exception as e:
            logger.error(f"Error al mapear usuarios de Jira: {str(e)}")
            return 0
    
    def get_project_status(self, project_mapping):
        """Obtiene estadísticas de sincronización para un proyecto mapeado"""
        try:
            # Verificar si el proyecto existe en ambos sistemas
            try:
                proyecto_local = Proyecto.objects.get(idproyecto=project_mapping.proyecto_local_id)
            except Proyecto.DoesNotExist:
                return {
                    'error': f"No existe el proyecto local con ID {project_mapping.proyecto_local_id}"
                }
            
            # Contar tareas locales y tareas mapeadas
            requerimientos = Requerimiento.objects.filter(idproyecto=proyecto_local)
            total_tareas_locales = Tarea.objects.filter(idrequerimiento__in=requerimientos).count()
            
            # Tareas con mapeo a Jira
            tareas_mapeadas = JiraTaskMapping.objects.filter(
                integracion=self.config,
                tarea_local_id__in=Tarea.objects.filter(
                    idrequerimiento__in=requerimientos
                ).values_list('idtarea', flat=True)
            ).count()
            
            # Intentar obtener total de issues en el proyecto Jira
            try:
                jql = f'project={project_mapping.jira_project_key}'
                total_issues_jira = len(self.jira.search_issues(jql, maxResults=1, fields='id'))
            except Exception:
                total_issues_jira = "No disponible"
            
            return {
                'proyecto_local': {
                    'id': proyecto_local.idproyecto,
                    'nombre': proyecto_local.nombreproyecto,
                    'total_tareas': total_tareas_locales,
                },
                'proyecto_jira': {
                    'key': project_mapping.jira_project_key,
                    'id': project_mapping.jira_project_id,
                    'total_issues': total_issues_jira,
                },
                'sincronizacion': {
                    'tareas_mapeadas': tareas_mapeadas,
                    'ultima_sincronizacion': self.config.ultima_sincronizacion,
                    'porcentaje_sincronizado': (
                        round((tareas_mapeadas / total_tareas_locales) * 100, 1) 
                        if total_tareas_locales > 0 else 0
                    ),
                    'estado': 'Sincronizado' if tareas_mapeadas == total_tareas_locales and total_tareas_locales > 0 
                             else 'Parcial' if tareas_mapeadas > 0 
                             else 'No sincronizado'
                }
            }
        except Exception as e:
            logger.error(f"Error al obtener estado del proyecto: {str(e)}")
            return {
                'error': f"Error al obtener estado del proyecto: {str(e)}"
            }

    def clean_orphaned_mappings(self):
        """Limpia mapeos huérfanos (sin tarea o issue correspondiente)"""
        try:
            logger.info("Iniciando limpieza de mapeos huérfanos...")
            
            # 1. Encontrar mappings con tareas locales inexistentes
            orphaned_local = []
            for mapping in JiraTaskMapping.objects.filter(integracion=self.config):
                try:
                    Tarea.objects.get(idtarea=mapping.tarea_local_id)
                except Tarea.DoesNotExist:
                    orphaned_local.append(mapping.id)
            
            # 2. Encontrar mappings con issues inexistentes en Jira
            orphaned_jira = []
            for mapping in JiraTaskMapping.objects.filter(integracion=self.config):
                try:
                    self.jira.issue(mapping.jira_issue_key)
                except Exception:
                    orphaned_jira.append(mapping.id)
            
            # Eliminar mappings huérfanos
            total_deleted = 0
            if orphaned_local:
                deleted = JiraTaskMapping.objects.filter(id__in=orphaned_local).delete()[0]
                total_deleted += deleted
                logger.info(f"Eliminados {deleted} mapeos con tareas locales inexistentes")
                
            if orphaned_jira:
                deleted = JiraTaskMapping.objects.filter(id__in=orphaned_jira).delete()[0]
                total_deleted += deleted
                logger.info(f"Eliminados {deleted} mapeos con issues de Jira inexistentes")
            
            # Hacer lo mismo con los comentarios
            orphaned_comments = JiraComentarioMapping.objects.filter(
                integracion=self.config,
                actividad_local_id__isnull=False
            ).exclude(
                actividad_local_id__in=Actividad.objects.values_list('idactividad', flat=True)
            )
            
            if orphaned_comments:
                deleted = orphaned_comments.delete()[0]
                logger.info(f"Eliminados {deleted} mapeos de comentarios huérfanos")
                total_deleted += deleted
            
            return {
                'success': True,
                'total_cleaned': total_deleted,
                'message': f"Se eliminaron {total_deleted} mapeos huérfanos"
            }
                
        except Exception as e:
            logger.error(f"Error al limpiar mapeos huérfanos: {str(e)}")
            return {
                'success': False,
                'message': f"Error al limpiar mapeos: {str(e)}"
            }

    def check_integration_health(self):
        """Verifica el estado de salud de la integración con Jira"""
        health_report = {
            'connection': {'status': 'unknown', 'message': ''},
            'mappings': {'status': 'unknown', 'message': ''},
            'sync_status': {'status': 'unknown', 'message': ''},
            'last_sync': self.config.ultima_sincronizacion,
            'overall_status': 'unknown'
        }
        
        # Verificar conexión
        try:
            success, message = self.test_connection()
            health_report['connection'] = {
                'status': 'healthy' if success else 'error',
                'message': message
            }
        except Exception as e:
            health_report['connection'] = {
                'status': 'error',
                'message': f"Error de conexión: {str(e)}"
            }
        
        # Verificar mapeos
        try:
            project_mappings = JiraProjectMapping.objects.filter(integracion=self.config).count()
            task_mappings = JiraTaskMapping.objects.filter(integracion=self.config).count()
            
            if project_mappings == 0:
                health_report['mappings'] = {
                    'status': 'warning',
                    'message': 'No hay proyectos mapeados'
                }
            elif task_mappings == 0:
                health_report['mappings'] = {
                    'status': 'warning',
                    'message': 'No hay tareas mapeadas'
                }
            else:
                health_report['mappings'] = {
                    'status': 'healthy',
                    'message': f'{project_mappings} proyectos y {task_mappings} tareas mapeadas'
                }
        except Exception as e:
            health_report['mappings'] = {
                'status': 'error',
                'message': f"Error al verificar mapeos: {str(e)}"
            }
        
        # Verificar estado de sincronización
        try:
            if not self.config.ultima_sincronizacion:
                health_report['sync_status'] = {
                    'status': 'warning',
                    'message': 'Nunca se ha sincronizado'
                }
            else:
                time_diff = timezone.now() - self.config.ultima_sincronizacion
                hours_diff = time_diff.total_seconds() / 3600
                
                if hours_diff < 24:
                    health_report['sync_status'] = {
                        'status': 'healthy',
                        'message': 'Sincronizado en las últimas 24 horas'
                    }
                elif hours_diff < 72:
                    health_report['sync_status'] = {
                        'status': 'warning',
                        'message': 'Última sincronización hace más de 1 día'
                    }
                else:
                    health_report['sync_status'] = {
                        'status': 'error',
                        'message': 'Última sincronización hace más de 3 días'
                    }
        except Exception as e:
            health_report['sync_status'] = {
                'status': 'error',
                'message': f"Error al verificar estado de sincronización: {str(e)}"
            }
        
        # Determinar estado general
        if any(item['status'] == 'error' for item in [
            health_report['connection'], 
            health_report['mappings'], 
            health_report['sync_status']
        ]):
            health_report['overall_status'] = 'error'
        elif any(item['status'] == 'warning' for item in [
            health_report['connection'], 
            health_report['mappings'], 
            health_report['sync_status']
        ]):
            health_report['overall_status'] = 'warning'
        else:
            health_report['overall_status'] = 'healthy'
        
        return health_report

    def generate_sync_report(self, days_back=30):
        """
        Genera un reporte completo de sincronización
        para los últimos N días
        """
        start_date = timezone.now() - timezone.timedelta(days=days_back)
        
        # Estadísticas de proyectos sincronizados
        project_mappings = JiraProjectMapping.objects.filter(integracion=self.config)
        
        projects_data = []
        total_tareas_exportadas = 0
        total_issues_importados = 0
        
        for mapping in project_mappings:
            project_status = self.get_project_status(mapping)
            
            # Contar tareas creadas recientemente en este proyecto
            requerimientos = Requerimiento.objects.filter(
                idproyecto__idproyecto=mapping.proyecto_local_id
            )
            
            tareas_recientes = Tarea.objects.filter(
                idrequerimiento__in=requerimientos,
                fechacreacion__gte=start_date
            ).count()
            
            # Contar tareas mapeadas recientemente
            tareas_exportadas = JiraTaskMapping.objects.filter(
                integracion=self.config,
                tarea_local_id__in=Tarea.objects.filter(
                    idrequerimiento__in=requerimientos
                ).values_list('idtarea', flat=True),
                ultima_actualizacion__gte=start_date
            ).count()
            
            total_tareas_exportadas += tareas_exportadas
            
            # Mapear issues importados (si se puede identificar)
            issues_importados = Tarea.objects.filter(
                idrequerimiento__in=requerimientos,
                fechacreacion__gte=start_date,
                actividad__descripcion__contains="importada desde Jira"
            ).count()
            
            total_issues_importados += issues_importados
            
            projects_data.append({
                'proyecto_local': {
                    'id': mapping.proyecto_local_id,
                    'nombre': project_status.get('proyecto_local', {}).get('nombre', 'Desconocido'),
                    'tareas_recientes': tareas_recientes
                },
                'proyecto_jira': {
                    'key': mapping.jira_project_key,
                    'id': mapping.jira_project_id
                },
                'sincronizacion': {
                    'tareas_exportadas': tareas_exportadas,
                    'issues_importados': issues_importados,
                    'porcentaje': project_status.get('sincronizacion', {}).get('porcentaje_sincronizado', 0)
                }
            })
        
        # Obtener historial de sincronizaciones (desde tabla actividad si existe)
        sync_history = []
        try:
            sync_activities = Actividad.objects.filter(
                idusuario=self.config.idusuario,
                accion__in=["Importación", "Exportación", "Sincronización"],
                fechacreacion__gte=start_date
            ).order_by('-fechacreacion')
            
            for activity in sync_activities:
                sync_history.append({
                    'fecha': activity.fechacreacion,
                    'tipo': activity.accion,
                    'descripcion': activity.descripcion
                })
        except:
            pass  # La tabla actividad podría no existir o no tener los campos esperados
        
        return {
            'periodo': {
                'inicio': start_date,
                'fin': timezone.now()
            },
            'estadisticas': {
                'proyectos_sincronizados': len(project_mappings),
                'tareas_exportadas': total_tareas_exportadas,
                'issues_importados': total_issues_importados,
                'ultima_sincronizacion': self.config.ultima_sincronizacion
            },
            'proyectos': projects_data,
            'historial_sincronizaciones': sync_history,
            'estado_salud': self.check_integration_health()
        }

    def get_jira_users(self):
        """
        Obtiene usuarios de Jira usando diferentes estrategias
        para manejar las limitaciones de la API
        """
        try:
            # Primer intento: usar maxResults y patrón de búsqueda más amplio
            users = self.jira.search_users(query='*', maxResults=1000)
            if users:
                return users
                
            # Segundo intento: buscar por letras comunes
            all_users = []
            for letter in 'aeiou':  # Vocales - probablemente aparecen en muchos nombres
                users = self.jira.search_users(query=letter, maxResults=500)
                # Filtrar duplicados por accountId
                existing_account_ids = set(u.accountId for u in all_users if hasattr(u, 'accountId'))
                for user in users:
                    if not hasattr(user, 'accountId') or user.accountId not in existing_account_ids:
                        all_users.append(user)
                        if hasattr(user, 'accountId'):
                            existing_account_ids.add(user.accountId)
            
            return all_users
            
        except Exception as e:
            logger.error(f"Error al obtener usuarios de Jira: {str(e)}")
            
            # Si todo lo demás falla, intentar un enfoque más básico
            try:
                # Intento final: usar getUser con el administrador del proyecto
                admin_user = self.jira.myself()
                return [admin_user]  # Al menos devolver el usuario actual
            except:
                return []  # Si todo falla, devolver lista vacía