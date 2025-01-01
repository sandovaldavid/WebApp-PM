# Gestión de Proyectos para Consultoría Informática

Este proyecto es una aplicación web desarrollada en Django para la gestión de proyectos en una empresa de consultoría informática. La aplicación permite gestionar equipos, tareas, recursos, notificaciones, reportes y más.

## Estructura del Proyecto

- **auditoria/**: Módulo para la auditoría de acciones.
- **dashboard/**: Módulo principal del dashboard.
- **gestion_equipos/**: Gestión de equipos y miembros.
- **gestion_proyectos/**: Gestión de proyectos y requerimientos.
- **gestion_recursos/**: Gestión de recursos humanos y materiales.
- **gestion_tareas/**: Gestión de tareas y su monitoreo.
- **integracion/**: Integración con herramientas externas.
- **notificaciones/**: Gestión de notificaciones y alertas.
- **redes_neuronales/**: Modelos de redes neuronales para estimaciones.
- **reporte/**: Generación de reportes.
- **usuarios/**: Gestión de usuarios y roles.
- **webapp/**: Configuración principal del proyecto Django.

## Instalación

1. Clona el repositorio:
    ```sh
    git clone <URL_DEL_REPOSITORIO>
    cd <NOMBRE_DEL_PROYECTO>
    ```

2. Crea y activa un entorno virtual:
    ```sh
    python -m venv env
    source env/bin/activate  # En Windows usa `env\Scripts\activate`
    ```

3. Instala las dependencias:
    ```sh
    pip install -r requirements.txt
    ```

4. Realiza las migraciones:
    ```sh
    python manage.py migrate
    ```

5. Ejecuta el servidor de desarrollo:
    ```sh
    python manage.py runserver
    ```

## Uso

### Archivo `.env`

```sh
DB_NAME=Db-Web-App-PM
DB_USER=development
DB_PASSWORD=123456
DB_HOST=db-web-app
DB_PORT=5432
```


Accede a `http://127.0.0.1:8000/` en tu navegador para ver la aplicación en funcionamiento.

## Evaluación del Proyecto

### Funcionalidades Implementadas

- **Gestión de Usuarios**: Registro, autenticación y roles.
- **Gestión de Proyectos**: Creación y seguimiento de proyectos.
- **Gestión de Tareas**: Asignación y monitoreo de tareas.
- **Gestión de Recursos**: Administración de recursos humanos y materiales.
- **Notificaciones**: Alertas y notificaciones en tiempo real.
- **Reportes**: Generación de reportes detallados.
- **Integración**: Conexión con herramientas externas como Jira y Trello.

## Contribuciones

Las contribuciones son bienvenidas. Por favor, abre un issue o envía un pull request para discutir cualquier cambio que desees realizar.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo `LICENSE` para más detalles.