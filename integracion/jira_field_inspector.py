import json
import logging
from django.core.management.base import BaseCommand
from integracion.models import IntegracionJira, JiraProjectMapping
from integracion.jira_client import JiraClient

logger = logging.getLogger(__name__)

class JiraFieldInspector:
    """Utilidad para inspeccionar campos disponibles en Jira"""
    
    def __init__(self, integracion_id=None, config=None):
        if integracion_id:
            self.config = IntegracionJira.objects.get(pk=integracion_id)
        elif config:
            self.config = config
        else:
            raise ValueError("Se requiere ID de integración o configuración")
            
        self.client = JiraClient(config=self.config)
    
    def get_available_fields_for_project(self, project_key=None):
        """Obtiene los campos disponibles para un proyecto específico o todos los mapeados"""
        try:
            if not project_key:
                # Usar el primer proyecto mapeado
                mapping = JiraProjectMapping.objects.filter(integracion=self.config).first()
                if mapping:
                    project_key = mapping.jira_project_key
                else:
                    return {"error": "No hay proyectos mapeados"}
            
            # Obtener metadatos de creación
            create_meta = self.client.jira.createmeta(
                projectKeys=project_key,
                expand='projects.issuetypes.fields'
            )
            
            result = {
                "project": project_key,
                "issue_types": {}
            }
            
            # Procesar cada tipo de issue y sus campos
            for project in create_meta.get('projects', []):
                for issue_type in project.get('issuetypes', []):
                    issue_type_name = issue_type.get('name')
                    fields = {}
                    
                    for field_id, field_data in issue_type.get('fields', {}).items():
                        fields[field_id] = {
                            "name": field_data.get('name'),
                            "required": field_data.get('required', False),
                            "type": field_data.get('schema', {}).get('type')
                        }
                    
                    result['issue_types'][issue_type_name] = fields
            
            return result
        
        except Exception as e:
            logger.error(f"Error obteniendo campos disponibles: {str(e)}")
            return {"error": str(e)}

    def get_field_options(self, project_key, issue_type_name, field_id):
        """Obtiene las opciones disponibles para un campo específico"""
        try:
            field_meta = self.client.jira.createmeta(
                projectKeys=project_key,
                issuetypeNames=issue_type_name,
                expand=f'projects.issuetypes.fields.{field_id}.allowedValues'
            )
            
            for project in field_meta.get('projects', []):
                for issue_type in project.get('issuetypes', []):
                    field = issue_type.get('fields', {}).get(field_id, {})
                    allowed_values = field.get('allowedValues', [])
                    
                    options = []
                    for value in allowed_values:
                        if 'name' in value:
                            options.append({
                                'id': value.get('id'),
                                'name': value.get('name')
                            })
                    
                    return {
                        'field_id': field_id,
                        'field_name': field.get('name'),
                        'options': options
                    }
            
            return {'error': 'No se encontraron opciones para el campo'}
        
        except Exception as e:
            logger.error(f"Error obteniendo opciones de campo: {str(e)}")
            return {"error": str(e)}

    def print_fields_report(self, project_key=None):
        """Imprime un reporte de campos disponibles para diagnóstico"""
        fields_info = self.get_available_fields_for_project(project_key)
        
        if 'error' in fields_info:
            print(f"Error: {fields_info['error']}")
            return
            
        print(f"\n=== CAMPOS DISPONIBLES PARA PROYECTO: {fields_info['project']} ===\n")
        
        for issue_type, fields in fields_info['issue_types'].items():
            print(f"\n-- TIPO DE ISSUE: {issue_type} --\n")
            
            # Campos requeridos primero
            required_fields = {k: v for k, v in fields.items() if v.get('required')}
            print("Campos requeridos:")
            for field_id, field_info in required_fields.items():
                print(f"  • {field_info['name']} ({field_id})")
            
            # Luego campos opcionales
            optional_fields = {k: v for k, v in fields.items() if not v.get('required')}
            print("\nCampos opcionales:")
            for field_id, field_info in optional_fields.items():
                print(f"  • {field_info['name']} ({field_id})")
        
        print("\n=== FIN DE REPORTE ===\n")

def run_field_inspector():
    """Ejecuta el inspector de campos para la primera integración disponible"""
    try:
        integracion = IntegracionJira.objects.first()
        if not integracion:
            print("No hay integraciones configuradas")
            return
            
        inspector = JiraFieldInspector(config=integracion)
        inspector.print_fields_report()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    run_field_inspector()
