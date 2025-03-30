import logging
from jira import JIRA
from django.utils import timezone
from django.conf import settings
from .models import IntegracionJira, JiraProjectMapping, JiraTaskMapping
from dashboard.models import Proyecto, Tarea, Requerimiento

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
    
    def get_issues(self, project_key, max_results=50):
        """Obtiene issues de un proyecto específico"""
        try:
            return self.jira.search_issues(f'project={project_key}', maxResults=max_results)
        except Exception as e:
            logger.error(f"Error al obtener issues: {str(e)}")
            return []
    
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
            
            # Preparar datos para el issue - SOLO CAMPOS BÁSICOS
            issue_dict = {
                'project': {'key': project_mapping.jira_project_key},
                'summary': tarea.nombretarea,
                'description': tarea.descripcion or 'Sin descripción',
                'issuetype': {'name': 'Task'},
            }
            
            # Crear issue en Jira con los campos básicos
            issue = self.jira.create_issue(fields=issue_dict)
            
            # DESPUÉS de crear la tarea, actualizar su estado mediante transiciones
            if tarea.estado:
                jira_status = self._map_status_to_jira(tarea.estado)
                self._update_issue_status(issue, jira_status)
            
            # Guardar mapeo
            JiraTaskMapping.objects.create(
                integracion=self.config,
                tarea_local_id=tarea.idtarea,
                jira_issue_id=issue.id,
                jira_issue_key=issue.key
            )
            
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
            
            # Actualizar campos
            update_dict = {}
            
            if issue.fields.summary != tarea.nombretarea:
                update_dict['summary'] = tarea.nombretarea
                
            if issue.fields.description != tarea.descripcion:
                update_dict['description'] = tarea.descripcion or 'Sin descripción'
            
            if tarea.estado:
                jira_status = self._map_status_to_jira(tarea.estado)
                # La actualización de estado suele requerir una transición en Jira
                self._update_issue_status(issue, jira_status)
            
            if update_dict:
                issue.update(fields=update_dict)
            
            return issue
        except Exception as e:
            logger.error(f"Error al actualizar issue en Jira: {str(e)}")
            return None
    
    def _map_status_to_jira(self, estado_local):
        """Mapea estados locales a estados de Jira"""
        status_mapping = {
            'Pendiente': 'Tarea por hacer',
            'En Progreso': 'En curso',
            'En Revisión': 'In Review',
            'Completada': 'Finalizada',
            'Cancelada': 'Canceled',
        }
        return status_mapping.get(estado_local, 'To Do')
    
    def _update_issue_status(self, issue, target_status):
        """Intenta actualizar el estado del issue usando transiciones"""
        try:
            transitions = self.jira.transitions(issue)
            for t in transitions:
                if t['name'].lower() == target_status.lower() or t['to']['name'].lower() == target_status.lower():
                    self.jira.transition_issue(issue, t['id'])
                    return True
            logger.warning(f"No se encontró transición a estado {target_status}")
            return False
        except Exception as e:
            logger.error(f"Error al actualizar estado: {str(e)}")
            return False
    
    def sync_all_data(self):
        """Sincroniza todos los datos entre la aplicación local y Jira"""
        self.sync_from_jira()
        self.sync_to_jira()
        
        # Actualizar timestamp de última sincronización
        self.config.ultima_sincronizacion = timezone.now()
        self.config.save()
    
    def sync_from_jira(self):
        """Importa datos desde Jira a la aplicación local"""
        # Implementar lógica para importar proyectos y tareas desde Jira
        pass
    
    def sync_to_jira(self):
        """Exporta datos desde la aplicación local a Jira"""
        logger.info("Iniciando sincronización hacia Jira")
        
        # Para cada proyecto mapeado
        project_mappings = JiraProjectMapping.objects.filter(integracion=self.config)
        
        for mapping in project_mappings:
            logger.info(f"Sincronizando proyecto local {mapping.proyecto_local_id} con proyecto Jira {mapping.jira_project_key}")
            
            # Obtener tareas del proyecto local a través de sus requerimientos
            requerimientos = Requerimiento.objects.filter(idproyecto__idproyecto=mapping.proyecto_local_id)
            tareas = Tarea.objects.filter(idrequerimiento__in=requerimientos)
            
            logger.info(f"Encontradas {tareas.count()} tareas para sincronizar")
            
            if tareas.count() == 0:
                logger.warning(f"No hay tareas para sincronizar en el proyecto {mapping.proyecto_local_id}")
                continue
            
            for tarea in tareas:
                # Verificar si ya existe mapeo
                task_mapping = JiraTaskMapping.objects.filter(
                    integracion=self.config, 
                    tarea_local_id=tarea.idtarea
                ).first()
                
                if task_mapping:
                    logger.info(f"Actualizando tarea {tarea.idtarea} en Jira")
                    self.update_issue(tarea)
                else:
                    logger.info(f"Creando tarea {tarea.idtarea} en Jira")
                    result = self.create_issue(tarea)
                    if result:
                        logger.info(f"Tarea creada exitosamente con key {result.key}")
                    else:
                        logger.error(f"Error al crear tarea {tarea.idtarea} en Jira")