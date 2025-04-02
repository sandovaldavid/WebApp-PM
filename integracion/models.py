from django.db import models
from dashboard.models import Usuario


class IntegracionJira(models.Model):
    idusuario = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    url_servidor = models.URLField()
    api_key = models.CharField(max_length=255)
    token = models.CharField(max_length=255, blank=True, null=True)
    usuario_jira = models.CharField(max_length=100)
    frecuencia_sync = models.CharField(
        max_length=20,
        choices=[
            ("manual", "Manual"),
            ("hourly", "Cada hora"),
            ("daily", "Diaria"),
            ("weekly", "Semanal"),
        ],
        default="manual",
    )
    ultima_sincronizacion = models.DateTimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)

    # Opciones de configuración adicionales
    importar_issues = models.BooleanField(
        default=True, help_text="Si está activo, importa issues desde Jira"
    )
    exportar_tareas = models.BooleanField(
        default=True, help_text="Si está activo, exporta tareas locales a Jira"
    )
    sync_comentarios = models.BooleanField(
        default=True, help_text="Si está activo, sincroniza comentarios"
    )
    sincronizar_adjuntos = models.BooleanField(
        default=False, help_text="Si está activo, sincroniza archivos adjuntos"
    )

    class Meta:
        verbose_name = "Integración Jira"
        verbose_name_plural = "Integraciones Jira"
        managed = True
        db_table = "integracionjira"

    def __str__(self):
        return f"Integración Jira de {self.idusuario.nombreusuario}"


class JiraProjectMapping(models.Model):
    integracion = models.ForeignKey(IntegracionJira, on_delete=models.CASCADE)
    proyecto_local_id = models.IntegerField()
    jira_project_id = models.CharField(max_length=100)
    jira_project_key = models.CharField(max_length=20)

    class Meta:
        unique_together = ("integracion", "proyecto_local_id")
        managed = True
        db_table = "jiraprojectmapping"


class JiraTaskMapping(models.Model):
    integracion = models.ForeignKey(IntegracionJira, on_delete=models.CASCADE)
    tarea_local_id = models.IntegerField()
    jira_issue_id = models.CharField(max_length=100)
    jira_issue_key = models.CharField(max_length=20)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("integracion", "tarea_local_id")
        managed = True
        db_table = "jirataskmapping"


class JiraUserMapping(models.Model):
    integracion = models.ForeignKey(IntegracionJira, on_delete=models.CASCADE)
    usuario_local_id = models.IntegerField()
    jira_user_id = models.CharField(max_length=100)
    jira_user_key = models.CharField(max_length=100)
    jira_user_name = models.CharField(max_length=100)

    class Meta:
        unique_together = ("integracion", "usuario_local_id")
        managed = True
        db_table = "jirausermapping"


class JiraComentarioMapping(models.Model):
    integracion = models.ForeignKey(IntegracionJira, on_delete=models.CASCADE)
    actividad_local_id = models.IntegerField(null=True, blank=True)
    jira_comment_id = models.CharField(max_length=100)
    jira_issue_key = models.CharField(max_length=20)
    ultima_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("integracion", "jira_comment_id")
        managed = True
        db_table = "jiracomentariomapping"
