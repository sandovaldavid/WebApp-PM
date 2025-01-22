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
)
from script.random_user import generar_usuarios
from faker import Faker
from django.utils import timezone

print("Iniciando generación de datos de prueba...")
fake = Faker()
print("---------------------( Creando usuarios ...)---------------------")

try:
    # Crear un usuario administrador
    usuarios_admin = generar_usuarios(1, "Administrador")
    if usuarios_admin:
        usuario_admin = usuarios_admin[0]
        admin = Administrador.objects.create(
            idusuario=usuario_admin
        )
        print("Administrador creados exitosamente")
    else:
        print("No se pudo crear el usuario administrador")
    
    # Crear usuario Jefe de Proyecto
    JefeProyecto = generar_usuarios(5, "Jefe de Proyecto")
    if JefeProyecto:
        for jefe in JefeProyecto:
            Jefeproyecto.objects.create(
                idusuario=jefe
            )
        print("Jefes de Proyecto creados exitosamente")
    else:
        print("No se pudieron crear los Jefes de Proyecto")
        
    # Crear usuardesarroladores ios para Recursos Humanos
    desarroladores = generar_usuarios(10, "Desarrollador")
    if desarroladores:
        for desarrolador in desarroladores:
            Desarrollador.objects.create(
                idusuario=desarrolador
            )
        print("Desarroladores creados exitosamente")
    else:
        print("No se pudieron crear los Desarroladores")
    
    # Crear testes para Recursos Humanos
    testers = generar_usuarios(10, "Desarrollador")
    if testers:
        for tester in testers:
            Tester.objects.create(
                idusuario=tester
            )
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
print("---------------------( Tipos de Recurso creados exitosamente )---------------------")

print("---------------------( Creando Recursos ...)---------------------")

print("Creando recursos humanos - Desarroladores...")

frontend_skills = [
    "HTML5, CSS3, JavaScript ES6+, React.js, Redux, Responsive Design, Bootstrap, SASS",
    "Vue.js, Nuxt.js, TypeScript, Webpack, Jest, CSS Grid, Flexbox, UI/UX principles",
    "React Native, Next.js, Material-UI, Tailwind CSS, GraphQL, PWA development",
    "Angular, RxJS, SCSS, Cypress, WebPack, Performance optimization, Cross-browser compatibility",
    "JavaScript frameworks, CSS preprocessors, Component libraries, Web accessibility, SEO best practices"
]

backend_skills = [
    "Python, Django, DRF, PostgreSQL, Redis, Celery, Docker, AWS, CI/CD pipelines",
    "Node.js, Express.js, MongoDB, GraphQL, REST APIs, Microservices, RabbitMQ, Kubernetes",
    "Java, Spring Boot, Hibernate, MySQL, JUnit, Maven, Jenkins, Swagger, OAuth2",
    "PHP, Laravel, Symfony, MariaDB, Memcached, RESTful Services, Unit Testing, Git flow",
    "Python, FastAPI, SQLAlchemy, Redis, Docker, Kubernetes, gRPC, Message Queues"
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
    "Desarrollador Frontend Full Stack"
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
    "Backend Systems Developer"
]

Recurso.objects.create(
    nombrerecurso=frontend_names[0],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-03-15T10:00:00Z",
    fechamodificacion="2023-03-15T10:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[0]),
    idusuario=desarroladores[0],
    cargo=frontend_names[0],
    habilidades = "Diseño de interfaces, experiencia de usuario, prototipado",
    tarifahora = 25.00,
)

Recurso.objects.create(
    nombrerecurso="DevOps Engineer",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    idusuario=desarroladores[1],
    cargo="DevOps Engineer",
    habilidades = "Automatización de despliegues, integración continua, monitoreo",
    tarifahora = 50.00,
)

Recurso.objects.create(
    nombrerecurso=frontend_names[1],
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso=frontend_names[1]),
    idusuario=desarroladores[2],
    cargo=frontend_names[1],
    habilidades = frontend_skills[0],
    tarifahora = 40.00,
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
    habilidades = frontend_skills[1],
    tarifahora = 40.00,
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
    habilidades = frontend_skills[2],
    tarifahora = 40.00,
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
    habilidades = backend_skills[0],
    tarifahora = 60.00,
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
    habilidades = backend_skills[1],
    tarifahora = 60.00,
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
    habilidades = backend_skills[2],
    tarifahora = 60.00,
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
    habilidades = backend_skills[3],
    tarifahora = 60.00,
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
    habilidades = backend_skills[4],
    tarifahora = 60.00,
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
    habilidades = qa_skills[0],
    tarifahora = 30.00,
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
    habilidades = qa_skills[1],
    tarifahora = 70.00,
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
    habilidades = qa_skills[2],
    tarifahora = 75.00,
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
    habilidades = qa_skills[3],
    tarifahora = 65.00,
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
    habilidades = qa_skills[4],
    tarifahora = 75.00,
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
    habilidades = qa_skills[5],
    tarifahora = 80.00,
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechacompra = fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
)

