from rest_framework import serializers
from dashboard.models import Requerimiento, Proyecto


class RequerimientoSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de requerimientos"""
    
    proyecto_nombre = serializers.SerializerMethodField()
    tareas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Requerimiento
        fields = [
            'idrequerimiento', 
            'descripcion', 
            'keywords', 
            'idproyecto',
            'proyecto_nombre',
            'tareas_count',
            'fechacreacion', 
            'fechamodificacion'
        ]
        read_only_fields = ['fechacreacion', 'fechamodificacion']
    
    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto si existe"""
        if obj.idproyecto:
            return obj.idproyecto.nombreproyecto
        return None
    
    def get_tareas_count(self, obj):
        """Obtener el número de tareas asociadas al requerimiento"""
        return obj.tarea_set.count()


class RequerimientoListSerializer(serializers.ModelSerializer):
    """Serializer ligero para listar requerimientos"""
    
    proyecto_nombre = serializers.SerializerMethodField()
    tareas_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Requerimiento
        fields = [
            'idrequerimiento', 
            'descripcion', 
            'idproyecto',
            'proyecto_nombre',
            'tareas_count'
        ]
    
    def get_proyecto_nombre(self, obj):
        """Obtener el nombre del proyecto si existe"""
        if obj.idproyecto:
            return obj.idproyecto.nombreproyecto
        return None
    
    def get_tareas_count(self, obj):
        """Obtener el número de tareas asociadas al requerimiento"""
        return obj.tarea_set.count()
