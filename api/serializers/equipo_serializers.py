from rest_framework import serializers
from dashboard.models import Equipo, Miembro, Recurso, Usuario


class EquipoSerializer(serializers.ModelSerializer):
    """Serializer completo para operaciones CRUD de equipos"""

    miembros_count = serializers.SerializerMethodField()

    class Meta:
        model = Equipo
        fields = [
            "idequipo",
            "nombreequipo",
            "descripcion",
            "fechacreacion",
            "fechamodificacion",
            "miembros_count",
        ]
        read_only_fields = ["fechacreacion", "fechamodificacion"]

    def get_miembros_count(self, obj):
        """Obtener el número de miembros del equipo"""
        return Miembro.objects.filter(idequipo=obj).count()


class EquipoDetailSerializer(EquipoSerializer):
    """Serializer extendido que incluye información de miembros"""

    miembros = serializers.SerializerMethodField()

    class Meta(EquipoSerializer.Meta):
        fields = EquipoSerializer.Meta.fields + ["miembros"]

    def get_miembros(self, obj):
        """Obtener información detallada de los miembros del equipo"""
        miembros = Miembro.objects.filter(idequipo=obj)
        miembros_data = []

        for miembro in miembros:
            recurso = miembro.idrecurso
            # Verificar si el recurso es humano y tiene un usuario asociado
            usuario_data = None
            if hasattr(recurso, "recursohumano") and recurso.recursohumano.idusuario:
                usuario = recurso.recursohumano.idusuario
                usuario_data = {
                    "idusuario": usuario.idusuario,
                    "nombreusuario": usuario.nombreusuario,
                    "email": usuario.email,
                    "rol": usuario.rol,
                }

            miembro_data = {
                "idmiembro": miembro.idmiembro,
                "recurso": {
                    "idrecurso": recurso.idrecurso,
                    "nombrerecurso": recurso.nombrerecurso,
                    "tipo": recurso.idtiporecurso.nametiporecurso,
                    "disponibilidad": recurso.disponibilidad,
                    "carga_trabajo": recurso.carga_trabajo,
                },
            }

            if usuario_data:
                miembro_data["recurso"]["usuario"] = usuario_data

            miembros_data.append(miembro_data)

        return miembros_data
