from django.db import models

# Create your models here.

class Reporte(models.Model):
    tipoReporte = models.CharField(max_length=50)
    fechaGeneracion = models.DateTimeField(auto_now_add=True)
    proyecto = models.ForeignKey('dashboard.Proyecto', on_delete=models.CASCADE, related_name="reportes")

    def __str__(self):
        return f"Reporte {self.tipoReporte} - Proyecto {self.proyecto.nombreProyecto}"
    
    class Meta:
        db_table = "reporte"
        verbose_name = "Reporte"
        verbose_name_plural = "Reportes"

class ReporteUsuario(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name="usuarios")
    usuario = models.ForeignKey('usuarios.Usuario', on_delete=models.CASCADE, related_name="reportes")
    descripcion = models.TextField(blank=True, null=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reporte {self.reporte.id} - Usuario {self.usuario.nombreUsuario}"
    
    class Meta:
        db_table = "reporte_usuario"
        verbose_name = "Reporte Usuario"
        verbose_name_plural = "Reportes Usuarios"

class HistorialReporte(models.Model):
    reporte = models.ForeignKey(Reporte, on_delete=models.CASCADE, related_name="historial")
    fechaModificacion = models.DateTimeField(auto_now=True)
    descripcionCambio = models.TextField()

    def __str__(self):
        return f"Historial de Reporte {self.reporte.id} - {self.fechaModificacion}"

    class Meta:
        db_table = 'historial_reporte'
        verbose_name = 'Historial de Reporte'
        verbose_name_plural = 'Historial de Reportes'
        
class HistorialReporteUsuario(models.Model):
    reporteUsuario = models.ForeignKey(ReporteUsuario, on_delete=models.CASCADE, related_name="historial")
    cambio = models.TextField()
    fechaModificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Historial de ReporteUsuario {self.reporteUsuario.id} - {self.fechaModificacion}"
