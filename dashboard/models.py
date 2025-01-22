# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = True` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.contrib.auth.models import AbstractUser
from django.db import models


class Actividad(models.Model):
    idactividad = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    idusuario = models.ForeignKey("Usuario", models.DO_NOTHING, db_column="idusuario")
    accion = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = "actividad"


class Administrador(models.Model):
    idusuario = models.OneToOneField(
        "Usuario", models.DO_NOTHING, db_column="idusuario", primary_key=True
    )

    class Meta:
        managed = True
        db_table = "administrador"


class Alerta(models.Model):
    idalerta = models.AutoField(primary_key=True)
    idtarea = models.ForeignKey("Tarea", models.DO_NOTHING, db_column="idtarea")
    tipoalerta = models.CharField(max_length=50, blank=True, null=True)
    mensaje = models.TextField()
    activa = models.BooleanField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "alerta"


class Cliente(models.Model):
    idusuario = models.OneToOneField(
        "Usuario", models.DO_NOTHING, db_column="idusuario", primary_key=True
    )

    class Meta:
        managed = True
        db_table = "cliente"


class Desarrollador(models.Model):
    idusuario = models.OneToOneField(
        "Usuario", models.DO_NOTHING, db_column="idusuario", primary_key=True
    )
    tareascompletadas = models.IntegerField(blank=True, null=True)
    tiempototalempleado = models.DurationField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "desarrollador"


class Entradamodeloestimacionrnn(models.Model):
    idmodelo = models.ForeignKey(
        "Modeloestimacionrnn", models.DO_NOTHING, db_column="idmodelo"
    )
    funcionentrada = models.TextField(blank=True, null=True)
    tipodato = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "entradamodeloestimacionrnn"


class Equipo(models.Model):
    idequipo = models.AutoField(primary_key=True)
    nombreequipo = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "equipo"


class Historialalerta(models.Model):
    idhistorial = models.AutoField(primary_key=True)
    idalerta = models.ForeignKey(Alerta, models.DO_NOTHING, db_column="idalerta")
    fecharesolucion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "historialalerta"


class Historialnotificacion(models.Model):
    idhistorial = models.AutoField(primary_key=True)
    idnotificacion = models.ForeignKey(
        "Notificacion", models.DO_NOTHING, db_column="idnotificacion"
    )
    fechalectura = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "historialnotificacion"


class Historialreporte(models.Model):
    idhistorialreporte = models.AutoField(primary_key=True)
    idreporte = models.ForeignKey("Reporte", models.DO_NOTHING, db_column="idreporte")
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    descripcioncambio = models.TextField()

    class Meta:
        managed = True
        db_table = "historialreporte"


class Historialreporteusuario(models.Model):
    idhistorialreporteusuario = models.AutoField(primary_key=True)
    idreporteusuario = models.ForeignKey(
        "Reporteusuario", models.DO_NOTHING, db_column="idreporteusuario"
    )
    cambio = models.TextField()
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "historialreporteusuario"


class Historialtarea(models.Model):
    idhistorialtarea = models.AutoField(primary_key=True)
    idtarea = models.ForeignKey("Tarea", models.DO_NOTHING, db_column="idtarea")
    fechacambio = models.DateTimeField(blank=True, null=True)
    descripcioncambio = models.TextField()

    class Meta:
        managed = True
        db_table = "historialtarea"


class Jefeproyecto(models.Model):
    idusuario = models.OneToOneField(
        "Usuario", models.DO_NOTHING, db_column="idusuario", primary_key=True
    )
    proyectosgestionados = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "jefeproyecto"


class Miembro(models.Model):
    idmiembro = models.AutoField(primary_key=True)
    idrecurso = models.ForeignKey("Recurso", models.DO_NOTHING, db_column="idrecurso")
    idequipo = models.ForeignKey(Equipo, models.DO_NOTHING, db_column="idequipo")

    class Meta:
        managed = True
        db_table = "miembro"


