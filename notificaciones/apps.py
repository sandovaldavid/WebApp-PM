from django.apps import AppConfig
import sys


class NotificacionesConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "notificaciones"

    def ready(self):
        """
        Iniciar el scheduler cuando la aplicación esté lista
        Evitar cargar en comandos de gestión
        """
        if "runserver" in sys.argv:
            from notificaciones.scheduler import start_scheduler

            start_scheduler()
