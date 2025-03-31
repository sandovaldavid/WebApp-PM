from django.apps import AppConfig
import sys

class AuditoriaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'auditoria'
    
    def ready(self):
        """Importar las señales cuando se inicialice la app"""
        # No registrar señales durante las migraciones
        if 'migrate' not in sys.argv:
            from . import signals
            signals.register_signals()