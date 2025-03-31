from rest_framework import serializers
from dashboard.models import (
    Tarea,
    TipoTarea,
    Fase,
    Requerimiento,
    Recurso,
    Tarearecurso,
)


class EstimacionTareaInputSerializer(serializers.Serializer):
    """Serializer para recibir los datos de entrada para estimación de tareas"""

    # Si se proporciona idtarea, se extrae la info automáticamente
    idtarea = serializers.IntegerField(required=False, allow_null=True)

    # Si no se proporciona idtarea, estos campos son necesarios para la estimación
    complejidad = serializers.IntegerField(required=False, min_value=1, max_value=5)
    prioridad = serializers.IntegerField(required=False, min_value=1, max_value=3)
    tipo_tarea = serializers.CharField(required=False)
    fase_tarea = serializers.CharField(required=False)
    cantidad_recursos = serializers.IntegerField(
        required=False, min_value=1, max_value=3
    )
    carga_trabajo_r1 = serializers.FloatField(
        required=False, min_value=0.1, max_value=1
    )
    experiencia_r1 = serializers.IntegerField(required=False, min_value=1, max_value=5)
    claridad_requisitos = serializers.FloatField(
        required=False, min_value=0.1, max_value=1
    )
    tamaño_estimado = serializers.IntegerField(required=False, min_value=1)

    # Opcional: información de contexto del requerimiento
    idrequerimiento = serializers.IntegerField(required=False)

    def validate(self, data):
        """Valida que se proporcione idtarea o los campos necesarios para estimación"""
        if "idtarea" not in data:
            required_fields = ["complejidad", "prioridad", "tipo_tarea"]
            for field in required_fields:
                if field not in data:
                    raise serializers.ValidationError(
                        f"Si no se proporciona idtarea, el campo '{field}' es obligatorio"
                    )
        return data

    def get_task_data(self, validated_data):
        """Extrae datos completos de la tarea para la estimación"""
        if "idtarea" in validated_data and validated_data["idtarea"]:
            # Extraer información de la tarea existente
            try:
                tarea = Tarea.objects.get(idtarea=validated_data["idtarea"])

                # Obtener recursos de la tarea
                recursos = Tarearecurso.objects.filter(idtarea=tarea)
                cantidad_recursos = recursos.count()

                # Obtener valores de recursos
                carga_trabajo_r1 = 0
                experiencia_r1 = 0
                if recursos.exists():
                    # Tomamos el primer recurso como R1
                    primer_recurso = recursos.first()
                    carga_trabajo_r1 = 0.5  # Valor por defecto
                    if (
                        hasattr(primer_recurso.idrecurso, "carga_trabajo")
                        and primer_recurso.idrecurso.carga_trabajo
                    ):
                        carga_trabajo_r1 = (
                            primer_recurso.idrecurso.carga_trabajo / 3.0
                        )  # Normalizamos a 0-1
                    experiencia_r1 = primer_recurso.experiencia or 3

                # Construir diccionario con datos de la tarea - usar formato PascalCase para nombres de claves
                return {
                    "Complejidad": tarea.dificultad or 3,
                    "Tipo_Tarea": (
                        tarea.tipo_tarea.nombre if tarea.tipo_tarea else "Backend"
                    ),
                    "Fase_Tarea": (
                        tarea.fase.nombre if tarea.fase else "Construcción/Desarrollo"
                    ),
                    "Cantidad_Recursos": cantidad_recursos or 1,
                    "Carga_Trabajo_R1": float(
                        carga_trabajo_r1
                    ),  # Convertir explícitamente a float
                    "Experiencia_R1": int(
                        experiencia_r1
                    ),  # Convertir explícitamente a int
                    "Carga_Trabajo_R2": 0.0,
                    "Experiencia_R2": 0,
                    "Carga_Trabajo_R3": 0.0,
                    "Experiencia_R3": 0,
                    "Experiencia_Equipo": 3,  # Valor por defecto
                    "Claridad_Requisitos": float(tarea.claridad_requisitos or 0.7),
                    "Tamaño_Tarea": int(tarea.tamaño_estimado or 5),
                }
            except Tarea.DoesNotExist:
                raise serializers.ValidationError("La tarea especificada no existe")
        else:
            # Usar los datos proporcionados directamente - en formato PascalCase
            return {
                "Complejidad": int(validated_data.get("complejidad", 3)),
                "Tipo_Tarea": str(validated_data.get("tipo_tarea", "Backend")),
                "Fase_Tarea": str(
                    validated_data.get("fase_tarea", "Construcción/Desarrollo")
                ),
                "Cantidad_Recursos": int(validated_data.get("cantidad_recursos", 1)),
                "Carga_Trabajo_R1": float(validated_data.get("carga_trabajo_r1", 0.5)),
                "Experiencia_R1": int(validated_data.get("experiencia_r1", 3)),
                "Carga_Trabajo_R2": float(validated_data.get("carga_trabajo_r2", 0)),
                "Experiencia_R2": int(validated_data.get("experiencia_r2", 0)),
                "Carga_Trabajo_R3": float(validated_data.get("carga_trabajo_r3", 0)),
                "Experiencia_R3": int(validated_data.get("experiencia_r3", 0)),
                "Experiencia_Equipo": int(validated_data.get("experiencia_equipo", 3)),
                "Claridad_Requisitos": float(
                    validated_data.get("claridad_requisitos", 0.7)
                ),
                "Tamaño_Tarea": int(validated_data.get("tamaño_estimado", 5)),
            }


class EstimacionResultadoSerializer(serializers.Serializer):
    """Serializer para los resultados de la estimación"""

    tiempo_estimado = serializers.FloatField()
    unidad = serializers.CharField()
    modelo = serializers.CharField()
    confianza = serializers.FloatField()
