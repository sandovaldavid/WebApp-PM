from rest_framework import serializers
from dashboard.models import Proyecto, Equipo


class ProyectoSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de proyectos"""

    class Meta:
        model = Proyecto
        fields = [
            "idproyecto",
            "nombreproyecto",
            "descripcion",
            "idequipo",
            "fechainicio",
            "fechafin",
            "presupuesto",
            "presupuestoutilizado",
            "estado",
            "fechacreacion",
            "fechamodificacion",
        ]
        read_only_fields = ["fechacreacion", "fechamodificacion"]

    def validate(self, data):
        """Validar que la fecha fin sea posterior a la fecha inicio"""
        if "fechainicio" in data and "fechafin" in data:
            if data["fechainicio"] > data["fechafin"]:
                raise serializers.ValidationError(
                    "La fecha de fin debe ser posterior a la fecha de inicio."
                )
        return data


class ProyectoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar proyectos"""

    equipo_nombre = serializers.SerializerMethodField()

    class Meta:
        model = Proyecto
        fields = [
            "idproyecto",
            "nombreproyecto",
            "estado",
            "fechainicio",
            "fechafin",
            "equipo_nombre",
        ]

    def get_equipo_nombre(self, obj):
        """Obtener el nombre del equipo si existe"""
        if obj.idequipo:
            return obj.idequipo.nombreequipo
        return None
