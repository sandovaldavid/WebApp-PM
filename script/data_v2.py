from django.db.models.signals import pre_save, post_save, post_delete
from auditoria.signals import audit_post_save, audit_post_delete, pre_save_handler

# Desconectar señales de auditoría
pre_save.disconnect(pre_save_handler)
post_save.disconnect(audit_post_save)
post_delete.disconnect(audit_post_delete)

from django.utils.timezone import now
from dashboard.models import (
    Administrador,
    Jefeproyecto,
    Desarrollador,
    Tester,
    Recurso,
    Tiporecurso,
    Recursohumano,
    Recursomaterial,
    Equipo,
    Proyecto,
    Miembro,
    Usuario,
    Notificacion,
    Historialnotificacion,
    Requerimiento,
    Tarea,
    Historialtarea,
    Tarearecurso,
    Alerta,
    Historialalerta,
    # Nuevos modelos importados
    TipoTarea,
    Fase,
    TareaComun,
    TareaTareaComun,
    HistorialEquipo,
)
from script.random_user import generar_usuarios
from faker import Faker
from django.utils import timezone
import random

print("Iniciando generación de datos de prueba...")
fake = Faker()

# Crear tipos de tareas iniciales
print("---------------------( Creando tipos de tareas ...)---------------------")
tipos_tarea = [
    {
        "nombre": "Frontend",
        "descripcion": "Desarrollo de interfaces de usuario y experiencia de usuario",
    },
    {
        "nombre": "Backend",
        "descripcion": "Desarrollo de lógica de negocio y servicios de servidor",
    },
    {"nombre": "Database", "descripcion": "Tareas relacionadas con bases de datos"},
    {"nombre": "Testing", "descripcion": "Pruebas y aseguramiento de calidad"},
    {"nombre": "DevOps", "descripcion": "Infraestructura y despliegue"},
    {
        "nombre": "Documentación",
        "descripcion": "Elaboración de documentación técnica y de usuario",
    },
    {
        "nombre": "Análisis",
        "descripcion": "Análisis de requerimientos y diseño de soluciones",
    },
]

tipo_tarea_objects = {}
for tipo in tipos_tarea:
    obj = TipoTarea.objects.create(
        nombre=tipo["nombre"],
        descripcion=tipo["descripcion"],
    )
    tipo_tarea_objects[tipo["nombre"]] = obj
    print(f"Tipo de tarea '{tipo['nombre']}' creado")

# Crear fases iniciales
print("---------------------( Creando fases ...)---------------------")
fases = [
    {
        "nombre": "Inicio/Conceptualización",
        "descripcion": "Fase inicial del proyecto",
        "orden": 1,
    },
    {
        "nombre": "Elaboración/Requisitos",
        "descripcion": "Definición y análisis de requisitos",
        "orden": 2,
    },
    {
        "nombre": "Construcción/Desarrollo",
        "descripcion": "Implementación de la solución",
        "orden": 3,
    },
    {
        "nombre": "Transición/Implementación",
        "descripcion": "Despliegue y entrega",
        "orden": 4,
    },
    {
        "nombre": "Mantenimiento",
        "descripcion": "Soporte y mantenimiento post-implementación",
        "orden": 5,
    },
]

fase_objects = {}
for fase in fases:
    obj = Fase.objects.create(
        nombre=fase["nombre"],
        descripcion=fase["descripcion"],
        orden=fase["orden"],
    )
    fase_objects[fase["nombre"]] = obj
    print(f"Fase '{fase['nombre']}' creada")

print("---------------------( Creando usuarios ...)---------------------")

try:
    # Crear un usuario administrador
    usuarios_admin = generar_usuarios(1, "Administrador")
    if usuarios_admin:
        usuario_admin = usuarios_admin[0]
        admin = Administrador.objects.create(idusuario=usuario_admin)
        print("Administrador creados exitosamente")
    else:
        print("No se pudo crear el usuario administrador")

    # Crear usuario Jefe de Proyecto
    JefeProyecto = generar_usuarios(5, "Jefe de Proyecto")
    if JefeProyecto:
        for jefe in JefeProyecto:
            Jefeproyecto.objects.create(idusuario=jefe)
        print("Jefes de Proyecto creados exitosamente")
    else:
        print("No se pudieron crear los Jefes de Proyecto")

    # Crear usuardesarroladores ios para Recursos Humanos
    desarroladores = generar_usuarios(10, "Desarrollador")
    if desarroladores:
        for desarrolador in desarroladores:
            Desarrollador.objects.create(idusuario=desarrolador)
        print("Desarroladores creados exitosamente")
    else:
        print("No se pudieron crear los Desarroladores")

    # Crear testes para Recursos Humanos
    testers = generar_usuarios(10, "Desarrollador")
    if testers:
        for tester in testers:
            Tester.objects.create(idusuario=tester)
        print("Testers creados exitosamente")
    else:
        print("No se pudieron crear los Testers")
except Exception as e:
    print(f"Error en el proceso: {str(e)}")

print("---------------------( Usuarios creados exitosamente )---------------------")

print("---------------------( Creando Tipo de Recurso ...)---------------------")

tipo_humano = Tiporecurso.objects.create(
    nametiporecurso="Recurso Humano",
    descripcion="Recursos humanos asignados a proyectos y tareas.",
)

tipo_software = Tiporecurso.objects.create(
    nametiporecurso="Software",
    descripcion="Licencias y herramientas de software utilizadas en proyectos.",
)

tipo_hardware = Tiporecurso.objects.create(
    nametiporecurso="Hardware",
    descripcion="Equipos y dispositivos físicos utilizados en proyectos.",
)
print(
    "---------------------( Tipos de Recurso creados exitosamente )---------------------"
)

print("---------------------( Creando Recursos ...)---------------------")

print("Creando recursos humanos - Desarroladores...")

frontend_skills = [
    "HTML5, CSS3, JavaScript ES6+, React.js, Redux, Responsive Design, Bootstrap, SASS",
    "Vue.js, Nuxt.js, TypeScript, Webpack, Jest, CSS Grid, Flexbox, UI/UX principles",
    "React Native, Next.js, Material-UI, Tailwind CSS, GraphQL, PWA development",
    "Angular, RxJS, SCSS, Cypress, WebPack, Performance optimization, Cross-browser compatibility",
    "JavaScript frameworks, CSS preprocessors, Component libraries, Web accessibility, SEO best practices",
]

backend_skills = [
    "Python, Django, DRF, PostgreSQL, Redis, Celery, Docker, AWS, CI/CD pipelines",
    "Node.js, Express.js, MongoDB, GraphQL, REST APIs, Microservices, RabbitMQ, Kubernetes",
    "Java, Spring Boot, Hibernate, MySQL, JUnit, Maven, Jenkins, Swagger, OAuth2",
    "PHP, Laravel, Symfony, MariaDB, Memcached, RESTful Services, Unit Testing, Git flow",
    "Python, FastAPI, SQLAlchemy, Redis, Docker, Kubernetes, gRPC, Message Queues",
]

qa_skills = [
    "Selenium, Cucumber, JUnit, TestNG, Jenkins, JIRA, Manual Testing, Test Cases Design",
    "Postman, REST API Testing, Performance Testing with JMeter, SQL, Bug Tracking, Test Plans",
    "Cypress, Jest, Mocha, End-to-End Testing, Load Testing, Security Testing, TestRail",
    "Python, PyTest, Robot Framework, Continuous Integration, Bug Life Cycle, Test Documentation",
    "Automated Testing, Performance Testing, Mobile Testing, Cross-browser Testing, Agile Testing",
    "Test Automation Frameworks, Test Management Tools, Test Data Management, Test Strategy Planning",
    "API Testing, Web Testing, Mobile App Testing, Test Automation Tools, Test Reporting",
]

frontend_names = [
    "Diseñador UX/UI",
    "Frontend Developer Senior",
    "Desarrollador UI/UX",
    "Frontend React Specialist",
    "Ingeniero Frontend Angular",
    "Desarrollador Web Frontend",
    "Frontend Vue.js Developer",
    "Desarrollador Frontend Mobile",
    "Frontend Architect",
    "Frontend Performance Engineer",
    "Desarrollador Frontend Full Stack",
]

backend_names = [
    "Backend Developer Senior",
    "Python/Django Developer",
    "Node.js Backend Engineer",
    "Java Backend Specialist",
    "Arquitecto Backend",
    "Backend DevOps Engineer",
    "Desarrollador API REST",
    "Backend Cloud Engineer",
    "Ingeniero Backend Go",
    "Backend Systems Developer",
]

# Añadimos carga_trabajo a los recursos
Recurso.objects.create(
    nombrerecurso=frontend_names[0],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    carga_trabajo=0.75,  # 75% de carga de trabajo
    fechacreacion="2023-03-15T10:00:00Z",
    fechamodificacion="2023-03-15T10:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[0]),
    idusuario=desarroladores[0],
    cargo=frontend_names[0],
    habilidades="Diseño de interfaces, experiencia de usuario, prototipado",
    tarifahora=25.00,
)

Recurso.objects.create(
    nombrerecurso="DevOps Engineer",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    carga_trabajo=0.85,  # 85% de carga de trabajo
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    idusuario=desarroladores[1],
    cargo="DevOps Engineer",
    habilidades="Automatización de despliegues, integración continua, monitoreo",
    tarifahora=50.00,
)

Recurso.objects.create(
    nombrerecurso=frontend_names[1],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    carga_trabajo=0.65,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[1]),
    idusuario=desarroladores[2],
    cargo=frontend_names[1],
    habilidades=frontend_skills[0],
    tarifahora=40.00,
)

