from rest_framework import serializers
from dashboard.models import Tarea, TipoTarea, Fase, Requerimiento


class TareaSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de tareas"""

    tipo_tarea_nombre = serializers.SerializerMethodField()
    fase_nombre = serializers.SerializerMethodField()
    requerimiento_descripcion = serializers.SerializerMethodField()

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
            "prioridad",
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

    def validate(self, data):
        """Validar que la fecha fin sea posterior a la fecha inicio"""
        if "fechainicio" in data and "fechafin" in data:
            if data["fechainicio"] > data["fechafin"]:
                raise serializers.ValidationError(
                    "La fecha de fin debe ser posterior a la fecha de inicio."
                )
        return data


class TareaListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar tareas"""

    tipo_tarea_nombre = serializers.SerializerMethodField()
    fase_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Tarea
        fields = [
            "idtarea",
            "nombretarea",
            "estado",
            "prioridad",
            "fechainicio",
            "fechafin",
            "tipo_tarea_nombre",
            "fase_nombre",
            "duracionestimada",
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
