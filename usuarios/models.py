from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Usuario(AbstractUser):
    email = models.EmailField(unique=True)
    rol = models.CharField(max_length=50, choices=[
        ('Administrador', 'Administrador'),
        ('Desarrollador', 'Desarrollador'),
        ('JefeProyecto', 'Jefe de Proyecto'),
        ('Cliente', 'Cliente'),
        ('Tester', 'Tester'),
    ])
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_modificacion = models.DateTimeField(auto_now=True)

class RolModuloAcceso(models.Model):
    nombre_rol = models.CharField(max_length=50)
    modulo = models.CharField(max_length=255)
    permisos = models.CharField(max_length=50, choices=[
        ('lectura', 'Lectura'),
        ('escritura', 'Escritura'),
        ('lectura-escritura', 'Lectura-Escritura'),
    ])

class UsuarioRolModulo(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    rol_modulo = models.ForeignKey(RolModuloAcceso, on_delete=models.CASCADE)

class Meta:
    db_table = 'usuario'
    ordering = ['id']
    verbose_name = 'Usuario'
    verbose_name_plural = 'Usuarios'