Recurso.objects.create(
    nombrerecurso=frontend_names[2],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[2]),
    idusuario=desarroladores[3],
    cargo=frontend_names[2],
    habilidades=frontend_skills[1],
    tarifahora=40.00,
)

Recurso.objects.create(
    nombrerecurso=frontend_names[3],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[3]),
    idusuario=desarroladores[4],
    cargo=frontend_names[3],
    habilidades=frontend_skills[2],
    tarifahora=40.00,
)

Recurso.objects.create(
    nombrerecurso=backend_names[0],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[0]),
    idusuario=desarroladores[5],
    cargo=backend_names[0],
    habilidades=backend_skills[0],
    tarifahora=60.00,
)

Recurso.objects.create(
    nombrerecurso=backend_names[1],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[1]),
    idusuario=desarroladores[6],
    cargo=backend_names[1],
    habilidades=backend_skills[1],
    tarifahora=60.00,
)

Recurso.objects.create(
    nombrerecurso=backend_names[2],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[2]),
    idusuario=desarroladores[7],
    cargo=backend_names[2],
    habilidades=backend_skills[2],
    tarifahora=60.00,
)

Recurso.objects.create(
    nombrerecurso=backend_names[3],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[3]),
    idusuario=desarroladores[8],
    cargo=backend_names[3],
    habilidades=backend_skills[3],
    tarifahora=60.00,
)

Recurso.objects.create(
    nombrerecurso=backend_names[4],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[4]),
    idusuario=desarroladores[9],
    cargo=backend_names[4],
    habilidades=backend_skills[4],
    tarifahora=60.00,
)

print("Creando recursos humanos - Testers...")

Recurso.objects.create(
    nombrerecurso="Analista QA",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    idusuario=testers[0],
    cargo="Analista QA",
    habilidades=qa_skills[0],
    tarifahora=30.00,
)

Recurso.objects.create(
    nombrerecurso="QA Engineer Senior",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="QA Engineer Senior"),
    idusuario=testers[0],
    cargo="QA Engineer Senior",
    habilidades=qa_skills[1],
    tarifahora=70.00,
)

Recurso.objects.create(
    nombrerecurso="Analista de Pruebas Automatizadas",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista de Pruebas Automatizadas"),
    idusuario=testers[0],
    cargo="Analista de Pruebas Automatizadas",
    habilidades=qa_skills[2],
    tarifahora=75.00,
)

Recurso.objects.create(
    nombrerecurso="Ingeniero de Control de Calidad",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Ingeniero de Control de Calidad"),
    idusuario=testers[0],
    cargo="Ingeniero de Control de Calidad",
    habilidades=qa_skills[3],
    tarifahora=65.00,
)

Recurso.objects.create(
    nombrerecurso="Tester de Aplicaciones Web",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Tester de Aplicaciones Web"),
    idusuario=testers[0],
    cargo="Tester de Aplicaciones Web",
    habilidades=qa_skills[4],
    tarifahora=75.00,
)

Recurso.objects.create(
    nombrerecurso="QA Automation Engineer",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="QA Automation Engineer"),
    idusuario=testers[0],
    cargo="QA Automation Engineer",
    habilidades=qa_skills[5],
    tarifahora=80.00,
)
print("Creando recursos hardware y software...")

Recurso.objects.create(
    nombrerecurso="Monitor 4K",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-06-01T11:00:00Z",
    fechamodificacion="2023-06-01T11:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Monitor 4K"),
    costounidad=5,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Servidor de Desarrollo",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-06-15T14:00:00Z",
    fechamodificacion="2023-06-15T14:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    costounidad=5,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

# Recursos Software
Recurso.objects.create(
    nombrerecurso="Licencia Adobe Creative Suite",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-07-01T08:00:00Z",
    fechamodificacion="2023-07-01T08:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    costounidad=200,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia IDE Premium",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-07-15T13:00:00Z",
    fechamodificacion="2023-07-15T13:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    costounidad=300,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Estación de Trabajo",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-08-15T10:00:00Z",
    fechamodificacion="2023-08-15T10:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    costounidad=500,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia Base de Datos Enterprise",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-09-01T11:00:00Z",
    fechamodificacion="2023-09-01T11:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Base de Datos Enterprise"),
    costounidad=600,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia Antivirus Empresarial",
    idtiporecurso=tipo_software,
    disponibilidad=True,
    fechacreacion="2023-10-01T10:00:00Z",
    fechamodificacion="2023-10-01T10:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Antivirus Empresarial"),
    costounidad=100,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Router Empresarial de Alto Rendimiento",
    idtiporecurso=tipo_hardware,
    disponibilidad=True,
    fechacreacion="2023-10-15T11:00:00Z",
    fechamodificacion="2023-10-15T11:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(
        nombrerecurso="Router Empresarial de Alto Rendimiento"
    ),
    costounidad=1000,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia Autodesk Maya",
    idtiporecurso=tipo_software,
    disponibilidad=True,
    fechacreacion="2023-11-01T09:00:00Z",
    fechamodificacion="2023-11-01T09:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Autodesk Maya"),
    costounidad=500,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="NAS Enterprise Storage",
    idtiporecurso=tipo_hardware,
    disponibilidad=True,
    fechacreacion="2023-11-15T14:00:00Z",
    fechamodificacion="2023-11-15T14:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="NAS Enterprise Storage"),
    costounidad=5000,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia Jira Software",
    idtiporecurso=tipo_software,
    disponibilidad=True,
    fechacreacion="2023-12-01T08:00:00Z",
    fechamodificacion="2023-12-01T08:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Jira Software"),
    costounidad=300,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia TestComplete",
    idtiporecurso=tipo_software,
    disponibilidad=True,
    fechacreacion="2024-01-01T09:00:00Z",
    fechamodificacion="2024-01-01T09:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia TestComplete"),
    costounidad=1500,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Sistema de Videoconferencia 4K",
    idtiporecurso=tipo_hardware,
    disponibilidad=True,
    fechacreacion="2024-01-15T11:00:00Z",
    fechamodificacion="2024-01-15T11:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Sistema de Videoconferencia 4K"),
    costounidad=80,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

Recurso.objects.create(
    nombrerecurso="Licencia VMware Enterprise",
    idtiporecurso=tipo_software,
    disponibilidad=True,
    fechacreacion="2024-02-01T08:00:00Z",
    fechamodificacion="2024-02-01T08:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia VMware Enterprise"),
    costounidad=500,
    fechacompra=fake.date_time_between(
        start_date="-3y", end_date="-2y", tzinfo=timezone.get_current_timezone()
    ),
)

print("Recursos creados exitosamente")

print("Creando equipos ...")


Equipo.objects.create(
    nombreequipo="Equipo de Desarrollo Web",
    descripcion="Equipo encargado de desarrollar y mantener aplicaciones web.",
    fechacreacion="2023-01-15T10:00:00Z",
    fechamodificacion="2023-01-15T10:00:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de Marketing",
    descripcion="Equipo encargado de las estrategias de marketing digital y relaciones públicas.",
    fechacreacion="2023-05-10T09:30:00Z",
    fechamodificacion="2023-05-10T09:30:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de Diseño UX/UI",
    descripcion="Equipo especializado en diseño de interfaces y experiencia de usuario.",
    fechacreacion="2023-02-01T08:00:00Z",
    fechamodificacion="2023-02-01T08:00:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de QA",
    descripcion="Equipo dedicado al control de calidad y testing de aplicaciones.",
    fechacreacion="2023-03-15T09:00:00Z",
    fechamodificacion="2023-03-15T09:00:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de DevOps",
    descripcion="Equipo responsable de la infraestructura y despliegue continuo.",
    fechacreacion="2023-04-01T10:00:00Z",
    fechamodificacion="2023-04-01T10:00:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de Análisis de Datos",
    descripcion="Equipo especializado en análisis de datos y generación de insights.",
    fechacreacion="2023-05-20T11:00:00Z",
    fechamodificacion="2023-05-20T11:00:00Z",
)

Equipo.objects.create(
    nombreequipo="Equipo de Soporte Técnico",
    descripcion="Equipo encargado del soporte y mantenimiento de sistemas.",
    fechacreacion="2023-06-10T13:00:00Z",
    fechamodificacion="2023-06-10T13:00:00Z",
)


