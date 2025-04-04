from django.utils import timezone
from datetime import timedelta
from dashboard.models import Alerta
from .services import MonitoreoService, NotificacionService


def verificar_y_crear_alertas():
    # Verificar tareas retrasadas
    alertas_retraso = MonitoreoService.verificar_tareas_retrasadas()

    # Verificar presupuestos excedidos
    alertas_presupuesto = MonitoreoService.verificar_presupuesto_excedido()

    # Verificar tareas bloqueadas
    alertas_bloqueo = MonitoreoService.verificar_tareas_bloqueadas()

    # Para cada nueva alerta creada, notificar a los usuarios
    alertas_nuevas = Alerta.objects.filter(
        fechacreacion__gte=timezone.now() - timedelta(minutes=10)
    )
    for alerta in alertas_nuevas:
        NotificacionService.notificar_alerta_a_usuarios(alerta)

    return f"Alertas creadas: {alertas_retraso + alertas_presupuesto + alertas_bloqueo}"
