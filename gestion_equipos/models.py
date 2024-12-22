from django.db import models

class Equipo(models.Model):
    idequipo = models.AutoField(primary_key=True)
    nombreequipo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        db_table = 'equipo'
        verbose_name = 'Equipo'
        verbose_name_plural = 'Equipos'

class Miembro(models.Model):
    idmiembro = models.AutoField(primary_key=True)
    idrecurso = models.ForeignKey('gestion_recursos.Recurso', models.DO_NOTHING, db_column='idrecurso')
    idequipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column='idequipo')

    class Meta:
        db_table = 'miembro'
        verbose_name = 'Miembro'
        verbose_name_plural = 'Miembros'
