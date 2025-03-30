import logging
from django_apscheduler.jobstores import DjangoJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from django_apscheduler.models import DjangoJobExecution
from django.conf import settings
from django.utils import timezone
import sys
from datetime import datetime

from notificaciones.cron import verificar_y_crear_alertas

logger = logging.getLogger(__name__)

def delete_old_job_executions(max_age=604_800):
    """
    Elimina ejecuciones de trabajos antiguas del historial de trabajos (por defecto: 7 días).
    Esto ayuda a prevenir que la tabla de historial crezca indefinidamente.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)

def start_scheduler():
    """
    Configura e inicia el scheduler con las tareas programadas.
    """
    scheduler = BackgroundScheduler()
    scheduler.add_jobstore(DjangoJobStore(), "default")
    
    # Añadir el trabajo para verificar y crear alertas (cada 6 horas)
    scheduler.add_job(
        verificar_y_crear_alertas,
        trigger=IntervalTrigger(hours=6),
        id="verificar_alertas",  # ID único para este trabajo
        name="Verificar y crear alertas",
        max_instances=1,
        replace_existing=True,
    )
    
    # Añadir trabajo para limpiar historial de ejecuciones (una vez por semana)
    scheduler.add_job(
        delete_old_job_executions,
        trigger=IntervalTrigger(days=7),
        id='delete_old_job_executions',
        max_instances=1,
        replace_existing=True,
    )
    
    logger.info(
        "Tareas programadas iniciadas:"
        f" verificar_alertas (cada 6 horas),"
        f" delete_old_job_executions (semanal)"
    )
    
    try:
        logger.info("Iniciando scheduler...")
        scheduler.start()
    except KeyboardInterrupt:
        logger.info("Deteniendo scheduler...")
        scheduler.shutdown()
        logger.info("Scheduler parado correctamente.")
