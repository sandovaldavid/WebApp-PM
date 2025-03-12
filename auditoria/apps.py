from django.apps import AppConfig

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'
    
    def ready(self):
        """Importar las señales cuando se inicialice la app"""
        from . import signals
        signals.register_signals()