class Modeloestimacionrnn(models.Model):
    idmodelo = models.AutoField(primary_key=True)
    nombremodelo = models.CharField(max_length=255)
    descripcionmodelo = models.TextField(blank=True, null=True)
    versionmodelo = models.CharField(max_length=50, blank=True, null=True)
    precision = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "modeloestimacionrnn"


class Monitoreotarea(models.Model):
    idtarea = models.OneToOneField(
        "Tarea", models.DO_NOTHING, db_column="idtarea", primary_key=True
    )
    fechainicioreal = models.DateField(blank=True, null=True)
    fechafinreal = models.DateField(blank=True, null=True)
    porcentajecompletado = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    alertagenerada = models.BooleanField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "monitoreotarea"


class Notificacion(models.Model):
    idnotificacion = models.AutoField(primary_key=True)
    idusuario = models.ForeignKey("Usuario", models.DO_NOTHING, db_column="idusuario")
    mensaje = models.TextField()
    leido = models.BooleanField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    prioridad = models.CharField(
        max_length=20,
        choices=[
            ("baja", "Baja"),
            ("media", "Media"),
            ("alta", "Alta"),
        ],
        default="media",
    )
    categoria = models.CharField(
        max_length=20,
        choices=[
            ("Frontend", "Frontend"),
            ("Backend", "Backend"),
            ("QA", "QA"),
            ("Otro", "Otro"),
        ],
        default="media",
    )
    archivada = models.BooleanField(default=False)
    fecha_recordatorio = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "notificacion"


class Proyecto(models.Model):
    idproyecto = models.AutoField(primary_key=True)
    nombreproyecto = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)
    idequipo = models.ForeignKey(
        Equipo, models.DO_NOTHING, db_column="idequipo", blank=True, null=True
    )
    fechainicio = models.DateField(blank=True, null=True)
    fechafin = models.DateField(blank=True, null=True)
    presupuesto = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    presupuestoutilizado = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    estado = models.CharField(max_length=50, blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "proyecto"


class Recurso(models.Model):
    idrecurso = models.AutoField(primary_key=True)
    nombrerecurso = models.CharField(max_length=255)
    idtiporecurso = models.ForeignKey(
        "Tiporecurso", models.DO_NOTHING, db_column="idtiporecurso"
    )
    disponibilidad = models.BooleanField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "recurso"


class Recursohumano(models.Model):
    idrecurso = models.OneToOneField(
        Recurso, models.DO_NOTHING, db_column="idrecurso", primary_key=True
    )
    cargo = models.CharField(max_length=255, blank=True, null=True)
    habilidades = models.TextField(blank=True, null=True)
    tarifahora = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    idusuario = models.ForeignKey(
        "Usuario", models.DO_NOTHING, db_column="idusuario", blank=True, null=True
    )

    class Meta:
        managed = True
        db_table = "recursohumano"


class Recursomaterial(models.Model):
    idrecurso = models.OneToOneField(
        Recurso, models.DO_NOTHING, db_column="idrecurso", primary_key=True
    )
    costounidad = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    fechacompra = models.DateField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "recursomaterial"


class Reporte(models.Model):
    idreporte = models.AutoField(primary_key=True)
    tiporeporte = models.CharField(max_length=50)
    fechageneracion = models.DateTimeField(blank=True, null=True)
    idproyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column="idproyecto")

    class Meta:
        managed = True
        db_table = "reporte"


class Reporteusuario(models.Model):
    idreporteusuario = models.AutoField(primary_key=True)
    idreporte = models.ForeignKey(Reporte, models.DO_NOTHING, db_column="idreporte")
    idusuario = models.ForeignKey("Usuario", models.DO_NOTHING, db_column="idusuario")
    descripcion = models.TextField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "reporteusuario"


class Requerimiento(models.Model):
    idrequerimiento = models.AutoField(primary_key=True)
    descripcion = models.TextField()
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    idproyecto = models.ForeignKey(Proyecto, models.DO_NOTHING, db_column="idproyecto")

    class Meta:
        managed = True
        db_table = "requerimiento"


