from django.db import models
from gestion_proyectos.models import Proyecto, Requerimiento
from gestion_recursos.models import Recurso

# Create your models here.

class Tarea(models.Model):
    idtarea = models.AutoField(primary_key=True)
    nombretarea = models.CharField(max_length=255)
    fechainicio = models.DateField(blank=True, null=True)
    fechafin = models.DateField(blank=True, null=True)
    duracionestimada = models.IntegerField(blank=True, null=True)
    duracionactual = models.IntegerField(blank=True, null=True)
    dificultad = models.IntegerField(blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    prioridad = models.IntegerField(blank=True, null=True)
    costoestimado = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    costoactual = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    idrequerimiento = models.ForeignKey(Requerimiento, models.DO_NOTHING, db_column='idrequerimiento')
    
    def __str__(self):
        return self.nombretarea
    
    class Meta:
        db_table = 'tarea'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

class Tarearecurso(models.Model):
    idtarea = models.ForeignKey(Tarea, models.DO_NOTHING, db_column='idtarea', primary_key=True)  # Aquí quitamos OneToOneField
    idrecurso = models.ForeignKey(Recurso, models.DO_NOTHING, db_column='idrecurso')
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tarea_recurso'
        verbose_name = 'Tarea Recurso'
        verbose_name_plural = 'Tareas Recursos'
        unique_together = ('idtarea', 'idrecurso')  # Asegura que no haya duplicados de tarea y recurso

class Monitoreotarea(models.Model):
    idtarea = models.OneToOneField('Tarea', models.DO_NOTHING, db_column='idtarea', primary_key=True)
    fechainicioreal = models.DateField(blank=True, null=True)
    fechafinreal = models.DateField(blank=True, null=True)
    porcentajecompletado = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    alertagenerada = models.BooleanField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'monitoreo_tarea'
        verbose_name = 'Monitoreo Tarea'
        verbose_name_plural = 'Monitoreo Tareas'
