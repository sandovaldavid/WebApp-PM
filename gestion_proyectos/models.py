from django.db import models
from gestion_equipos.models import Equipo

class Proyecto(models.Model):
    idproyecto = models.AutoField(primary_key=True)
    nombreproyecto = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    idequipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='idequipo')
    fechainicio = models.DateField(blank=True, null=True)
    fechafin = models.DateField(blank=True, null=True)
    presupuesto = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'proyecto'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

class Requerimiento(models.Model):
    idrequerimiento = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    idproyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column='idproyecto')
    
    class Meta:
        db_table = 'requerimiento'
        verbose_name = 'Requerimiento'
        verbose_name_plural = 'Requerimientos'
