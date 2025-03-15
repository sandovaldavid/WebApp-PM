from django.core.management.base import BaseCommand
from dashboard.models import Actividad
from django.db.models import Count
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Comprueba y muestra actividades redundantes en la auditoría'

    def handle(self, *args, **options):
        # Buscar actividades de modificación que ocurrieron en un intervalo corto de tiempo (5 segundos)
        window = 5  # segundos

        # Obtener todas las actividades de los últimos 30 días
        recent_activities = Actividad.objects.filter(
            fechacreacion__gte=timezone.now() - timedelta(days=30),
            accion='MODIFICACION',
        ).order_by('fechacreacion')

        # Agrupar por entidad y aproximación de tiempo
        redundancy_groups = {}

        for act in recent_activities:
            if not act.entidad_tipo or not act.entidad_id:
                continue

            key = f"{act.entidad_tipo}_{act.entidad_id}"
            timestamp = act.fechacreacion.timestamp()

            if key not in redundancy_groups:
                redundancy_groups[key] = []

            # Buscar si ya existe una actividad cercana en tiempo
            found_group = False
            for group in redundancy_groups[key]:
                for existing_act in group:
                    if abs(existing_act.fechacreacion.timestamp() - timestamp) < window:
                        group.append(act)
                        found_group = True
                        break
                if found_group:
                    break

            if not found_group:
                redundancy_groups[key].append([act])

        # Mostrar grupos con más de una actividad (redundantes)
        redundant_count = 0
        for key, groups in redundancy_groups.items():
            for group in groups:
                if len(group) > 1:
                    redundant_count += 1
                    self.stdout.write(
                        self.style.WARNING(
                            f"Actividades redundantes encontradas para {key}: {len(group)} actividades"
                        )
                    )
                    for act in group:
                        self.stdout.write(
                            f"  - ID: {act.idactividad}, Fecha: {act.fechacreacion}, Usuario: {act.idusuario.nombreusuario}"
                        )

        if redundant_count == 0:
            self.stdout.write(
                self.style.SUCCESS("No se encontraron actividades redundantes")
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Se encontraron {redundant_count} grupos de actividades redundantes"
                )
            )
