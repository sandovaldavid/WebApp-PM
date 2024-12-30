from django.db import models
import datetime

# Create your models here.

class Tarea(models.Model):
    ESTADOS = [
        ('pendiente', 'Pendiente'),
        ('en_progreso', 'En Progreso'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    PRIORIDADES = [
        (1, 'Baja'),
        (2, 'Media'),
        (3, 'Alta'),
    ]
    idTarea = models.AutoField(primary_key=True)
    nombreTarea = models.CharField(max_length=255)
    fechaInicio = models.DateField(blank=True, null=True)
    fechaFin = models.DateField(blank=True, null=True)
    duracionEstimada = models.PositiveIntegerField(blank=True, null=True)
    duracionActual = models.PositiveIntegerField(blank=True, null=True)
    dificultad = models.PositiveIntegerField(blank=True, null=True)
    estado = models.CharField(max_length=50, choices=ESTADOS, default='pendiente')
    prioridad = models.PositiveIntegerField(choices=PRIORIDADES, default=2)
    costoEstimado = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    costoActual = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(auto_now=True)
    requerimiento = models.ForeignKey('gestion_proyectos.Requerimiento', on_delete=models.CASCADE, related_name="tareas")
    tarea_padre = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name="subtareas")

    def __str__(self):
        return f"Tarea {self.nombreTarea} - {self.requerimiento.proyecto.nombreProyecto}"

    @property
    def progreso_estimado(self):
        if self.fechaInicio and self.fechaFin:
            total_dias = (self.fechaFin - self.fechaInicio).days
            dias_transcurridos = (datetime.date.today() - self.fechaInicio).days
            return min(100, max(0, (dias_transcurridos / total_dias) * 100))
        return None

    
    class Meta:
        db_table = 'tarea'
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

class TareaRecurso(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE,related_name="tarea_recursos")
    recurso = models.ForeignKey('gestion_recursos.Recurso', on_delete=models.CASCADE,related_name="tarea_recursos")
    cantidad = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = 'tarea_recurso'
        verbose_name = 'Tarea Recurso'
        verbose_name_plural = 'Tareas Recursos'
        unique_together = ('tarea', 'recurso')

    def __str__(self):
        return f"{self.tarea.nombreTarea} - {self.recurso.nombreRecurso}"

class MonitoreoTarea(models.Model):
    tarea = models.OneToOneField(Tarea, on_delete=models.CASCADE,primary_key=True, related_name="monitoreo")
    fechaInicioReal = models.DateField(blank=True, null=True)
    fechaFinReal = models.DateField(blank=True, null=True)
    porcentajeCompletado = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    alertaGenerada = models.BooleanField(default=False)
    fechaModificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Monitoreo de {self.tarea.nombreTarea}"
    
    class Meta:
        db_table = 'monitoreo_tarea'
        verbose_name = 'Monitoreo Tarea'
        verbose_name_plural = 'Monitoreo Tareas'
        
class HistorialTarea(models.Model):
    tarea = models.ForeignKey(Tarea, on_delete=models.CASCADE, related_name="historial")
    fechaCambio = models.DateTimeField(auto_now_add=True)
    descripcionCambio = models.TextField()

    def __str__(self):
        return f"Historial de Tarea {self.tarea.nombreTarea} - {self.fechaCambio}"
    
    class Meta:
        db_table = 'historial_tarea'
        verbose_name = 'Historial de Tarea'
        verbose_name_plural = 'Historial de Tareas'
