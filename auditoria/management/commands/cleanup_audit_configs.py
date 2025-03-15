from django.core.management.base import BaseCommand
from django.db.models import Count
from dashboard.models import ConfiguracionAuditoria
from django.db import transaction


class Command(BaseCommand):
    help = 'Limpia configuraciones de auditoría duplicadas dejando solo una por modelo'

    def handle(self, *args, **options):
        with transaction.atomic():
            # Encontrar modelos con configuraciones duplicadas (mismo modelo y campo nulo)
            duplicados = (
                ConfiguracionAuditoria.objects.filter(campo__isnull=True)
                .values('modelo')
                .annotate(count=Count('modelo'))
                .filter(count__gt=1)
            )

            total_duplicados = 0
            total_eliminados = 0

            # Procesar cada modelo con duplicados
            for dup in duplicados:
                modelo = dup['modelo']
                configs = ConfiguracionAuditoria.objects.filter(
                    modelo=modelo, campo__isnull=True
                ).order_by('idconfiguracion')

                if configs.count() <= 1:
                    continue

                # Mantener la primera configuración y eliminar las demás
                config_principal = configs.first()
                self.stdout.write(
                    f"Modelo {modelo}: manteniendo configuración ID {config_principal.idconfiguracion}"
                )

                # Eliminar todas las demás configuraciones
                eliminar_ids = list(
                    configs.exclude(
                        idconfiguracion=config_principal.idconfiguracion
                    ).values_list('idconfiguracion', flat=True)
                )
                total_eliminados += len(eliminar_ids)
                total_duplicados += 1

                self.stdout.write(
                    f"  - Eliminando {len(eliminar_ids)} configuraciones duplicadas: {eliminar_ids}"
                )
                ConfiguracionAuditoria.objects.filter(
                    idconfiguracion__in=eliminar_ids
                ).delete()

        self.stdout.write(
            self.style.SUCCESS(
                f'Limpieza completada: {total_duplicados} modelos con duplicados, {total_eliminados} configuraciones eliminadas'
            )
        )
