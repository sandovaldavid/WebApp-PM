from django.db import models

# Create your models here.

class Recurso(models.Model):
    idRecurso = models.AutoField(primary_key=True)
    nombreRecurso = models.CharField(max_length=255)
    idTipoRecurso = models.ForeignKey('TipoRecurso', on_delete=models.CASCADE, related_name="recursos")
    disponibilidad = models.BooleanField(default=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombreRecurso
    
    class Meta:
        db_table = 'recurso'
        verbose_name = 'Recurso'
        verbose_name_plural = 'Recursos'   
        
class TipoRecurso(models.Model):
    idTipoRecurso = models.AutoField(primary_key=True)
    nameTipoRecurso = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nameTipoRecurso
    
    class Meta:
        db_table = 'tipo_recurso'
        verbose_name = 'Tipo de Recurso'
        verbose_name_plural = 'Tipos de Recursos'

class RecursoHumano(models.Model):
    recurso = models.OneToOneField(Recurso, on_delete=models.CASCADE, primary_key=True, related_name="recurso_humano")
    cargo = models.CharField(max_length=255, blank=True, null=True)
    habilidades = models.TextField(blank=True, null=True)
    tarifaHora = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    usuario = models.OneToOneField('usuarios.Usuario', on_delete=models.CASCADE,related_name="recurso_humano")

    def __str__(self):
        return f"{self.recurso.nombreRecurso} ({self.cargo})"

    
    class Meta:
        db_table = 'recurso_humano'
        verbose_name = 'Recurso Humano'
        verbose_name_plural = 'Recursos Humanos'

class RecursoMaterial(models.Model):
    recurso = models.OneToOneField('Recurso', on_delete=models.CASCADE, primary_key=True, related_name="recurso_material")
    costoUnidad = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    fechaCompra = models.DateField(blank=True, null=True)

    def __str__(self):
        return f"{self.recurso.nombreRecurso} - Costo: {self.costoUnidad}"

    
    class Meta:
        db_table = 'recurso_material'
        verbose_name = 'Recurso Material'
        verbose_name_plural = 'Recursos Materiales'