Proyecto.objects.create(
    nombreproyecto="Sistema de Gestión de Inventarios",
    descripcion="Desarrollo de sistema ERP para control de inventarios y almacenes.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2024-09-01",
    fechafin="2025-02-15",
    presupuesto=75000.00,
    presupuestoutilizado=30450.1246,
    estado="Monitoreo-Control",
    fechacreacion="2024-07-01T08:00:00Z",
    fechamodificacion="2024-07-01T08:00:00Z",
)
print("Equipos creados exitosamente")
print("Creando proyectos ...")
Proyecto.objects.create(
    nombreproyecto="Plataforma E-learning",
    descripcion="Desarrollo de plataforma educativa en línea con contenido interactivo.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
    fechainicio="2024-01-15",
    fechafin="2024-02-28",
    presupuesto=60000.00,
    presupuestoutilizado=60000,
    estado="Cierre",
    fechacreacion="2024-08-15T09:00:00Z",
    fechamodificacion="2024-08-15T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="App Móvil de Delivery",
    descripcion="Desarrollo de aplicación móvil para servicio de entrega a domicilio.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2024-11-04",
    fechafin="2025-03-15",
    presupuesto=45000.00,
    presupuestoutilizado=29743,
    estado="Ejecución",
    fechacreacion="2024-10-01T10:00:00Z",
    fechamodificacion="2024-10-01T10:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Business Intelligence",
    descripcion="Implementación de herramientas de BI para análisis de datos empresariales.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Análisis de Datos"),
    fechainicio="2024-10-01",
    fechafin="2025-04-15",
    presupuesto=90000.00,
    presupuestoutilizado=50567,
    estado="Ejecución",
    fechacreacion="2024-10-01T08:30:00Z",
    fechamodificacion="2024-10-01T08:30:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Portal de Atención al Cliente",
    descripcion="Desarrollo de portal web para soporte y atención al cliente.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Soporte Técnico"),
    fechainicio="2024-11-15",
    fechafin="2025-05-30",
    presupuesto=40000.00,
    presupuestoutilizado=23089,
    estado="Ejecución",
    fechacreacion="2024-11-15T11:00:00Z",
    fechamodificacion="2024-11-15T11:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Facturación Electrónica",
    descripcion="Implementación de sistema de facturación conforme a normativas vigentes.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2024-08-01",
    fechafin="2025-02-10",
    presupuesto=55000.00,
    presupuestoutilizado=45069,
    estado="Ejecución",
    fechacreacion="2024-08-01T09:00:00Z",
    fechamodificacion="2024-08-01T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Gestión de RRHH",
    descripcion="Desarrollo de plataforma integral para gestión de recursos humanos, nóminas y evaluaciones.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2024-07-15",
    fechafin="2024-12-30",
    presupuesto=85000.00,
    presupuestoutilizado=85000,
    estado="Cierre",
    fechacreacion="2024-07-15T09:00:00Z",
    fechamodificacion="2024-07-15T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Gestión Financiera",
    descripcion="Sistema para control de finanzas, contabilidad y reportes financieros empresariales.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Análisis de Datos"),
    fechainicio="2025-01-10",
    fechafin="2025-02-11",
    presupuesto=95000.00,
    presupuestoutilizado=0,
    estado="Planificación",
    fechacreacion="2025-01-01T10:00:00Z",
    fechamodificacion="2025-01-01T10:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Portal de Gestión de Proveedores",
    descripcion="Plataforma web para gestión y seguimiento de proveedores y licitaciones.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
    fechainicio="2024-10-01",
    fechafin="2025-03-15",
    presupuesto=65000.00,
    presupuestoutilizado=48234,
    estado="Ejecución",
    fechacreacion="2024-10-01T08:00:00Z",
    fechamodificacion="2024-10-01T08:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="CRM Empresarial Integrado",
    descripcion="Sistema de gestión de relaciones con clientes con análisis predictivo y automatización.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
    fechainicio="2024-12-15",
    fechafin="2025-05-15",
    presupuesto=88000.00,
    presupuestoutilizado=1542,
    estado="Inicio",
    fechacreacion="2024-12-01T11:00:00Z",
    fechamodificacion="2024-12-01T11:00:00Z",
)

print("Proyectos creados exitosamente")

print("Asignando recursos a equipos...")

# Frontend Team Members
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[0]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[1]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[2]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
)

# Backend Team Members
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[0]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[1]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[2]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)
print("Backend Team Members")

# QA Team Members
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="QA Engineer Senior"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista de Pruebas Automatizadas"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

print("QA Team Members")

# Design Team Members
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Diseñador UX/UI"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

print("Design Team Members")

# DevOps Members
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

print("DevOps Members")

# Hardware Resources
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Monitor 4K"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(
        nombrerecurso="Router Empresarial de Alto Rendimiento"
    ),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="NAS Enterprise Storage"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Sistema de Videoconferencia 4K"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
)

print("Hardware Resources")

# Software Resources
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Base de Datos Enterprise"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Antivirus Empresarial"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Autodesk Maya"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Jira Software"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia TestComplete"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia VMware Enterprise"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de DevOps"),
)

print("Software Resources")

# Additional Human Resources
Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="QA Automation Engineer"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Ingeniero de Control de Calidad"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Tester de Aplicaciones Web"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[3]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[3]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[4]),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)
print("Additional Human Resources")
print("Recursos asignados a equipos exitosamente")

# Project: Sistema de Gestión de Inventarios
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Revisión del módulo de control de inventarios requerida para el proyecto 'Sistema de Gestión de Inventarios'",
    leido=False,
    fechacreacion="2024-01-10T09:00:00Z",
    prioridad="alta",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2024-01-11T09:00:00Z",
)

# Project: Plataforma E-learning
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=3),
    mensaje="Validación de módulos de cursos interactivos pendiente en 'Plataforma E-learning'",
    leido=False,
    fechacreacion="2024-01-15T10:30:00Z",
    prioridad="media",
    categoria="QA",
    archivada=False,
    fecha_recordatorio="2024-01-16T10:00:00Z",
)

# Project: App Móvil de Delivery
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=1),
    mensaje="Integración de pasarela de pagos requiere revisión urgente - App Móvil de Delivery",
    leido=False,
    fechacreacion="2024-01-20T11:00:00Z",
    prioridad="alta",
    categoria="Frontend",
    archivada=False,
    fecha_recordatorio="2024-01-21T09:00:00Z",
)

# Project: Sistema de Business Intelligence
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Implementación de dashboards analíticos pendiente de aprobación",
    leido=False,
    fechacreacion="2024-02-01T14:00:00Z",
    prioridad="media",
    categoria="Frontend",
    archivada=False,
    fecha_recordatorio="2024-02-02T10:00:00Z",
)

# Project: Portal de Atención al Cliente
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=3),
    mensaje="Pruebas del sistema de chat en tiempo real programadas para mañana",
    leido=False,
    fechacreacion="2024-02-05T15:00:00Z",
    prioridad="alta",
    categoria="QA",
    archivada=False,
    fecha_recordatorio="2024-02-06T09:00:00Z",
)

# Project: Sistema de Gestión Financiera
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=1),
    mensaje="Reunión de inicio del proyecto 'Sistema de Gestión Financiera' - Presentación de requerimientos",
    leido=False,
    fechacreacion="2024-02-10T09:00:00Z",
    prioridad="alta",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2024-02-11T09:00:00Z",
)

# Project: Portal de Gestión de Proveedores
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Review del diseño de la plataforma de proveedores programada",
    leido=False,
    fechacreacion="2024-03-01T10:00:00Z",
    prioridad="media",
    categoria="Frontend",
    archivada=False,
    fecha_recordatorio="2024-03-02T10:00:00Z",
)

# Project: CRM Empresarial Integrado
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=3),
    mensaje="Kickoff del proyecto CRM Empresarial - Presentación del equipo",
    leido=False,
    fechacreacion="2024-04-01T11:00:00Z",
    prioridad="alta",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2024-04-02T09:00:00Z",
)

# Sistema de Gestión de Inventarios
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Revisión del módulo de control de inventarios requerida para el proyecto 'Sistema de Gestión de Inventarios'",
    ),
    fechalectura="2024-01-11T10:00:00Z",
)

# Plataforma E-learning
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=3),
        mensaje="Validación de módulos de cursos interactivos pendiente en 'Plataforma E-learning'",
    ),
    fechalectura="2024-01-16T11:00:00Z",
)

# App Móvil de Delivery
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=1),
        mensaje="Integración de pasarela de pagos requiere revisión urgente - App Móvil de Delivery",
    ),
    fechalectura="2024-01-21T10:00:00Z",
)

# Sistema de Business Intelligence
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Implementación de dashboards analíticos pendiente de aprobación",
    ),
    fechalectura="2024-02-02T11:00:00Z",
)

# Portal de Atención al Cliente
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=3),
        mensaje="Pruebas del sistema de chat en tiempo real programadas para mañana",
    ),
    fechalectura="2024-02-06T10:00:00Z",
)

# Sistema de Gestión Financiera
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=1),
        mensaje="Reunión de inicio del proyecto 'Sistema de Gestión Financiera' - Presentación de requerimientos",
    ),
    fechalectura="2024-02-11T10:00:00Z",
)

# Portal de Gestión de Proveedores
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Review del diseño de la plataforma de proveedores programada",
    ),
    fechalectura="2024-03-02T11:00:00Z",
)

# CRM Empresarial Integrado
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=3),
        mensaje="Kickoff del proyecto CRM Empresarial - Presentación del equipo",
    ),
    fechalectura="2024-04-02T10:00:00Z",
)

