from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
from dashboard.models import Actividad


class Command(BaseCommand):
    help = 'Elimina actividades redundantes en la base de datos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de días hacia atrás para buscar y limpiar (default: 30)',
        )
        parser.add_argument(
            '--window',
            type=int,
            default=5,
            help='Ventana de tiempo en segundos para considerar actividades como redundantes (default: 5)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Solo mostrar qué se eliminaría sin realizar cambios',
        )

    def handle(self, *args, **options):
        days = options['days']
        window = options['window']
        dry_run = options['dry_run']

        self.stdout.write(
            self.style.NOTICE(
                f"Buscando actividades redundantes en los últimos {days} días..."
            )
        )

        # Obtener todas las actividades de modificación en el período especificado
        start_date = timezone.now() - timedelta(days=days)
        activities = Actividad.objects.filter(
            fechacreacion__gte=start_date, accion='MODIFICACION'
        ).order_by('entidad_tipo', 'entidad_id', 'fechacreacion')

        self.stdout.write(f"Encontradas {activities.count()} actividades para analizar")

        # Agrupar por entidad
        groups = {}
        for act in activities:
            if not act.entidad_tipo or not act.entidad_id:
                continue

            key = f"{act.entidad_tipo}_{act.entidad_id}"

            if key not in groups:
                groups[key] = []

            groups[key].append(act)

        # Buscar redundantes en cada grupo
        redundant_ids = []
        for key, acts in groups.items():
            if len(acts) <= 1:
                continue

            # Verificar actividades en ventanas de tiempo cercanas
            for i in range(len(acts) - 1):
                current = acts[i]
                next_act = acts[i + 1]

                time_diff = (
                    next_act.fechacreacion - current.fechacreacion
                ).total_seconds()

                # Si están muy cerca en tiempo, marcar la segunda como redundante
                if time_diff < window:
                    redundant_ids.append(next_act.idactividad)
                    self.stdout.write(
                        f"  Redundante: ID {next_act.idactividad}, {time_diff:.2f}s después de ID {current.idactividad}"
                    )

        # Eliminar las actividades redundantes
        if redundant_ids:
            self.stdout.write(
                self.style.WARNING(
                    f"Se encontraron {len(redundant_ids)} actividades redundantes"
                )
            )

            if not dry_run:
                with transaction.atomic():
                    # Primero eliminar detalles
                    from dashboard.models import DetalleActividad

                    DetalleActividad.objects.filter(
                        idactividad__idactividad__in=redundant_ids
                    ).delete()

                    # Luego eliminar las actividades
                    deleted = Actividad.objects.filter(
                        idactividad__in=redundant_ids
                    ).delete()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"Eliminadas {deleted[0]} actividades redundantes"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.NOTICE("Modo simulación: No se realizaron cambios")
                )
        else:
            self.stdout.write(
                self.style.SUCCESS("No se encontraron actividades redundantes")
            )
