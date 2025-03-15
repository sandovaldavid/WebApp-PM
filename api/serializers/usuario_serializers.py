from rest_framework import serializers
from dashboard.models import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = ["id", "username", "email", "nombreusuario", "rol"]
        read_only_fields = ["fechacreacion"]