# Sistema de Gestión de Inventarios
Requerimiento.objects.create(
    descripcion="Módulo de gestión de usuarios y permisos",
    keywords="autenticación, autorización, roles, permisos, seguridad",
    fechacreacion="2023-07-01T08:00:00Z",
    fechamodificacion="2023-07-01T08:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Sistema de control de stock en tiempo real",
    keywords="inventario, stock, tiempo real, alertas, monitoreo",
    fechacreacion="2023-07-05T09:00:00Z",
    fechamodificacion="2023-07-05T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Generación de reportes y estadísticas",
    keywords="reportes, estadísticas, análisis, gráficos, datos",
    fechacreacion="2023-07-10T10:00:00Z",
    fechamodificacion="2023-07-10T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Integración con sistema de facturación",
    keywords="integración, facturación, pagos, contabilidad, ERP",
    fechacreacion="2023-07-15T11:00:00Z",
    fechamodificacion="2023-07-15T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Gestión de proveedores y órdenes de compra",
    keywords="proveedores, órdenes de compra, gestión, compras, inventario",
    fechacreacion="2023-07-20T13:00:00Z",
    fechamodificacion="2023-07-20T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

# Plataforma E-learning
Requerimiento.objects.create(
    descripcion="Sistema de gestión de cursos y contenidos",
    keywords="cursos, contenidos, gestión, educación, e-learning",
    fechacreacion="2023-08-15T09:00:00Z",
    fechamodificacion="2023-08-15T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Módulo de evaluaciones y seguimiento",
    keywords="evaluaciones, seguimiento, progreso, educación, e-learning",
    fechacreacion="2023-08-20T10:00:00Z",
    fechamodificacion="2023-08-20T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Sistema de videoconferencias integrado",
    keywords="videoconferencias, integración, comunicación, educación, e-learning",
    fechacreacion="2023-08-25T11:00:00Z",
    fechamodificacion="2023-08-25T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Gestión de certificaciones y diplomas",
    keywords="certificaciones, diplomas, gestión, educación, e-learning",
    fechacreacion="2023-08-30T13:00:00Z",
    fechamodificacion="2023-08-30T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Sistema de pagos y suscripciones",
    keywords="pagos, suscripciones, gestión, educación, e-learning",
    fechacreacion="2023-09-05T14:00:00Z",
    fechamodificacion="2023-09-05T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

# App Móvil de Delivery
Requerimiento.objects.create(
    descripcion="Sistema de geolocalización en tiempo real",
    keywords="geolocalización, tiempo real, tracking, delivery, móvil",
    fechacreacion="2023-09-01T10:00:00Z",
    fechamodificacion="2023-09-01T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Gestión de pedidos y estados",
    keywords="pedidos, estados, gestión, delivery, móvil",
    fechacreacion="2023-09-05T11:00:00Z",
    fechamodificacion="2023-09-05T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Sistema de calificaciones y reseñas",
    keywords="calificaciones, reseñas, gestión, delivery, móvil",
    fechacreacion="2023-09-10T13:00:00Z",
    fechamodificacion="2023-09-10T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Integración con múltiples métodos de pago",
    keywords="integración, métodos de pago, gestión, delivery, móvil",
    fechacreacion="2023-09-15T14:00:00Z",
    fechamodificacion="2023-09-15T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Sistema de notificaciones push",
    keywords="notificaciones push, gestión, delivery, móvil",
    fechacreacion="2023-09-20T15:00:00Z",
    fechamodificacion="2023-09-20T15:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

# Sistema de Business Intelligence
Requerimiento.objects.create(
    descripcion="Diseño de data warehouse empresarial",
    keywords="data warehouse, diseño, BI, análisis, datos",
    fechacreacion="2023-10-01T09:00:00Z",
    fechamodificacion="2023-10-01T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Desarrollo de ETLs para integración de datos",
    keywords="ETL, integración de datos, BI, análisis, datos",
    fechacreacion="2023-10-05T10:00:00Z",
    fechamodificacion="2023-10-05T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Creación de dashboards interactivos",
    keywords="dashboards, interactivos, BI, análisis, datos",
    fechacreacion="2023-10-10T11:00:00Z",
    fechamodificacion="2023-10-10T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Sistema de reportes automatizados",
    keywords="reportes, automatizados, BI, análisis, datos",
    fechacreacion="2023-10-15T13:00:00Z",
    fechamodificacion="2023-10-15T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Implementación de análisis predictivo",
    keywords="análisis predictivo, BI, análisis, datos, machine learning",
    fechacreacion="2023-10-20T14:00:00Z",
    fechamodificacion="2023-10-20T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

# Portal de Atención al Cliente
Requerimiento.objects.create(
    descripcion="Sistema de tickets y seguimiento",
    keywords="tickets, seguimiento, atención al cliente, soporte, portal",
    fechacreacion="2023-11-15T09:00:00Z",
    fechamodificacion="2023-11-15T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Requerimiento.objects.create(
    descripcion="Chat en tiempo real con agentes",
    keywords="chat en tiempo real, agentes, atención al cliente, soporte, portal",
    fechacreacion="2023-11-20T10:00:00Z",
    fechamodificacion="2023-11-20T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Requerimiento.objects.create(
    descripcion="Base de conocimientos y FAQs",
    keywords="base de conocimientos, FAQs, atención al cliente, soporte, portal",
    fechacreacion="2023-11-25T11:00:00Z",
    fechamodificacion="2023-11-25T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Requerimiento.objects.create(
    descripcion="Sistema de encuestas de satisfacción",
    keywords="encuestas de satisfacción, atención al cliente, soporte, portal",
    fechacreacion="2023-11-30T13:00:00Z",
    fechamodificacion="2023-11-30T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Requerimiento.objects.create(
    descripcion="Integración con redes sociales",
    keywords="integración, redes sociales, atención al cliente, soporte, portal",
    fechacreacion="2023-12-05T14:00:00Z",
    fechamodificacion="2023-12-05T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

# Sistema de Gestión Financiera
Requerimiento.objects.create(
    descripcion="Módulo de contabilidad general",
    keywords="contabilidad general, gestión financiera, ERP, finanzas, contabilidad",
    fechacreacion="2024-02-01T09:00:00Z",
    fechamodificacion="2024-02-01T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión Financiera"),
)

Requerimiento.objects.create(
    descripcion="Sistema de gestión de presupuestos",
    keywords="gestión de presupuestos, ERP, finanzas, contabilidad, gestión financiera",
    fechacreacion="2024-02-05T10:00:00Z",
    fechamodificacion="2024-02-05T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión Financiera"),
)

Requerimiento.objects.create(
    descripcion="Control de flujo de caja y tesorería",
    keywords="flujo de caja, tesorería, ERP, finanzas, contabilidad, gestión financiera",
    fechacreacion="2024-02-10T11:00:00Z",
    fechamodificacion="2024-02-10T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión Financiera"),
)

Requerimiento.objects.create(
    descripcion="Gestión de activos y depreciación",
    keywords="gestión de activos, depreciación, ERP, finanzas, contabilidad, gestión financiera",
    fechacreacion="2024-02-15T13:00:00Z",
    fechamodificacion="2024-02-15T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión Financiera"),
)

Requerimiento.objects.create(
    descripcion="Reportes financieros y balance general",
    keywords="reportes financieros, balance general, ERP, finanzas, contabilidad, gestión financiera",
    fechacreacion="2024-02-20T14:00:00Z",
    fechamodificacion="2024-02-20T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión Financiera"),
)

# Portal de Gestión de Proveedores
Requerimiento.objects.create(
    descripcion="Registro y validación de proveedores",
    keywords="registro, validación, proveedores, gestión, compras",
    fechacreacion="2024-03-01T09:00:00Z",
    fechamodificacion="2024-03-01T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Gestión de Proveedores"),
)

Requerimiento.objects.create(
    descripcion="Sistema de licitaciones electrónicas",
    keywords="licitaciones electrónicas, proveedores, gestión, compras",
    fechacreacion="2024-03-05T10:00:00Z",
    fechamodificacion="2024-03-05T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Gestión de Proveedores"),
)

Requerimiento.objects.create(
    descripcion="Gestión de contratos y documentación",
    keywords="gestión de contratos, documentación, proveedores, gestión, compras",
    fechacreacion="2024-03-10T11:00:00Z",
    fechamodificacion="2024-03-10T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Gestión de Proveedores"),
)

Requerimiento.objects.create(
    descripcion="Evaluación y calificación de proveedores",
    keywords="evaluación, calificación, proveedores, gestión, compras",
    fechacreacion="2024-03-15T13:00:00Z",
    fechamodificacion="2024-03-15T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Gestión de Proveedores"),
)

Requerimiento.objects.create(
    descripcion="Portal de autogestión para proveedores",
    keywords="autogestión, proveedores, gestión, compras",
    fechacreacion="2024-03-20T14:00:00Z",
    fechamodificacion="2024-03-20T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Gestión de Proveedores"),
)

# CRM Empresarial Integrado
Requerimiento.objects.create(
    descripcion="Gestión de contactos y empresas",
    keywords="gestión de contactos, empresas, CRM, relaciones con clientes",
    fechacreacion="2024-04-01T09:00:00Z",
    fechamodificacion="2024-04-01T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="CRM Empresarial Integrado"),
)

Requerimiento.objects.create(
    descripcion="Pipeline de ventas y oportunidades",
    keywords="pipeline de ventas, oportunidades, CRM, relaciones con clientes",
    fechacreacion="2024-04-05T10:00:00Z",
    fechamodificacion="2024-04-05T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="CRM Empresarial Integrado"),
)

Requerimiento.objects.create(
    descripcion="Automatización de marketing",
    keywords="automatización de marketing, CRM, relaciones con clientes",
    fechacreacion="2024-04-10T11:00:00Z",
    fechamodificacion="2024-04-10T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="CRM Empresarial Integrado"),
)

Requerimiento.objects.create(
    descripcion="Análisis predictivo de ventas",
    keywords="análisis predictivo de ventas, CRM, relaciones con clientes",
    fechacreacion="2024-04-15T13:00:00Z",
    fechamodificacion="2024-04-15T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="CRM Empresarial Integrado"),
)

Requerimiento.objects.create(
    descripcion="Integración con servicios de email marketing",
    keywords="integración, servicios de email marketing, CRM, relaciones con clientes",
    fechacreacion="2024-04-20T14:00:00Z",
    fechamodificacion="2024-04-20T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="CRM Empresarial Integrado"),
)

# Requerimeintos proyecto Sistema de Gestión de RRHH:

# 1. Sistema de Gestión de Personal
Requerimiento.objects.create(
    descripcion="Módulo de gestión de empleados y estructura organizacional",
    keywords="gestión de empleados, estructura organizacional, RRHH",
    fechacreacion="2024-07-15T10:00:00Z",
    fechamodificacion="2024-07-15T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de RRHH"),
)

