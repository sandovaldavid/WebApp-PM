from rest_framework import serializers
from dashboard.models import Tarea, TipoTarea, Fase, Requerimiento, Proyecto


class TareaSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de tareas"""

    tipo_tarea_nombre = serializers.SerializerMethodField()
    fase_nombre = serializers.SerializerMethodField()
    requerimiento_descripcion = serializers.SerializerMethodField()
    proyecto_nombre = serializers.SerializerMethodField()

    # Useful for state representation in frontends
    estado_display = serializers.SerializerMethodField()
    prioridad_display = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            "idtarea",
            "nombretarea",
            "descripcion",
            "tags",
            "fechainicio",
            "fechafin",
            "duracionestimada",
            "duracionactual",
            "dificultad",
            "estado",
            "estado_display",
            "prioridad",
            "prioridad_display",
            "tipo_tarea",
            "tipo_tarea_nombre",
            "fase",
            "fase_nombre",
            "claridad_requisitos",
            "tamaño_estimado",
            "costoestimado",
            "costoactual",
            "idrequerimiento",
            "requerimiento_descripcion",
            "proyecto_nombre",
            "fechacreacion",
            "fechamodificacion",
        ]
        read_only_fields = ["fechacreacion", "fechamodificacion"]

    def get_tipo_tarea_nombre(self, obj):
        """Obtener el nombre del tipo de tarea si existe"""
        if obj.tipo_tarea:
            return obj.tipo_tarea.nombre
        return None

    def get_fase_nombre(self, obj):
        """Obtener el nombre de la fase si existe"""
        if obj.fase:
            return obj.fase.nombre
        return None

    def get_requerimiento_descripcion(self, obj):
        """Obtener la descripción del requerimiento"""
        if obj.idrequerimiento:
            return obj.idrequerimiento.descripcion
        return None

    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto asociado al requerimiento"""
        if obj.idrequerimiento and obj.idrequerimiento.idproyecto:
            return obj.idrequerimiento.idproyecto.nombreproyecto
        return None

    def get_estado_display(self, obj):
        """Proporciona una versión más legible del estado"""
        estados = {
            "pendiente": "Pendiente",
            "en_progreso": "En Progreso",
            "completada": "Completada",
            "pausada": "Pausada",
            "cancelada": "Cancelada",
        }
        return estados.get(obj.estado, obj.estado)

    def get_prioridad_display(self, obj):
        """Proporciona una versión más legible de la prioridad"""
        if obj.prioridad is None:
            return None

        prioridades = {1: "Baja", 2: "Media", 3: "Alta", 4: "Urgente", 5: "Crítica"}
        return prioridades.get(obj.prioridad, f"Nivel {obj.prioridad}")


class TareaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar tareas"""

    tipo_tarea_nombre = serializers.SerializerMethodField()
    fase_nombre = serializers.SerializerMethodField()
    requerimiento_id = serializers.SerializerMethodField()
    proyecto_nombre = serializers.SerializerMethodField()
    estado_display = serializers.SerializerMethodField()
    prioridad_display = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            "idtarea",
            "nombretarea",
            "descripcion",
            "tags",
            "estado",
            "estado_display",
            "prioridad",
            "prioridad_display",
            "fechainicio",
            "fechafin",
            "duracionestimada",
            "duracionactual",
            "tipo_tarea_nombre",
            "fase_nombre",
            "requerimiento_id",
            "proyecto_nombre",
        ]

    def get_tipo_tarea_nombre(self, obj):
        """Obtener el nombre del tipo de tarea si existe"""
        if obj.tipo_tarea:
            return obj.tipo_tarea.nombre
        return None

    def get_fase_nombre(self, obj):
        """Obtener el nombre de la fase si existe"""
        if obj.fase:
            return obj.fase.nombre
        return None

    def get_requerimiento_id(self, obj):
        """Obtener el ID del requerimiento"""
        if obj.idrequerimiento:
            return obj.idrequerimiento.idrequerimiento
        return None

    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto asociado al requerimiento"""
        if obj.idrequerimiento and obj.idrequerimiento.idproyecto:
            return obj.idrequerimiento.idproyecto.nombreproyecto
        return None

    def get_estado_display(self, obj):
        """Proporciona una versión más legible del estado"""
        estados = {
            "pendiente": "Pendiente",
            "en_progreso": "En Progreso",
            "completada": "Completada",
            "pausada": "Pausada",
            "cancelada": "Cancelada",
        }
        return estados.get(obj.estado, obj.estado)

    def get_prioridad_display(self, obj):
        """Proporciona una versión más legible de la prioridad"""
        if obj.prioridad is None:
            return None

        prioridades = {1: "Baja", 2: "Media", 3: "Alta", 4: "Urgente", 5: "Crítica"}
        return prioridades.get(obj.prioridad, f"Nivel {obj.prioridad}")
