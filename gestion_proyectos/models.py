from django.db import models

class Proyecto(models.Model):
    idProyecto = models.AutoField(primary_key=True)
    nombreProyecto = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    equipo = models.ForeignKey('gestion_equipos.Equipo', on_delete=models.CASCADE, related_name="proyectos")
    fechaInicio = models.DateField(blank=True, null=True)
    fechaFin = models.DateField(blank=True, null=True)
    presupuesto = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    estado = models.CharField(max_length=50, blank=True, null=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombreProyecto
    
    class Meta:
        db_table = 'proyecto'
        verbose_name = 'Proyecto'
        verbose_name_plural = 'Proyectos'

class Requerimiento(models.Model):
    idRequerimiento = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(auto_now=True)
    proyecto = models.ForeignKey('Proyecto', on_delete=models.CASCADE, related_name="requerimientos")

    def __str__(self):
        return f"Requerimiento {self.idRequerimiento} - {self.proyecto.nombreProyecto}"
    
    class Meta:
        db_table = 'requerimiento'
        verbose_name = 'Requerimiento'
        verbose_name_plural = 'Requerimientos'
