#!/bin/bash
# start-dev.sh

# Esperar a que la base de datos esté lista
echo "Esperando a que PostgreSQL esté listo..."
while ! pg_isready -h $DB_HOST -p $DB_PORT -U $DB_USER
do
    sleep 2
done

# Aplicar migraciones
python manage.py migrate

# Iniciar servidor de desarrollo
python manage.py runserver 0.0.0.0:8000