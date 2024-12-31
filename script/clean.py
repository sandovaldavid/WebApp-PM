from django.apps import apps
from django.db import connection, transaction

# Obtener todos los modelos registrados en tu proyecto
models = apps.get_models()

# Limpiar las tablas y reiniciar las secuencias
with transaction.atomic():
    with connection.cursor() as cursor:
        print("Limpiando tablas y reseteando contadores...")
        for model in models:
            table_name = model._meta.db_table
            primary_key = model._meta.pk.name

            # Eliminar datos de la tabla
            cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY CASCADE;")
            print(f"Tabla '{table_name}' limpiada y contador reiniciado.")

print("Limpieza completada con contadores reiniciados.")
