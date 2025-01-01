from django.db import connection
from django.apps import apps


def drop_all_tables():
    with connection.cursor() as cursor:
        tables = connection.introspection.table_names()
        for table in tables:
            if table in connection.introspection.django_table_names():
                print(f"Dropping table {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE;")


# Run the function
drop_all_tables()