# 2. Sistema de Nóminas
Requerimiento.objects.create(
    descripcion="Cálculo y procesamiento de nóminas, beneficios y deducciones",
    keywords="cálculo de nóminas, procesamiento de nóminas, beneficios, deducciones, RRHH",
    fechacreacion="2024-07-20T09:00:00Z",
    fechamodificacion="2024-07-20T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de RRHH"),
)

# 3. Gestión de Evaluaciones
Requerimiento.objects.create(
    descripcion="Sistema de evaluación de desempeño y seguimiento de objetivos",
    keywords="evaluación de desempeño, seguimiento de objetivos, RRHH",
    fechacreacion="2024-07-25T11:00:00Z",
    fechamodificacion="2024-07-25T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de RRHH"),
)

# 4. Control de Asistencia
Requerimiento.objects.create(
    descripcion="Módulo de control de asistencia, vacaciones y permisos",
    keywords="control de asistencia, vacaciones, permisos, RRHH",
    fechacreacion="2024-07-30T14:00:00Z",
    fechamodificacion="2024-07-30T14:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de RRHH"),
)

# 5. Reportes y Analytics
Requerimiento.objects.create(
    descripcion="Generación de reportes, métricas y análisis de recursos humanos",
    keywords="reportes, métricas, análisis de recursos humanos, RRHH",
    fechacreacion="2024-08-05T13:00:00Z",
    fechamodificacion="2024-08-05T13:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de RRHH"),
)

# Sistema de Gestión de Inventarios
# Requerimiento: Módulo de gestión de usuarios y permisos
tarea1 = Tarea.objects.create(
    nombretarea="Desarrollo de sistema de autenticación",
    descripcion="Implementar un sistema de autenticación seguro con opciones de recuperación de contraseña y autenticación de dos factores.",
    tags="seguridad, auth, login, jwt, oauth",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=120,
    fechainicio="2024-01-15",
    fechafin="2024-01-25",
    duracionestimada=8,
    duracionactual=0,
    dificultad=3,
    estado="En Progreso",
    prioridad=1,
    costoestimado=2000.00,
    costoactual=0.00,
    fechacreacion="2024-01-15T09:00:00Z",
    fechamodificacion="2024-01-15T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de usuarios y permisos"
    ),
)

tarea2 = Tarea.objects.create(
    nombretarea="Implementación de roles y permisos",
    descripcion="Desarrollar un sistema flexible de roles y permisos basado en acciones y recursos.",
    tags="rbac, permisos, autorización, seguridad",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=140,
    fechainicio="2024-01-26",
    fechafin="2024-02-05",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2024-01-15T09:00:00Z",
    fechamodificacion="2024-01-15T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de usuarios y permisos"
    ),
)

# Requerimiento: Sistema de control de stock en tiempo real
Tarea.objects.create(
    nombretarea="Desarrollo de API de inventario",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=100,
    fechainicio="2024-02-01",
    fechafin="2024-02-15",
    duracionestimada=12,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3000.00,
    costoactual=0.00,
    fechacreacion="2024-02-01T09:00:00Z",
    fechamodificacion="2024-02-01T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de control de stock en tiempo real"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de webhooks para actualizaciones",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.7,
    tamaño_estimado=80,
    fechainicio="2024-02-16",
    fechafin="2024-02-25",
    duracionestimada=8,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2000.00,
    costoactual=0.00,
    fechacreacion="2024-02-01T09:00:00Z",
    fechamodificacion="2024-02-01T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de control de stock en tiempo real"
    ),
)

# Requerimiento: Generación de reportes y estadísticas
Tarea.objects.create(
    nombretarea="Desarrollo de módulo de reportes dinámicos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=110,
    fechainicio="2024-02-26",
    fechafin="2024-03-10",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2024-02-26T09:00:00Z",
    fechamodificacion="2024-02-26T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Generación de reportes y estadísticas"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de gráficos estadísticos",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-03-11",
    fechafin="2024-03-20",
    duracionestimada=8,
    duracionactual=0,
    dificultad=3,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2000.00,
    costoactual=0.00,
    fechacreacion="2024-02-26T09:00:00Z",
    fechamodificacion="2024-02-26T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Generación de reportes y estadísticas"
    ),
)

# Requerimiento: Integración con sistema de facturación
Tarea.objects.create(
    nombretarea="Desarrollo de API de integración con facturación",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=130,
    fechainicio="2024-03-21",
    fechafin="2024-04-05",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="Pendiente",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=0.00,
    fechacreacion="2024-03-21T09:00:00Z",
    fechamodificacion="2024-03-21T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Integración con sistema de facturación"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de sincronización de datos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-04-06",
    fechafin="2024-04-15",
    duracionestimada=8,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2000.00,
    costoactual=0.00,
    fechacreacion="2024-03-21T09:00:00Z",
    fechamodificacion="2024-03-21T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Integración con sistema de facturación"
    ),
)

# Requerimiento: Gestión de proveedores y órdenes de compra
Tarea.objects.create(
    nombretarea="Desarrollo de módulo de proveedores",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=120,
    fechainicio="2024-04-16",
    fechafin="2024-04-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="Pendiente",
    prioridad=1,
    costoestimado=2800.00,
    costoactual=0.00,
    fechacreacion="2024-04-16T09:00:00Z",
    fechamodificacion="2024-04-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de proveedores y órdenes de compra"
    ),
)

Tarea.objects.create(
    nombretarea="Sistema de generación de órdenes de compra",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-05-01",
    fechafin="2024-05-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2024-04-16T09:00:00Z",
    fechamodificacion="2024-04-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de proveedores y órdenes de compra"
    ),
)

# Comenzando con Plataforma E-learning
# Requerimiento: Sistema de gestión de cursos y contenidos
Tarea.objects.create(
    nombretarea="Desarrollo de catálogo de cursos",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=110,
    fechainicio="2024-05-16",
    fechafin="2024-05-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=2700.00,
    costoactual=2700.00,
    fechacreacion="2024-05-16T09:00:00Z",
    fechamodificacion="2024-05-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de gestión de cursos y contenidos"
    ),
)

Tarea.objects.create(
    nombretarea="Sistema de carga y gestión de contenidos",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-06-01",
    fechafin="2024-06-15",
    duracionestimada=12,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=3000.00,
    costoactual=3000.00,
    fechacreacion="2024-05-16T09:00:00Z",
    fechamodificacion="2024-05-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de gestión de cursos y contenidos"
    ),
)

# Requerimiento: Módulo de evaluaciones y seguimiento
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de evaluaciones online",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=100,
    fechainicio="2024-06-16",
    fechafin="2024-06-30",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-06-16T09:00:00Z",
    fechamodificacion="2024-06-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de evaluaciones y seguimiento"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de sistema de seguimiento de progreso",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-07-01",
    fechafin="2024-07-15",
    duracionestimada=11,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=2600.00,
    costoactual=2600.00,
    fechacreacion="2024-06-16T09:00:00Z",
    fechamodificacion="2024-06-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de evaluaciones y seguimiento"
    ),
)

# Requerimiento: Sistema de videoconferencias integrado
Tarea.objects.create(
    nombretarea="Integración de API de videoconferencias",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2024-07-16",
    fechafin="2024-07-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="Completada",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=3500.00,
    fechacreacion="2024-07-16T09:00:00Z",
    fechamodificacion="2024-07-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de videoconferencias integrado"
    ),
)

Tarea.objects.create(
    nombretarea="Desarrollo de interfaz de videoconferencias",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-08-01",
    fechafin="2024-08-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-07-16T09:00:00Z",
    fechamodificacion="2024-07-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de videoconferencias integrado"
    ),
)

# Requerimiento: Gestión de certificaciones y diplomas
Tarea.objects.create(
    nombretarea="Desarrollo de generador de certificados",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=110,
    fechainicio="2024-08-16",
    fechafin="2024-08-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=2600.00,
    costoactual=2600.00,
    fechacreacion="2024-08-16T09:00:00Z",
    fechamodificacion="2024-08-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de certificaciones y diplomas"
    ),
)

Tarea.objects.create(
    nombretarea="Sistema de validación de certificados online",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-09-01",
    fechafin="2024-09-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-08-16T09:00:00Z",
    fechamodificacion="2024-08-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de certificaciones y diplomas"
    ),
)

# Requerimiento: Sistema de pagos y suscripciones
Tarea.objects.create(
    nombretarea="Integración de pasarela de pagos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2024-09-16",
    fechafin="2024-09-30",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="Completada",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=3500.00,
    fechacreacion="2024-09-16T09:00:00Z",
    fechamodificacion="2024-09-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de pagos y suscripciones"
    ),
)

Tarea.objects.create(
    nombretarea="Gestión de suscripciones y renovaciones",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-10-01",
    fechafin="2024-10-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=2,
    costoestimado=2900.00,
    costoactual=2900.00,
    fechacreacion="2024-09-16T09:00:00Z",
    fechamodificacion="2024-09-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de pagos y suscripciones"
    ),
)

# App Móvil de Delivery - Sistema de geolocalización en tiempo real
Tarea.objects.create(
    nombretarea="Implementación de tracking GPS en tiempo real",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2024-10-16",
    fechafin="2024-10-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="Pendiente",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=0.00,
    fechacreacion="2024-10-16T09:00:00Z",
    fechamodificacion="2024-10-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de geolocalización en tiempo real"
    ),
)

Tarea.objects.create(
    nombretarea="Desarrollo de visualización de rutas en mapa",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-11-01",
    fechafin="2024-11-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=0.00,
    fechacreacion="2024-10-16T09:00:00Z",
    fechamodificacion="2024-10-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de geolocalización en tiempo real"
    ),
)

