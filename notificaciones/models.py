from django.db import models

# Create your models here.

class Notificacion(models.Model):
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE,related_name="notificaciones")
    mensaje = models.TextField()
    leido = models.BooleanField(default=False)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.nombreUsuario} - {'Leído' if self.leido else 'No leído'}"

    class Meta:
        db_table = 'notificacion'
        ordering = ['-fechaCreacion']
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        
class Alerta(models.Model):
    tarea = models.ForeignKey('gestion_tareas.Tarea', on_delete=models.CASCADE, related_name="alertas")
    tipoAlerta = models.CharField(max_length=50, blank=True, null=True)
    mensaje = models.TextField()
    activa = models.BooleanField(default=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alerta {self.tipoAlerta} - {'Activa' if self.activa else 'Inactiva'}"
    
    class Meta:
        db_table = 'alerta'
        ordering = ['-fechaCreacion']
        verbose_name = 'Alerta'
        verbose_name_plural = 'Alertas'

class HistorialNotificacion(models.Model):
    notificacion = models.ForeignKey(Notificacion, on_delete=models.CASCADE, related_name="historial")
    fechaLectura = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Historial - {self.notificacion.idNotificacion} - {self.fechaLectura}"

    class Meta:
        db_table = 'historial_notificacion'
        verbose_name = 'Historial de Notificación'
        verbose_name_plural = 'Historial de Notificaciones'

class HistorialAlerta(models.Model):
    alerta = models.ForeignKey(Alerta, on_delete=models.CASCADE, related_name="historial")
    fechaResolucion = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Historial de Alerta {self.alerta.id} - {self.fechaResolucion or 'Sin resolver'}"
    
    class Meta:
        db_table = 'historial_alerta'
        verbose_name = 'Historial de Alerta'
        verbose_name_plural = 'Historial de Alertas'