Recurso.objects.create(
    nombrerecurso="Router Empresarial de Alto Rendimiento",
    idtiporecurso=tipo_hardware,
    disponibilidad=True,
    fechacreacion="2023-10-15T11:00:00Z",
    fechamodificacion="2023-10-15T11:00:00Z",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Router Empresarial de Alto Rendimiento"),
    costounidad=1000,
    fechacompra=fake.date_time_between(
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
        start_date='-3y',
        end_date='-2y',
        tzinfo=timezone.get_current_timezone()
    )
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
    fechainicio="2023-07-01",
    fechafin="2024-01-15",
    presupuesto=75000.00,
    estado="Monitoreo-Control",
    fechacreacion="2023-07-01T08:00:00Z",
    fechamodificacion="2023-07-01T08:00:00Z",
)
print("Equipos creados exitosamente")
print("Creando proyectos ...")
Proyecto.objects.create(
    nombreproyecto="Plataforma E-learning",
    descripcion="Desarrollo de plataforma educativa en línea con contenido interactivo.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
    fechainicio="2023-08-15",
    fechafin="2024-02-28",
    presupuesto=60000.00,
    estado="Planificación",
    fechacreacion="2023-08-15T09:00:00Z",
    fechamodificacion="2023-08-15T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="App Móvil de Delivery",
    descripcion="Desarrollo de aplicación móvil para servicio de entrega a domicilio.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2023-09-01",
    fechafin="2024-03-30",
    presupuesto=45000.00,
    estado="Inicio",
    fechacreacion="2023-09-01T10:00:00Z",
    fechamodificacion="2023-09-01T10:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Business Intelligence",
    descripcion="Implementación de herramientas de BI para análisis de datos empresariales.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Análisis de Datos"),
    fechainicio="2023-10-01",
    fechafin="2024-04-15",
    presupuesto=90000.00,
    estado="Planificación",
    fechacreacion="2023-10-01T08:30:00Z",
    fechamodificacion="2023-10-01T08:30:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Portal de Atención al Cliente",
    descripcion="Desarrollo de portal web para soporte y atención al cliente.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Soporte Técnico"),
    fechainicio="2023-11-15",
    fechafin="2024-05-30",
    presupuesto=40000.00,
    estado="Ejecución",
    fechacreacion="2023-11-15T11:00:00Z",
    fechamodificacion="2023-11-15T11:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Facturación Electrónica",
    descripcion="Implementación de sistema de facturación conforme a normativas vigentes.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2023-12-01",
    fechafin="2024-06-30",
    presupuesto=55000.00,
    estado="Inicio",
    fechacreacion="2023-12-01T09:00:00Z",
    fechamodificacion="2023-12-01T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Gestión de RRHH",
    descripcion="Desarrollo de plataforma integral para gestión de recursos humanos, nóminas y evaluaciones.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2024-01-15",
    fechafin="2024-07-30",
    presupuesto=85000.00,
    estado="Inicio",
    fechacreacion="2024-01-15T09:00:00Z",
    fechamodificacion="2024-01-15T09:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Sistema de Gestión Financiera",
    descripcion="Sistema para control de finanzas, contabilidad y reportes financieros empresariales.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Análisis de Datos"),
    fechainicio="2024-02-01",
    fechafin="2024-08-15",
    presupuesto=95000.00,
    estado="Planificación",
    fechacreacion="2024-02-01T10:00:00Z",
    fechamodificacion="2024-02-01T10:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Portal de Gestión de Proveedores",
    descripcion="Plataforma web para gestión y seguimiento de proveedores y licitaciones.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
    fechainicio="2024-03-01",
    fechafin="2024-09-30",
    presupuesto=65000.00,
    estado="Ejecución",
    fechacreacion="2024-03-01T08:00:00Z",
    fechamodificacion="2024-03-01T08:00:00Z",
)

Proyecto.objects.create(
    nombreproyecto="CRM Empresarial Integrado",
    descripcion="Sistema de gestión de relaciones con clientes con análisis predictivo y automatización.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
    fechainicio="2024-04-01",
    fechafin="2024-10-15",
    presupuesto=88000.00,
    estado="Inicio",
    fechacreacion="2024-04-01T11:00:00Z",
    fechamodificacion="2024-04-01T11:00:00Z",
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
    idrecurso=Recurso.objects.get(nombrerecurso="Router Empresarial de Alto Rendimiento"),
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

print("Proceso finalizado")