class Resultadosrnn(models.Model):
    idtarea = models.OneToOneField(
        "Tarea", models.DO_NOTHING, db_column="idtarea", primary_key=True
    )  # The composite primary key (idtarea, idmodelo) found, that is not supported. The first column is selected.
    idmodelo = models.IntegerField()
    duracionestimada = models.IntegerField(blank=True, null=True)
    costoestimado = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    timestamp = models.DateTimeField(blank=True, null=True)
    recursos = models.TextField(blank=True, null=True)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "resultadosrnn"
        unique_together = (("idtarea", "idmodelo"),)


class Rolmoduloacceso(models.Model):
    idrolmodulo = models.AutoField(primary_key=True)
    nombrerol = models.CharField(max_length=50)
    modulo = models.CharField(max_length=255)
    permisos = models.CharField(max_length=50)

    class Meta:
        managed = True
        db_table = "rolmoduloacceso"


class Salidamodeloestimacionrnn(models.Model):
    idmodelo = models.ForeignKey(
        Modeloestimacionrnn, models.DO_NOTHING, db_column="idmodelo"
    )
    metricasalida = models.TextField(blank=True, null=True)
    tipodato = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = "salidamodeloestimacionrnn"


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
    tipo_tarea = models.CharField(
        max_length=20,
        choices=[
            ("frontend", "Frontend"),
            ("backend", "Backend"),
            ("database", "Database"),
            ("testing", "testing"),
            ("deployment", "Deployment"),
        ],
        default="media",
    )
    costoestimado = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    costoactual = models.DecimalField(
        max_digits=15, decimal_places=2, blank=True, null=True
    )
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    idrequerimiento = models.ForeignKey(
        Requerimiento, models.DO_NOTHING, db_column="idrequerimiento"
    )

    class Meta:
        managed = True
        db_table = "tarea"


class Tarearecurso(models.Model):
    idtarearecurso = models.AutoField(primary_key=True)
    idtarea = models.ForeignKey(
        Tarea, models.DO_NOTHING, db_column="idtarea"
    )
    idrecurso = models.ForeignKey(Recurso, models.DO_NOTHING, db_column="idrecurso")
    cantidad = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tarearecurso"
        unique_together = (("idtarea", "idrecurso"),)


class Tester(models.Model):
    idusuario = models.OneToOneField(
        "Usuario", models.DO_NOTHING, db_column="idusuario", primary_key=True
    )

    class Meta:
        managed = True
        db_table = "tester"


class Tiporecurso(models.Model):
    idtiporecurso = models.AutoField(primary_key=True)
    nametiporecurso = models.CharField(max_length=255)
    descripcion = models.TextField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = "tiporecurso"


class Usuario(AbstractUser):
    idusuario = models.AutoField(primary_key=True)
    nombreusuario = models.CharField(max_length=255, unique=True)
    email = models.CharField(unique=True, max_length=255)
    contrasena = models.CharField(max_length=255)
    rol = models.CharField(max_length=50)
    fechacreacion = models.DateTimeField(blank=True, null=True)
    fechamodificacion = models.DateTimeField(blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    confirmado = models.BooleanField(blank=True, null=True)

    # Obligatorio para modelos de usuario personalizados
    USERNAME_FIELD = "nombreusuario"  # Este campo debe ser un string
    REQUIRED_FIELDS = [
        "email"
    ]  # Campos adicionales requeridos para crear un superusuario

    class Meta:
        managed = True
        db_table = "usuario"

    def __str__(self):
        return self.nombreusuario


class Usuariorolmodulo(models.Model):
    idusuario = models.OneToOneField(
        Usuario, models.DO_NOTHING, db_column="idusuario", primary_key=True
    )  # The composite primary key (idusuario, idrolmodulo) found, that is not supported. The first column is selected.
    idrolmodulo = models.ForeignKey(
        Rolmoduloacceso, models.DO_NOTHING, db_column="idrolmodulo"
    )

    class Meta:
        managed = True
        db_table = "usuariorolmodulo"
        unique_together = (("idusuario", "idrolmodulo"),)