# Gestión de pedidos y estados
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de gestión de pedidos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=110,
    fechainicio="2024-11-16",
    fechafin="2024-11-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3000.00,
    costoactual=0.00,
    fechacreacion="2024-11-16T09:00:00Z",
    fechamodificacion="2024-11-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de pedidos y estados"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de actualizaciones de estado en tiempo real",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-12-01",
    fechafin="2024-12-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2024-11-16T09:00:00Z",
    fechamodificacion="2024-11-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Gestión de pedidos y estados"
    ),
)

# Sistema de calificaciones y reseñas
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de calificaciones",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=100,
    fechainicio="2024-12-16",
    fechafin="2024-12-30",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2024-12-16T09:00:00Z",
    fechamodificacion="2024-12-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de calificaciones y reseñas"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de gestión de reseñas",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2025-01-01",
    fechafin="2025-01-15",
    duracionestimada=11,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2700.00,
    costoactual=0.00,
    fechacreacion="2024-12-16T09:00:00Z",
    fechamodificacion="2024-12-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de calificaciones y reseñas"
    ),
)

# Integración con múltiples métodos de pago
Tarea.objects.create(
    nombretarea="Integración de pasarelas de pago",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2025-01-16",
    fechafin="2025-01-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=0.00,
    fechacreacion="2025-01-16T09:00:00Z",
    fechamodificacion="2025-01-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Integración con múltiples métodos de pago"
    ),
)

Tarea.objects.create(
    nombretarea="Desarrollo de interfaz de pagos",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2025-02-01",
    fechafin="2025-02-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=2800.00,
    costoactual=0.00,
    fechacreacion="2025-01-16T09:00:00Z",
    fechamodificacion="2025-01-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Integración con múltiples métodos de pago"
    ),
)

# Sistema de notificaciones push
Tarea.objects.create(
    nombretarea="Implementación de sistema de notificaciones",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=100,
    fechainicio="2025-02-16",
    fechafin="2025-02-28",
    duracionestimada=9,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=2,
    costoestimado=2600.00,
    costoactual=0.00,
    fechacreacion="2025-02-16T09:00:00Z",
    fechamodificacion="2025-02-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de notificaciones push"
    ),
)

Tarea.objects.create(
    nombretarea="Configuración de servicios push",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2025-03-01",
    fechafin="2025-03-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2400.00,
    costoactual=0.00,
    fechacreacion="2025-02-16T09:00:00Z",
    fechamodificacion="2025-02-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de notificaciones push"
    ),
)

# Diseño de data warehouse empresarial
Tarea.objects.create(
    nombretarea="Diseño de arquitectura del data warehouse",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2025-03-16",
    fechafin="2025-03-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="En Progreso",
    prioridad=1,
    costoestimado=4000.00,
    costoactual=0.00,
    fechacreacion="2025-03-16T09:00:00Z",
    fechamodificacion="2025-03-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Diseño de data warehouse empresarial"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de modelos dimensionales",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2025-04-01",
    fechafin="2025-04-15",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="Pendiente",
    prioridad=2,
    costoestimado=3500.00,
    costoactual=0.00,
    fechacreacion="2025-03-16T09:00:00Z",
    fechamodificacion="2025-03-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Diseño de data warehouse empresarial"
    ),
)

# Desarrollo de ETLs para integración de datos
Tarea.objects.create(
    nombretarea="Desarrollo de procesos ETL",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=110,
    fechainicio="2025-04-16",
    fechafin="2025-04-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3200.00,
    costoactual=0.00,
    fechacreacion="2025-04-16T09:00:00Z",
    fechamodificacion="2025-04-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Desarrollo de ETLs para integración de datos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de validaciones de datos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2025-05-01",
    fechafin="2025-05-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=0.00,
    fechacreacion="2025-04-16T09:00:00Z",
    fechamodificacion="2025-04-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Desarrollo de ETLs para integración de datos"
    ),
)

# Creación de dashboards interactivos
Tarea.objects.create(
    nombretarea="Desarrollo de visualizaciones interactivas",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2025-05-16",
    fechafin="2025-05-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=0.00,
    fechacreacion="2025-05-16T09:00:00Z",
    fechamodificacion="2025-05-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Creación de dashboards interactivos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de filtros dinámicos",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2025-06-01",
    fechafin="2025-06-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=0.00,
    fechacreacion="2025-05-16T09:00:00Z",
    fechamodificacion="2025-05-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Creación de dashboards interactivos"
    ),
)

# Sistema de reportes automatizados
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de programación de reportes",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=110,
    fechainicio="2025-06-16",
    fechafin="2025-06-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3200.00,
    costoactual=0.00,
    fechacreacion="2025-06-16T09:00:00Z",
    fechamodificacion="2025-06-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de reportes automatizados"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de exportación de reportes",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2025-07-01",
    fechafin="2025-07-15",
    duracionestimada=10,
    duracionactual=0,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2600.00,
    costoactual=0.00,
    fechacreacion="2025-06-16T09:00:00Z",
    fechamodificacion="2025-06-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de reportes automatizados"
    ),
)

# Implementación de análisis predictivo
Tarea.objects.create(
    nombretarea="Desarrollo de modelos predictivos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=120,
    fechainicio="2025-07-16",
    fechafin="2025-07-31",
    duracionestimada=12,
    duracionactual=0,
    dificultad=5,
    estado="En Progreso",
    prioridad=1,
    costoestimado=4000.00,
    costoactual=0.00,
    fechacreacion="2025-07-16T09:00:00Z",
    fechamodificacion="2025-07-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Implementación de análisis predictivo"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de algoritmos de machine learning",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=110,
    fechainicio="2025-08-01",
    fechafin="2025-08-15",
    duracionestimada=11,
    duracionactual=0,
    dificultad=5,
    estado="En Progreso",
    prioridad=2,
    costoestimado=3800.00,
    costoactual=0.00,
    fechacreacion="2025-07-16T09:00:00Z",
    fechamodificacion="2025-07-16T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Implementación de análisis predictivo"
    ),
)

# 1. Sistema de Gestión de Personal
Tarea.objects.create(
    nombretarea="Desarrollo de módulo de gestión de empleados",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=120,
    fechainicio="2024-07-15",
    fechafin="2024-07-30",
    duracionestimada=12,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=3000.00,
    costoactual=3000.00,
    fechacreacion="2024-07-15T10:00:00Z",
    fechamodificacion="2024-07-15T10:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de empleados y estructura organizacional"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de estructura organizacional",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-07-31",
    fechafin="2024-08-15",
    duracionestimada=12,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-07-15T10:00:00Z",
    fechamodificacion="2024-07-15T10:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de empleados y estructura organizacional"
    ),
)

# 2. Sistema de Nóminas
Tarea.objects.create(
    nombretarea="Desarrollo de motor de cálculo de nóminas",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=130,
    fechainicio="2024-07-20",
    fechafin="2024-08-05",
    duracionestimada=15,
    duracionactual=0,
    dificultad=5,
    estado="Completada",
    prioridad=1,
    costoestimado=4000.00,
    costoactual=4000.00,
    fechacreacion="2024-07-20T09:00:00Z",
    fechamodificacion="2024-07-20T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Cálculo y procesamiento de nóminas, beneficios y deducciones"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de gestión de beneficios",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-08-06",
    fechafin="2024-08-20",
    duracionestimada=11,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-07-20T09:00:00Z",
    fechamodificacion="2024-07-20T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Cálculo y procesamiento de nóminas, beneficios y deducciones"
    ),
)

# 3. Gestión de Evaluaciones
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de evaluación de desempeño",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=110,
    fechainicio="2024-07-25",
    fechafin="2024-08-10",
    duracionestimada=13,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=3200.00,
    costoactual=3200.00,
    fechacreacion="2024-07-25T11:00:00Z",
    fechamodificacion="2024-07-25T11:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de evaluación de desempeño y seguimiento de objetivos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de seguimiento de objetivos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-08-11",
    fechafin="2024-08-25",
    duracionestimada=11,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=2600.00,
    costoactual=2600.00,
    fechacreacion="2024-07-25T11:00:00Z",
    fechamodificacion="2024-07-25T11:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de evaluación de desempeño y seguimiento de objetivos"
    ),
)

# 4. Control de Asistencia
Tarea.objects.create(
    nombretarea="Desarrollo de módulo de control de asistencia",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.8,
    tamaño_estimado=110,
    fechainicio="2024-07-30",
    fechafin="2024-08-15",
    duracionestimada=13,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=3200.00,
    costoactual=3200.00,
    fechacreacion="2024-07-30T14:00:00Z",
    fechamodificacion="2024-07-30T14:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de control de asistencia, vacaciones y permisos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de gestión de vacaciones y permisos",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=90,
    fechainicio="2024-08-16",
    fechafin="2024-08-30",
    duracionestimada=11,
    duracionactual=0,
    dificultad=3,
    estado="Completada",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-07-30T14:00:00Z",
    fechamodificacion="2024-07-30T14:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de control de asistencia, vacaciones y permisos"
    ),
)

