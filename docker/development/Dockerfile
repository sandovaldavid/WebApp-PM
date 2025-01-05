# Dockerfile.dev
FROM python:3.12-slim-bullseye as base

# Evitar mensajes de Python
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Instalar dependencias del sistema básicas
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    postgresql-client \
    git \
    && rm -rf /var/lib/apt/lists/*

# Crear usuario no root
RUN useradd -m -s /bin/bash developer

# Crear y configurar directorio de trabajo
WORKDIR /app
RUN chown developer:developer /app

# Cambiar al usuario no root
USER developer

# Configurar entorno virtual Python
RUN python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Instalar dependencias de Python
COPY --chown=developer:developer requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Instalar dependencias adicionales para desarrollo
RUN pip install django-debug-toolbar \
    pytest \
    pytest-django \
    coverage \
    black \
    isort \
    pylint

# Copiar el código del proyecto
COPY --chown=developer:developer . .

# Exponer puerto
EXPOSE 8000

# Script para iniciar el servidor en modo desarrollo
COPY --chown=developer:developer docker/development/start-dev.sh /app/start-dev.sh
RUN chmod +x /app/start-dev.sh

CMD ["/app/start-dev.sh"]