# WebApp-PM: Gestión Inteligente de Proyectos 🚀

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://www.djangoproject.com/)
[![TensorFlow](https://img.shields.io/badge/TensorFlow-2.0+-orange.svg)](https://tensorflow.org/)
[![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](docker-compose.yml)
[![Kubernetes](https://img.shields.io/badge/Kubernetes-Ready-blue.svg)](k8s/)

Sistema inteligente de gestión de proyectos informáticos con estimación de tiempos mediante redes neuronales LSTM 🧠

## ✨ Características

-   👥 **Gestión de Usuarios**: Sistema de roles y permisos
-   📊 **Dashboard Interactivo**: Visualización en tiempo real
-   📋 **Gestión de Proyectos**: Seguimiento completo del ciclo de vida
-   ⏱️ **Estimación Inteligente**: Predicción de tiempos con LSTM
-   📱 **Notificaciones**: Sistema de alertas en tiempo real
-   📈 **Reportes Automáticos**: Generación de informes detallados
-   🔄 **Integración**: Conexión con Jira y Trello

## 🛠️ Instalación

### Usando Python venv

```sh
# Clonar el repositorio
git clone https://github.com/sandovaldavid/WebApp-PM.git
cd WebApp-PM

# Crear entorno virtual
python -m venv env
source env/bin/activate  # Linux/MacOS
env\Scripts\activate     # Windows

# Instalar dependencias
pip install -r requirements.txt
pip install -r requirements-ml.txt
```

### Usando Conda

```sh
# Clonar el repositorio
git clone https://github.com/sandovaldavid/WebApp-PM.git
cd WebApp-PM

# Crear entorno conda
conda create -n webapp-pm python=3.10
conda activate webapp-pm

# Instalar dependencias
conda install --file requirements.txt
conda install --file requirements-ml.txt

# Crear entorno local en conda
conda create -p ./env python=3.10
conda activate ./env

pip install -r requirements.txt
pip install -r requirements-ml.txt
```

### ⚙️ Configuración

1. Configurar variables de entorno:

```sh
cp .env.example .env
# Editar .env con tus configuraciones
```

2. Inicializar la base de datos:

```sh
python manage.py migrate
python manage.py createsuperuser
```

3. Cargar datos de prueba:

```sh
python manage.py shell < script/data_v2.py
```

## 🚀 Uso

### Desarrollo local

```sh
python manage.py runserver
```

### Docker 🐳

```sh
docker-compose up --build
```

### Kubernetes ☸️

```sh
kubectl create namespace webapp-pm
kubectl apply -f k8s/
```

## 🧠 Modelo de ML

El sistema utiliza una red neuronal LSTM para estimar la duración de tareas basándose en:

-   Complejidad del proyecto
-   Prioridad
-   Tipo de tarea
-   Histórico de proyectos similares

El modelo se encuentra en redes_neuronales y se entrena automáticamente con datos históricos.

## 🤝 Contribuciones

1. Fork el repositorio
2. Crea una rama (`git checkout -b feature/amazing`)
3. Commit tus cambios (`git commit -m 'Add amazing feature'`)
4. Push a la rama (`git push origin feature/amazing`)
5. Abre un Pull Request

### Guía de Contribución

-   Sigue el estilo de código PEP 8
-   Añade pruebas para nueva funcionalidad
-   Actualiza la documentación según sea necesario
-   Verifica que los tests pasen antes de enviar PR

## 📝 Licencia

Este proyecto está bajo la Licencia GNU Affero General Public License v3.0 - ver el archivo [LICENSE](LICENSE) para detalles.

También debe actualizarse el badge de la licencia en la parte superior:

[![License](https://img.shields.io/badge/License-AGPL%20v3-blue.svg)](LICENSE)

## 📊 Estructura del Proyecto

-   📁 **auditoria/**: Sistema de auditoría
-   📁 **dashboard/**: Interfaz principal
-   📁 **gestion_equipos/**: Gestión de equipos
-   📁 **gestion_proyectos/**: Control de proyectos
-   📁 **gestion_tareas/**: Administración de tareas
-   📁 **redes_neuronales/**: Modelos LSTM
-   📁 **webapp/**: Configuración Django

## 📫 Contacto

-   Crear un [issue](https://github.com/sandovaldavid/WebApp-PM/issues)
-   Enviar un PR
