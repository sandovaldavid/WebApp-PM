from django.db import models

class Equipo(models.Model):
    idEquipo = models.AutoField(primary_key=True)
    nombreEquipo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fechaCreacion = models.DateTimeField(auto_now_add=True)
    fechaModificacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombreEquipo

    class Meta:
        db_table = 'equipo'
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'

class Miembro(models.Model):
    idMiembro = models.AutoField(primary_key=True)
    recurso = models.ForeignKey('gestion_recursos.Recurso', on_delete=models.CASCADE, related_name="miembros")
    equipo = models.ForeignKey(Equipo, on_delete=models.CASCADE, related_name="miembros")

    def __str__(self):
        return f"{self.recurso.nombreRecurso} - {self.equipo.nombreEquipo}"

    class Meta:
        db_table = 'miembro'
        verbose_name = 'Miembro'
        verbose_name_plural = 'Miembros'
