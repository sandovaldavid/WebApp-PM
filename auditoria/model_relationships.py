"""
Define las relaciones entre modelos para el sistema de auditoría.
Esto permite evitar registros duplicados cuando se modifican modelos relacionados.
"""

# Mapeo de modelos "hijo" a sus modelos "padre"
# Cuando se modifica un modelo hijo, la auditoría se registrará en el modelo padre
RELATED_MODELS = {
    # Formato: 'ModeloHijo': {'modelo_padre': 'ModeloPadre', 'campo_relacion': 'nombre_campo_fk'}
    'RecursoHumano': {'modelo_padre': 'Recurso', 'campo_relacion': 'idrecurso'},
    'RecursoMaterial': {'modelo_padre': 'Recurso', 'campo_relacion': 'idrecurso'},
    'Desarrollador': {'modelo_padre': 'Usuario', 'campo_relacion': 'idusuario'},
    'JefeProyecto': {'modelo_padre': 'Usuario', 'campo_relacion': 'idusuario'},
    'Cliente': {'modelo_padre': 'Usuario', 'campo_relacion': 'idusuario'},
    'Tester': {'modelo_padre': 'Usuario', 'campo_relacion': 'idusuario'},
    'Administrador': {'modelo_padre': 'Usuario', 'campo_relacion': 'idusuario'},
}

# Mapeo inverso para rápido acceso: modelos padre a todos sus hijos
PARENT_MODELS = {}
for hijo, info in RELATED_MODELS.items():
    padre = info['modelo_padre']
    if padre not in PARENT_MODELS:
        PARENT_MODELS[padre] = []
    PARENT_MODELS[padre].append(hijo)

def is_child_model(model_name):
    """Verifica si un modelo es un modelo hijo en la jerarquía de auditoría"""
    return model_name in RELATED_MODELS

def get_parent_model(model_name):
    """Obtiene el modelo padre para un modelo hijo dado"""
    if model_name in RELATED_MODELS:
        return RELATED_MODELS[model_name]['modelo_padre']
    return None

def get_relation_field(model_name):
    """Obtiene el campo de relación para un modelo hijo dado"""
    if model_name in RELATED_MODELS:
        return RELATED_MODELS[model_name]['campo_relacion']
    return None

def get_child_models(model_name):
    """Obtiene la lista de modelos hijo para un modelo padre dado"""
    return PARENT_MODELS.get(model_name, [])

# Agregamos una función para detectar si debe auditarse un cambio en un modelo hijo
def should_audit_child_change(instance, field_name):
    """
    Determina si un cambio en un campo específico de un modelo hijo debe auditarse.
    
    Para algunos campos especiales (como el propio ID del modelo o la relación con el padre),
    no queremos propagar los cambios.
    """
    model_name = instance.__class__.__name__
    
    # Si no es un modelo hijo, siempre auditar
    if not is_child_model(model_name):
        return True
    
    # Campos que normalmente no queremos auditar en modelos hijos
    ignore_fields = ['id', 'pk', get_relation_field(model_name)]
    
    # Si el campo está en la lista de ignorados, no auditar
    return field_name not in ignore_fields