# 5. Reportes y Analytics
Tarea.objects.create(
    nombretarea="Desarrollo de sistema de reportes de RRHH",
    tipo_tarea=tipo_tarea_objects["Backend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.85,
    tamaño_estimado=120,
    fechainicio="2024-08-05",
    fechafin="2024-08-20",
    duracionestimada=12,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=1,
    costoestimado=3000.00,
    costoactual=3000.00,
    fechacreacion="2024-08-05T13:00:00Z",
    fechamodificacion="2024-08-05T13:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Generación de reportes, métricas y análisis de recursos humanos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de dashboards analíticos de RRHH",
    tipo_tarea=tipo_tarea_objects["Frontend"],
    fase=fase_objects["Construcción/Desarrollo"],
    claridad_requisitos=0.75,
    tamaño_estimado=100,
    fechainicio="2024-08-21",
    fechafin="2024-09-05",
    duracionestimada=12,
    duracionactual=0,
    dificultad=4,
    estado="Completada",
    prioridad=2,
    costoestimado=2800.00,
    costoactual=2800.00,
    fechacreacion="2024-08-05T13:00:00Z",
    fechamodificacion="2024-08-05T13:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Generación de reportes, métricas y análisis de recursos humanos"
    ),
)

# Historial para Sistema de Gestión de Inventarios
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    fechacambio="2024-01-15T09:00:00Z",
    descripcioncambio="Tarea creada con estado: Pendiente",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    fechacambio="2024-01-20T10:30:00Z",
    descripcioncambio="Avance del 30% en la implementación de autenticación básica",
)

# Historial para Sistema de Control de Stock
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API de inventario"),
    fechacambio="2024-02-01T09:00:00Z",
    descripcioncambio="Inicio del desarrollo de endpoints principales",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de webhooks para actualizaciones"
    ),
    fechacambio="2024-02-16T11:00:00Z",
    descripcioncambio="Configuración inicial del sistema de webhooks",
)

# Historial para Plataforma E-learning
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de catálogo de cursos"),
    fechacambio="2024-05-16T09:30:00Z",
    descripcioncambio="Inicio de la estructura base del catálogo",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Sistema de carga y gestión de contenidos"),
    fechacambio="2024-06-01T10:00:00Z",
    descripcioncambio="Implementación del sistema de carga de archivos",
)

# Historial para Sistema de Videoconferencias
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de API de videoconferencias"),
    fechacambio="2024-07-16T14:00:00Z",
    descripcioncambio="Inicio de pruebas de integración con proveedor",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de interfaz de videoconferencias"
    ),
    fechacambio="2024-08-01T09:00:00Z",
    descripcioncambio="Diseño de interfaz principal completado",
)

# Historial para Sistema de Pagos
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de pasarela de pagos"),
    fechacambio="2024-09-16T11:00:00Z",
    descripcioncambio="Configuración inicial de pasarela de pagos",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Gestión de suscripciones y renovaciones"),
    fechacambio="2024-10-01T10:00:00Z",
    descripcioncambio="Desarrollo del módulo de suscripciones iniciado",
)

# Historial para App Móvil de Delivery
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de tracking GPS en tiempo real"
    ),
    fechacambio="2024-10-16T13:00:00Z",
    descripcioncambio="Integración con servicios de geolocalización iniciada",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de visualización de rutas en mapa"
    ),
    fechacambio="2024-11-01T09:00:00Z",
    descripcioncambio="Implementación de mapas interactivos en proceso",
)

# Historial para Sistema de Calificaciones
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de calificaciones"),
    fechacambio="2024-12-16T10:00:00Z",
    descripcioncambio="Inicio del desarrollo del sistema de calificaciones",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de gestión de reseñas"),
    fechacambio="2025-01-01T09:00:00Z",
    descripcioncambio="Configuración del módulo de reseñas iniciada",
)

# Historial para Sistema BI
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de arquitectura del data warehouse"),
    fechacambio="2025-03-16T11:00:00Z",
    descripcioncambio="Inicio del diseño de arquitectura",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de modelos dimensionales"),
    fechacambio="2025-04-01T09:00:00Z",
    descripcioncambio="Desarrollo de modelos dimensionales en proceso",
)

# Historial para ETL
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de procesos ETL"),
    fechacambio="2025-04-16T10:00:00Z",
    descripcioncambio="Inicio de implementación de procesos ETL",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de validaciones de datos"),
    fechacambio="2025-05-01T09:00:00Z",
    descripcioncambio="Desarrollo de validaciones de datos iniciado",
)

# Historial para Dashboards
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de visualizaciones interactivas"),
    fechacambio="2025-05-16T14:00:00Z",
    descripcioncambio="Inicio del desarrollo de visualizaciones",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de filtros dinámicos"),
    fechacambio="2025-06-01T09:00:00Z",
    descripcioncambio="Desarrollo de sistema de filtros iniciado",
)

# Recursos Humanos - Frontend
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de interfaz de videoconferencias"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[0]),
    cantidad=1,
    experiencia=4,  # Proficiente
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de gráficos estadísticos"),
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[1]),
    cantidad=1,
    experiencia=5,  # Experto
)

# Recursos Humanos - Backend
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API de inventario"),
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[0]),
    cantidad=1,
    experiencia=4,  # Proficiente
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de webhooks para actualizaciones"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[1]),
    cantidad=1,
    experiencia=5,  # Experto
)

# Recursos Humanos - QA
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de validaciones de datos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    cantidad=1,
    experiencia=4,  # Proficiente
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de calificaciones"),
    idrecurso=Recurso.objects.get(nombrerecurso="QA Engineer Senior"),
    cantidad=1,
    experiencia=5,  # Experto
)

# Recursos Hardware
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de visualizaciones interactivas"),
    idrecurso=Recurso.objects.get(nombrerecurso="Monitor 4K"),
    cantidad=2,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de procesos ETL"),
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    cantidad=1,
)

# Recursos Software
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de filtros dinámicos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de módulo de reportes dinámicos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Base de Datos Enterprise"),
    cantidad=1,
)

# DevOps y Herramientas
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de servicios push"),
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia VMware Enterprise"),
    cantidad=1,
)

# Diseño y Creatividad
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de visualizaciones interactivas"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de interfaz de pagos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Diseñador UX/UI"),
    cantidad=1,
)

# Testing y Calidad
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de gestión de reseñas"),
    idrecurso=Recurso.objects.get(nombrerecurso="QA Automation Engineer"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de sistema de programación de reportes"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia TestComplete"),
    cantidad=1,
)

# Infraestructura
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de API de videoconferencias"),
    idrecurso=Recurso.objects.get(nombrerecurso="Sistema de Videoconferencia 4K"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de modelos dimensionales"),
    idrecurso=Recurso.objects.get(nombrerecurso="NAS Enterprise Storage"),
    cantidad=1,
)

# Network Infrastructure
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de API de integración con facturación"
    ),
    idrecurso=Recurso.objects.get(
        nombrerecurso="Router Empresarial de Alto Rendimiento"
    ),
    cantidad=1,
)

# Development Tools
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de modelos predictivos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    cantidad=2,
)

# Backend Development
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de algoritmos de machine learning"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[2]),
    cantidad=1,
)

# Frontend Development
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de interfaz de videoconferencias"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[2]),
    cantidad=1,
)

# Security Tools
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Antivirus Empresarial"),
    cantidad=1,
)

# Project Management Tools
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de sistema de notificaciones"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Jira Software"),
    cantidad=1,
)

# Backend Development Tasks with Backend Developers
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[0]),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API de inventario"),
    idrecurso=Recurso.objects.get(nombrerecurso=backend_names[1]),
    cantidad=1,
)

# Frontend Development Tasks with Frontend Developers
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de gráficos estadísticos"),
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[0]),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de interfaz de videoconferencias"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[1]),
    cantidad=1,
)

# Development Tools and Software
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de módulo de reportes dinámicos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    cantidad=1,
)

# QA Resources
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de validaciones de datos"),
    idrecurso=Recurso.objects.get(nombrerecurso="QA Engineer Senior"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de calificaciones"),
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de API de videoconferencias"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    cantidad=1,
)

# Design Resources
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de interfaz de pagos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de arquitectura del data warehouse"),
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    cantidad=1,
)

# Management and Collaboration Tools
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de sistema de notificaciones"
    ),
    idrecurso=Recurso.objects.get(nombrerecurso="Python/Django Developer"),
    cantidad=1,
)

# Security and DevOps
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de servicios push"),
    idrecurso=Recurso.objects.get(nombrerecurso="Python/Django Developer"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de modelos dimensionales"),
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    cantidad=1,
)

print("Asignación de recursos a tareas completada")

print("Creando alertas para las tareas...")

# Sistema de Gestión de Inventarios
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
    tipoalerta="riesgo",
    mensaje="Posibles vulnerabilidades detectadas en el sistema de autenticación.",
    activa=True,
    fechacreacion="2024-01-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de roles y permisos"),
    tipoalerta="retraso",
    mensaje="La implementación está tomando más tiempo del previsto.",
    activa=True,
    fechacreacion="2024-02-01T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API de inventario"),
    tipoalerta="presupuesto",
    mensaje="Se requieren recursos adicionales para completar la API.",
    activa=True,
    fechacreacion="2024-02-10T11:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de webhooks para actualizaciones"
    ),
    tipoalerta="bloqueo",
    mensaje="Dependencia bloqueante con servicios externos.",
    activa=True,
    fechacreacion="2024-02-20T14:00:00Z",
)

# Generación de reportes y estadísticas
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de módulo de reportes dinámicos"),
    tipoalerta="riesgo",
    mensaje="Alto consumo de recursos en la generación de reportes.",
    activa=True,
    fechacreacion="2024-03-01T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de gráficos estadísticos"),
    tipoalerta="presupuesto",
    mensaje="Se necesitan licencias adicionales para las librerías de gráficos.",
    activa=True,
    fechacreacion="2024-03-15T10:00:00Z",
)

