from rest_framework import serializers
from dashboard.models import Usuario

class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Usuario
        fields = [
            'idusuario',  # Changed from 'id' to 'idusuario'
            'username', 
            'email', 
            'nombreusuario', 
            'rol', 
            'fechacreacion'
        ]
        read_only_fields = ['fechacreacion']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate_email(self, value):
        """Validate email is unique"""
        if self.instance and self.instance.email == value:
            return value
        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está en uso.")
        return value
        
    def create(self, validated_data):
        """Create a new user with encrypted password"""
        password = validated_data.pop('password', None)
        user = Usuario.objects.create(**validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user
    
    def update(self, instance, validated_data):
        """Update user with properly handling password"""
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save()
        return user


class UsuarioListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing users"""
    class Meta:
        model = Usuario
        fields = ["idusuario", "username", "email", "nombreusuario", "rol", "is_active"]
