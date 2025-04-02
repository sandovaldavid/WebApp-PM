from rest_framework import serializers
from dashboard.models import TareaComun, TipoTarea


class TareaComunSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de tareas comunes"""

    tipo_tarea_nombre = serializers.SerializerMethodField()

    class Meta:
        model = TareaComun
        fields = [
            "idtareacomun",
            "nombre",
            "descripcion",
            "idtipotarea",
            "tipo_tarea_nombre",
            "tiempo_promedio",
            "variabilidad_tiempo",
            "fechacreacion",
        ]
        read_only_fields = ["fechacreacion"]

    def get_tipo_tarea_nombre(self, obj):
        """Obtener el nombre del tipo de tarea si existe"""
        if obj.idtipotarea:
            return obj.idtipotarea.nombre
        return None

    def validate_idtipotarea(self, value):
        """Validar que el tipo de tarea exista"""
        if value is not None:
            try:
                TipoTarea.objects.get(idtipotarea=value.idtipotarea)
            except TipoTarea.DoesNotExist:
                raise serializers.ValidationError(
                    "El tipo de tarea especificado no existe."
                )
        return value


class TareaComunListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar tareas comunes"""

    tipo_tarea_nombre = serializers.SerializerMethodField()

    class Meta:
        model = TareaComun
        fields = [
            "idtareacomun",
            "nombre",
            "descripcion",
            "tipo_tarea_nombre",
            "tiempo_promedio",
            "variabilidad_tiempo",
        ]

    def get_tipo_tarea_nombre(self, obj):
        """Obtener el nombre del tipo de tarea si existe"""
        if obj.idtipotarea:
            return obj.idtipotarea.nombre
        return None
