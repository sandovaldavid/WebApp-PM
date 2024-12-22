from django.db import models
from gestion_proyectos.models import Proyecto

# Create your models here.

class Recurso(models.Model):
    idrecurso = models.AutoField(primary_key=True)
    nombrerecurso = models.CharField(max_length=255)
    idtiporecurso = models.IntegerField()
    disponibilidad = models.BooleanField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.nombrerecurso} - {self.proyecto}"
    
    class Meta:
        db_table = 'recurso'
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'   
        
class TipoRecurso(models.Model):
    nombre_tipo_recurso = models.CharField(max_length=255)
    descripcion = models.TextField(null=True, blank=True)
    
    def __str__(self):
        return self.nombre_tipo_recurso
    
    class Meta:
        db_table = 'tipo_recurso'
        verbose_name = 'Tipo de Recurso'
        verbose_name_plural = 'Tipos de Recursos'

class RecursoHumano(models.Model):
    recurso = models.OneToOneField(Recurso, on_delete=models.CASCADE, primary_key=True)
    cargo = models.CharField(max_length=255)
    habilidades = models.TextField(null=True, blank=True)
    tarifa_hora = models.DecimalField(max_digits=10, decimal_places=2)
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.recurso} - {self.usuario}"
    
    class Meta:
        db_table = 'recurso_humano'
        verbose_name = 'Recurso Humano'
        verbose_name_plural = 'Recursos Humanos'

class RecursoMaterial(models.Model):
    recurso = models.OneToOneField(Recurso, on_delete=models.CASCADE, primary_key=True)
    costo_unidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_compra = models.DateField()
    
    def __str__(self):
        return f"{self.recurso} - {self.costo_unidad}"
    
    class Meta:
        db_table = 'recurso_material'
        verbose_name = 'Recurso Material'
        verbose_name_plural = 'Recursos Materiales'
