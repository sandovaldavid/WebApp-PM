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
    git clone https://github.com/sandovaldavid/WebApp-PM.git
    cd WebApp-PM
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

### Scripts

#### Limpiar Base de Datos

``` sh
python manage.py shell < script/clean_db.py     
```

#### Limpiar tablas y reiniciar contador de Id's

``` sh
python manage.py shell < script/clean_tables.py   
```

#### Poblar Base de Datos con datos de prueba

``` sh
python manage.py shell < script/data.py  
```

### Archivo `.env`

```sh
DB_NAME=Db-Web-App-PM
DB_USER=development
DB_PASSWORD=123456
DB_HOST=db-web-app
DB_PORT=5432

# Mailtrap configuration
EMAIL_HOST=
EMAIL_PORT=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
```

### Kubernetes

#### Imagenes de forma local

1. **Construye las imágenes locales con Docker Compose**:

    ```sh
    docker-compose build
    ```

2. **Etiqueta las imágenes locales para que sean accesibles por Kubernetes**:

    ```sh
    docker tag webapp-pm-web:latest localhost:5000/webapp-pm-backend:latest
    ```

3. **Inicia un registro local de Docker** (si no tienes uno ya corriendo):

    ```sh
    docker run -d -p 5000:5000 --name registry registry:2
    ```

4. **Empuja las imágenes al registro local**:

    ```sh
    docker push localhost:5000/apv-backend:latest
    docker push localhost:5000/apv-frontend:latest
    ```

#### Deploy

1. Primero, asegúrate de tener un cluster de Kubernetes funcionando (puedes usar Docker Desktop con Kubernetes habilitado):

    ```sh
    # Verifica que Kubernetes está funcionando
    kubectl cluster-info
    ```

2. Crea el namespace para tu aplicación

    ```sh
    kubectl create namespace webapp-pm
    ```

3. Aplica las configuraciones en orden

    ```sh
    # Aplicar configuraciones y secretos
    kubectl apply -f k8s/config.yaml

    # Aplicar storage para PostgreSQL
    kubectl apply -f k8s/storage.yaml

    # Aplicar deployment de PostgreSQL
    kubectl apply -f k8s/postgres-deployment.yaml

    # Aplicar deployment de Django
    kubectl apply -f k8s/django-deployment.yaml

    # Aplicar servicios
    kubectl apply -f k8s/services.yaml
    ```

4. Verifica que todo esté funcionando:

    ```sh
    # Ver todos los recursos en tu namespace
    kubectl get all -n webapp-pm

    # Ver pods
    kubectl get pods -n webapp-pm

    # Ver servicios
    kubectl get services -n webapp-pm

    # Ver logs de un pod específico (reemplaza <pod-name> con el nombre real del pod)
    kubectl logs -n webapp-pm <pod-name>
    ```

5. Para acceder a tu aplicación:

    ```sh
    # La aplicación estará disponible en:
    http://localhost
    ```

6. Comandos útiles para diagnóstico

    ```sh
    # Describir un pod (para ver errores detallados)
    kubectl describe pod -n webapp-pm <pod-name>

    # Ver logs en tiempo real
    kubectl logs -f -n webapp-pm <pod-name>

    # Ejecutar comandos dentro de un pod
    kubectl exec -it -n webapp-pm <pod-name> -- /bin/bash
    ```

7. Para detener y limpiar

    ```sh
    # Eliminar todos los recursos
    kubectl delete -f k8s/

    # O eliminar el namespace completo
    kubectl delete namespace webapp-pm
    ```

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
