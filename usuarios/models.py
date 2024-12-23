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
    
    class Meta:
        db_table = 'usuario'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

class RolModuloAcceso(models.Model):
    PERMISOS_CHOICES = [
        ('lectura', 'Lectura'),
        ('escritura', 'Escritura'),
        ('lectura-escritura', 'Lectura-Escritura'),
    ]
    
    idRolModulo = models.AutoField(primary_key=True)
    nombreRol = models.CharField(max_length=50)
    modulo = models.CharField(max_length=255)
    permisos = models.CharField(max_length=50, choices=PERMISOS_CHOICES)

    def __str__(self):
        return f"{self.nombreRol} - {self.modulo}"
    
    class Meta:
        db_table = 'rol_modulo_acceso'
        verbose_name = 'Rol Modulo Acceso'
        verbose_name_plural = 'Roles Modulos Acceso'

class UsuarioRolModulo(models.Model):
    usuario = models.ForeignKey('Usuario', on_delete=models.CASCADE, related_name='roles_modulos')
    rol_modulo = models.ForeignKey('RolModuloAcceso',on_delete=models.CASCADE, related_name='usuarios')

    def __str__(self):
        return f"{self.usuario} - {self.rol_modulo}"

    class Meta:
        unique_together = ('usuario', 'rol_modulo')
        verbose_name = 'Usuario Rol Modulo'
        verbose_name_plural = 'Usuarios Roles Modulos'

class Administrador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name="administrador")

    def __str__(self):
        return f"Administrador: {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = 'administrador'
        verbose_name = 'Administrador'
        verbose_name_plural = 'Administradores'
        

class Desarrollador(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name="desarrollador")
    tareasCompletadas = models.PositiveIntegerField(default=0)
    tiempoTotalEmpleado = models.DurationField(default="0:00:00")

    def __str__(self):
        return f"Desarrollador: {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = 'desarrollador'
        verbose_name = 'Desarrollador'
        verbose_name_plural = 'Desarrolladores'


class JefeProyecto(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name="jefe_proyecto")
    proyectosGestionados = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Jefe de Proyecto: {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = 'jefe_proyecto'
        verbose_name = 'Jefe de Proyecto'
        verbose_name_plural = 'Jefes de Proyecto'


class Cliente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name="cliente")

    def __str__(self):
        return f"Cliente: {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = 'cliente'
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'


class Tester(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, primary_key=True, related_name="tester")

    def __str__(self):
        return f"Tester: {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = 'tester'
        verbose_name = 'Tester'
        verbose_name_plural = 'Testers'
