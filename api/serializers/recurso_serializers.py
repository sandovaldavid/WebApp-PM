from rest_framework import serializers
from dashboard.models import Recurso, Tiporecurso, Recursohumano, Recursomaterial


class RecursoSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de recursos"""

    tipo_recurso = serializers.SerializerMethodField()
    detalles = serializers.SerializerMethodField()

    class Meta:
        model = Recurso
        fields = [
            "idrecurso",
            "nombrerecurso",
            "idtiporecurso",
            "tipo_recurso",
            "disponibilidad",
            "carga_trabajo",
            "detalles",
            "fechacreacion",
            "fechamodificacion",
        ]
        read_only_fields = ["fechacreacion", "fechamodificacion"]

    def get_tipo_recurso(self, obj):
        """Obtener el nombre del tipo de recurso"""
        if obj.idtiporecurso:
            return obj.idtiporecurso.nametiporecurso
        return None

    def get_detalles(self, obj):
        """Obtener detalles adicionales según el tipo de recurso"""
        if hasattr(obj, "recursohumano"):
            return {
                "tipo": "Humano",
                "cargo": obj.recursohumano.cargo,
                "habilidades": obj.recursohumano.habilidades,
                "tarifahora": obj.recursohumano.tarifahora,
                "usuario": (
                    obj.recursohumano.idusuario.nombreusuario
                    if obj.recursohumano.idusuario
                    else None
                ),
            }
        elif hasattr(obj, "recursomaterial"):
            return {
                "tipo": "Material",
                "costounidad": obj.recursomaterial.costounidad,
                "fechacompra": obj.recursomaterial.fechacompra,
            }
        return None

    def create(self, validated_data):
        """Crear recurso con fecha actual"""
        import datetime

        validated_data["fechacreacion"] = datetime.datetime.now()
        validated_data["fechamodificacion"] = validated_data["fechacreacion"]
        return super().create(validated_data)

    def update(self, instance, validated_data):
        """Actualizar recurso con nueva fecha de modificación"""
        import datetime

        validated_data["fechamodificacion"] = datetime.datetime.now()
        return super().update(instance, validated_data)


class RecursoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar recursos"""

    tipo_recurso = serializers.SerializerMethodField()
    tipo_detalle = serializers.SerializerMethodField()

    class Meta:
        model = Recurso
        fields = [
            "idrecurso",
            "nombrerecurso",
            "tipo_recurso",
            "tipo_detalle",
            "disponibilidad",
            "carga_trabajo",
        ]

    def get_tipo_recurso(self, obj):
        """Obtener el nombre del tipo de recurso"""
        if obj.idtiporecurso:
            return obj.idtiporecurso.nametiporecurso
        return None

    def get_tipo_detalle(self, obj):
        """Obtener el tipo detallado del recurso (Humano o Material)"""
        if hasattr(obj, "recursohumano"):
            return "Humano"
        elif hasattr(obj, "recursomaterial"):
            return "Material"
        return "Desconocido"
