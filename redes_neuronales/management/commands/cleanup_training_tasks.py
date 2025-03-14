from django.core.management.base import BaseCommand
from redes_neuronales.tasks import cleanup_completed_tasks

class Command(BaseCommand):
    help = 'Limpia las tareas de entrenamiento completadas que han superado el tiempo máximo'

    def add_arguments(self, parser):
        parser.add_argument('--hours', type=int, default=24, help='Edad máxima de tareas en horas')

    def handle(self, *args, **options):
        max_age_hours = options['hours']
        removed = cleanup_completed_tasks(max_age_hours)
        self.stdout.write(self.style.SUCCESS(f'Se eliminaron {removed} tareas completadas antiguas'))