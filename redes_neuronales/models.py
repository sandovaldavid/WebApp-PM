from django.db import models
# from dashboard.models import Proyecto  # Esto causa la importación circular

class ModeloRedNeuronal(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    proyecto = models.ForeignKey('dashboard.Proyecto', on_delete=models.CASCADE, related_name="modelos_redes")
    fecha_entrenamiento = models.DateField()
    accuracy = models.FloatField()

    def __str__(self):
        return self.nombre

    class Meta:
        db_table = 'modelo_red_neuronal'
        ordering = ['id']
        verbose_name = 'Modelo de Red Neuronal'
        verbose_name_plural = 'Modelos de Redes Neuronales'