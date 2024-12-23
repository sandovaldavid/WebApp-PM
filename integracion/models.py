from django.db import models

# Create your models here.

class IntegracionExterna(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    url = models.URLField()
    token = models.CharField(max_length=255)

    def __str__(self):
        return self.nombre
    
    class Meta:
        db_table = 'integracion_externa'
        ordering = ['id']
        verbose_name = 'Integración Externa'
        verbose_name_plural = 'Integraciones Externas'