# Integración con sistema de facturación
Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de API de integración con facturación"
    ),
    tipoalerta="bloqueo",
    mensaje="Sistema de facturación no disponible para pruebas.",
    activa=True,
    fechacreacion="2024-03-25T11:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de sincronización de datos"),
    tipoalerta="retraso",
    mensaje="Problemas con la sincronización en tiempo real.",
    activa=True,
    fechacreacion="2024-04-10T13:00:00Z",
)

# Gestión de proveedores
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de módulo de proveedores"),
    tipoalerta="presupuesto",
    mensaje="Costos de desarrollo superiores a lo estimado.",
    activa=True,
    fechacreacion="2024-04-20T15:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Sistema de generación de órdenes de compra"),
    tipoalerta="riesgo",
    mensaje="Posibles inconsistencias en el cálculo de impuestos.",
    activa=True,
    fechacreacion="2024-05-05T09:00:00Z",
)

# Plataforma E-learning
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de catálogo de cursos"),
    tipoalerta="bloqueo",
    mensaje="Falta definición de categorías de cursos por parte del cliente.",
    activa=True,
    fechacreacion="2024-05-20T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Sistema de carga y gestión de contenidos"),
    tipoalerta="presupuesto",
    mensaje="Necesidad de aumentar capacidad de almacenamiento.",
    activa=True,
    fechacreacion="2024-06-05T11:00:00Z",
)

# Evaluaciones y Seguimiento
Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de sistema de evaluaciones online"
    ),
    tipoalerta="riesgo",
    mensaje="Problemas de rendimiento con evaluaciones concurrentes.",
    activa=True,
    fechacreacion="2024-06-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de sistema de seguimiento de progreso"
    ),
    tipoalerta="retraso",
    mensaje="Retraso en integración con sistema de calificaciones.",
    activa=True,
    fechacreacion="2024-07-05T14:00:00Z",
)

# Sistema de Videoconferencias
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de API de videoconferencias"),
    tipoalerta="bloqueo",
    mensaje="API del proveedor en mantenimiento programado.",
    activa=True,
    fechacreacion="2024-07-20T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de interfaz de videoconferencias"
    ),
    tipoalerta="presupuesto",
    mensaje="Costo de licencias superior al presupuestado.",
    activa=True,
    fechacreacion="2024-08-05T11:00:00Z",
)

# Certificaciones y Diplomas
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de generador de certificados"),
    tipoalerta="riesgo",
    mensaje="Incompatibilidad con algunos formatos de certificados.",
    activa=True,
    fechacreacion="2024-08-20T13:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Sistema de validación de certificados online"
    ),
    tipoalerta="retraso",
    mensaje="Pendiente definición de proceso de validación.",
    activa=True,
    fechacreacion="2024-09-05T09:00:00Z",
)

# Sistema de Pagos
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Integración de pasarela de pagos"),
    tipoalerta="bloqueo",
    mensaje="Pendiente aprobación de credenciales de producción.",
    activa=True,
    fechacreacion="2024-09-20T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Gestión de suscripciones y renovaciones"),
    tipoalerta="presupuesto",
    mensaje="Incremento en costos de procesamiento de pagos.",
    activa=True,
    fechacreacion="2024-10-05T11:00:00Z",
)

# App Móvil de Delivery
Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de tracking GPS en tiempo real"
    ),
    tipoalerta="riesgo",
    mensaje="Alto consumo de batería en el tracking continuo.",
    activa=True,
    fechacreacion="2024-10-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de visualización de rutas en mapa"
    ),
    tipoalerta="presupuesto",
    mensaje="Costos elevados en servicios de mapas.",
    activa=True,
    fechacreacion="2024-11-05T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Desarrollo de sistema de gestión de pedidos"
    ),
    tipoalerta="bloqueo",
    mensaje="Pendiente integración con sistema de inventario.",
    activa=True,
    fechacreacion="2024-11-20T11:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(
        nombretarea="Implementación de actualizaciones de estado en tiempo real"
    ),
    tipoalerta="retraso",
    mensaje="Problemas con notificaciones push.",
    activa=True,
    fechacreacion="2024-12-05T13:00:00Z",
)

# Business Intelligence
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de arquitectura del data warehouse"),
    tipoalerta="riesgo",
    mensaje="Complejidad en la integración de fuentes heterogéneas.",
    activa=True,
    fechacreacion="2024-12-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de modelos dimensionales"),
    tipoalerta="presupuesto",
    mensaje="Necesidad de aumentar capacidad de almacenamiento.",
    activa=True,
    fechacreacion="2025-01-05T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de procesos ETL"),
    tipoalerta="retraso",
    mensaje="Demoras en la transformación de datos históricos.",
    activa=True,
    fechacreacion="2025-01-20T11:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de validaciones de datos"),
    tipoalerta="bloqueo",
    mensaje="Fuentes de datos no disponibles para pruebas.",
    activa=True,
    fechacreacion="2025-02-05T13:00:00Z",
)

# Dashboards y Reportes
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de visualizaciones interactivas"),
    tipoalerta="presupuesto",
    mensaje="Licencias adicionales requeridas para componentes.",
    activa=True,
    fechacreacion="2025-02-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de filtros dinámicos"),
    tipoalerta="riesgo",
    mensaje="Rendimiento degradado con grandes volúmenes de datos.",
    activa=True,
    fechacreacion="2025-03-05T10:00:00Z",
)

print("Creación de alertas completada")

print("Creando historiales de alertas...")

# Sistema de Gestión de Inventarios
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de sistema de autenticación"),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-01-25T10:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Implementación de roles y permisos"),
        tipoalerta="retraso",
    ),
    fecharesolucion="2024-02-05T11:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de API de inventario"),
        tipoalerta="presupuesto",
    ),
    fecharesolucion="2024-02-15T09:00:00Z",
)

# Sistema de Control de Stock
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de webhooks para actualizaciones"
        ),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-02-25T14:00:00Z",
)

# Reportes y Estadísticas
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de módulo de reportes dinámicos"
        ),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-03-10T15:00:00Z",
)

# Integración con Facturación
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de API de integración con facturación"
        ),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-04-01T10:00:00Z",
)

# Gestión de Proveedores
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de módulo de proveedores"),
        tipoalerta="presupuesto",
    ),
    fecharesolucion="2024-04-25T11:00:00Z",
)

# Plataforma E-learning
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de catálogo de cursos"),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-05-25T09:00:00Z",
)

# Sistema de Evaluaciones
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de sistema de evaluaciones online"
        ),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-06-25T14:00:00Z",
)

# Sistema de Videoconferencias
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Integración de API de videoconferencias"
        ),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-07-25T11:00:00Z",
)

# Certificaciones
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de generador de certificados"
        ),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-08-25T10:00:00Z",
)

# Sistema de Pagos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Integración de pasarela de pagos"),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-09-25T13:00:00Z",
)

# App Móvil Delivery
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de tracking GPS en tiempo real"
        ),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-10-25T15:00:00Z",
)

# Gestión de Pedidos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de sistema de gestión de pedidos"
        ),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-11-25T10:00:00Z",
)

# Business Intelligence
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Diseño de arquitectura del data warehouse"
        ),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2024-12-25T11:00:00Z",
)

# ETL y Procesamiento de Datos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de modelos dimensionales"
        ),
    ),
    fecharesolucion="2025-01-10T09:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de procesos ETL"),
        tipoalerta="retraso",
    ),
    fecharesolucion="2025-01-25T10:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de validaciones de datos"
        ),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2025-02-10T11:00:00Z",
)

# Dashboards y Visualizaciones
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de visualizaciones interactivas"
        ),
        tipoalerta="presupuesto",
    ),
    fecharesolucion="2025-02-25T13:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Implementación de filtros dinámicos"),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2025-03-10T14:00:00Z",
)

# Módulo de Pagos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Integración de pasarela de pagos"),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2024-09-30T15:00:00Z",
)

# Gestión de Suscripciones
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Gestión de suscripciones y renovaciones"
        ),
    ),
    fecharesolucion="2024-10-15T10:00:00Z",
)

# Tracking GPS
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de tracking GPS en tiempo real"
        ),
    ),
    fecharesolucion="2024-11-01T11:00:00Z",
)

# Gestión de Pedidos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Desarrollo de sistema de gestión de pedidos"
        ),
    ),
    fecharesolucion="2024-11-30T14:00:00Z",
)

# Estado en Tiempo Real
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de actualizaciones de estado en tiempo real"
        ),
    ),
    fecharesolucion="2024-12-15T09:00:00Z",
)

# Data Warehouse
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Diseño de arquitectura del data warehouse"
        ),
    ),
    fecharesolucion="2024-12-30T10:00:00Z",
)

# ETL y Modelos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de modelos dimensionales"
        ),
    ),
    fecharesolucion="2025-01-15T11:00:00Z",
)

# Procesos ETL
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de procesos ETL"),
    ),
    fecharesolucion="2025-01-30T13:00:00Z",
)

# Validaciones
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(
            nombretarea="Implementación de validaciones de datos"
        ),
    ),
    fecharesolucion="2025-02-15T14:00:00Z",
)
# Reportes y Programación
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=34,
    ),
    fecharesolucion="2025-03-01T15:00:00Z",
)

# Exportación de Reportes
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=12,
    ),
    fecharesolucion="2025-03-15T10:00:00Z",
)

# Modelos Predictivos
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=24,
    ),
    fecharesolucion="2025-03-30T11:00:00Z",
)

# Machine Learning
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=33,
    ),
    fecharesolucion="2025-04-15T13:00:00Z",
)

pre_save.connect(pre_save_handler)
post_save.connect(audit_post_save)
post_delete.connect(audit_post_delete)

print("Historial de alertas adicional completado")

print("Proceso finalizado")
