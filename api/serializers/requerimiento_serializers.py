from rest_framework import serializers
from dashboard.models import Requerimiento, Proyecto


class RequerimientoSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de requerimientos"""

    proyecto_nombre = serializers.SerializerMethodField()
    tareas_count = serializers.SerializerMethodField()

    class Meta:
        model = Requerimiento
        fields = [
            "idrequerimiento",
            "descripcion",
            "keywords",
            "idproyecto",
            "proyecto_nombre",
            "tareas_count",
            "fechacreacion",
            "fechamodificacion",
        ]
        read_only_fields = ["fechacreacion", "fechamodificacion"]

    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto si existe"""
        if obj.idproyecto:
            return obj.idproyecto.nombreproyecto
        return None

    def get_tareas_count(self, obj):
        """Obtener el número de tareas asociadas al requerimiento"""
        return obj.tarea_set.count()

    def validate_idproyecto(self, value):
        """Validar que el proyecto exista"""
        if not Proyecto.objects.filter(idproyecto=value.idproyecto).exists():
            raise serializers.ValidationError("El proyecto especificado no existe.")
        return value

    def create(self, validated_data):
        """Crear requerimiento con fecha actual"""
        import datetime

        validated_data["fechacreacion"] = datetime.datetime.now()
        validated_data["fechamodificacion"] = validated_data["fechacreacion"]
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Actualizar requerimiento con nueva fecha de modificación"""
        import datetime

        validated_data["fechamodificacion"] = datetime.datetime.now()
        return super().update(instance, validated_data)


class RequerimientoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar requerimientos"""

    proyecto_nombre = serializers.SerializerMethodField()
    tareas_count = serializers.SerializerMethodField()

    class Meta:
        model = Requerimiento
        fields = [
            "idrequerimiento",
            "descripcion",
            "idproyecto",
            "proyecto_nombre",
            "tareas_count",
        ]

    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto si existe"""
        if obj.idproyecto:
            return obj.idproyecto.nombreproyecto
        return None

    def get_tareas_count(self, obj):
        """Obtener el número de tareas asociadas al requerimiento"""
        return obj.tarea_set.count()
