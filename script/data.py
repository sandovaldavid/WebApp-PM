from django.utils.timezone import now

from dashboard.models import (
    Alerta,
    Equipo,
    Historialalerta,
    Historialnotificacion,
    Historialtarea,
    Miembro,
    Monitoreotarea,
    Notificacion,
    Proyecto,
    Recurso,
    Recursohumano,
    Recursomaterial,
    Requerimiento,
    Tarea,
    Tarearecurso,
    Tiporecurso,
    Usuario,
    Actividad,
)

print("Generando datos de prueba...")

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
    nombreproyecto="Campaña Publicitaria 2030",
    descripcion="Estrategia de marketing para el lanzamiento de productos nuevos.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
    fechainicio="2024-01-01",
    fechafin="2024-03-01",
    presupuesto=100000.00,
    estado="Cierre",
    fechacreacion="2023-12-01T08:30:00Z",
    fechamodificacion="2023-12-01T08:30:00Z",
)

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

# Recursos Humanos
Recurso.objects.create(
    nombrerecurso="Diseñador UX/UI",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-03-15T10:00:00Z",
    fechamodificacion="2023-03-15T10:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Analista QA",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-04-01T09:00:00Z",
    fechamodificacion="2023-04-01T09:00:00Z",
)

# Recursos Hardware
Recurso.objects.create(
    nombrerecurso="Monitor 4K",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-06-01T11:00:00Z",
    fechamodificacion="2023-06-01T11:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Servidor de Desarrollo",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-06-15T14:00:00Z",
    fechamodificacion="2023-06-15T14:00:00Z",
)

# Recursos Software
Recurso.objects.create(
    nombrerecurso="Licencia Adobe Creative Suite",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-07-01T08:00:00Z",
    fechamodificacion="2023-07-01T08:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Licencia IDE Premium",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-07-15T13:00:00Z",
    fechamodificacion="2023-07-15T13:00:00Z",
)

# Recursos Adicionales
Recurso.objects.create(
    nombrerecurso="DevOps Engineer",
    idtiporecurso=tipo_humano,
    disponibilidad=False,
    fechacreacion="2023-08-01T09:00:00Z",
    fechamodificacion="2023-08-01T09:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Estación de Trabajo",
    idtiporecurso=tipo_hardware,
    disponibilidad=False,
    fechacreacion="2023-08-15T10:00:00Z",
    fechamodificacion="2023-08-15T10:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Licencia Base de Datos Enterprise",
    idtiporecurso=tipo_software,
    disponibilidad=False,
    fechacreacion="2023-09-01T11:00:00Z",
    fechamodificacion="2023-09-01T11:00:00Z",
)

# Recursos Humanos
Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Diseñador UX/UI"),
    cargo="Senior UX/UI Designer",
    habilidades="Figma, Adobe XD, Sketch, User Research, Wireframing",
    tarifahora=45.00,
    idusuario=Usuario.objects.get(idusuario=1),
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    cargo="QA Engineer",
    habilidades="Selenium, TestNG, JUnit, Manual Testing, Automation",
    tarifahora=40.00,
    idusuario=Usuario.objects.get(idusuario=2),
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    cargo="Senior DevOps Engineer",
    habilidades="Docker, Kubernetes, Jenkins, AWS, CI/CD",
    tarifahora=55.00,
    idusuario=Usuario.objects.get(idusuario=3),
)

# Recursos Materiales
Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Monitor 4K"),
    costounidad=499.99,
    fechacompra="2023-06-01",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    costounidad=1299.99,
    fechacompra="2023-06-15",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    costounidad=1599.99,
    fechacompra="2023-08-15",
)

# Software como Recurso Material
Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    costounidad=599.99,
    fechacompra="2023-07-01",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia IDE Premium"),
    costounidad=199.99,
    fechacompra="2023-07-15",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Base de Datos Enterprise"),
    costounidad=999.99,
    fechacompra="2023-09-01",
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Diseñador UX/UI"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Monitor 4K"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Diseño UX/UI"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    idequipo=Equipo.objects.get(nombreequipo="Equipo de QA"),
)

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

# Create notifications for different users and scenarios
Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=1),
    mensaje="Reunión de planificación del sprint mañana a las 10:00 AM.",
    leido=False,
    fechacreacion="2023-12-10T08:00:00Z",
    prioridad="alta",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2023-12-11T09:45:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Nueva tarea asignada: Implementar autenticación OAuth.",
    leido=False,
    fechacreacion="2023-12-09T15:30:00Z",
    prioridad="media",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2023-12-10T09:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=3),
    mensaje="Los tests de integración han fallado en el ambiente de QA.",
    leido=False,
    fechacreacion="2023-12-08T11:00:00Z",
    prioridad="alta",
    categoria="QA",
    archivada=False,
    fecha_recordatorio="2023-12-08T11:30:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=1),
    mensaje="Actualización de librería UI disponible para el proyecto.",
    leido=True,
    fechacreacion="2023-12-07T09:15:00Z",
    prioridad="baja",
    categoria="Frontend",
    archivada=True,
    fecha_recordatorio="2023-12-08T10:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Revisión de código pendiente en el PR #123.",
    leido=False,
    fechacreacion="2023-12-06T14:20:00Z",
    prioridad="media",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2023-12-07T10:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=3),
    mensaje="Nuevo reporte de bugs en el módulo de usuarios.",
    leido=True,
    fechacreacion="2023-12-05T16:45:00Z",
    prioridad="alta",
    categoria="QA",
    archivada=False,
    fecha_recordatorio="2023-12-06T09:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=1),
    mensaje="Sprint review programada para el viernes.",
    leido=False,
    fechacreacion="2023-12-04T10:30:00Z",
    prioridad="media",
    categoria="Otro",
    archivada=False,
    fecha_recordatorio="2023-12-08T14:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(idusuario=2),
    mensaje="Actualización de documentación técnica requerida.",
    leido=True,
    fechacreacion="2023-12-03T13:15:00Z",
    prioridad="baja",
    categoria="Backend",
    archivada=True,
    fecha_recordatorio="2023-12-04T11:00:00Z",
)

# Create historical records for notifications
Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=1),
        mensaje="Reunión de planificación del sprint mañana a las 10:00 AM.",
    ),
    fechalectura="2023-12-10T09:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Nueva tarea asignada: Implementar autenticación OAuth.",
    ),
    fechalectura="2023-12-09T16:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=3),
        mensaje="Los tests de integración han fallado en el ambiente de QA.",
    ),
    fechalectura="2023-12-08T12:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=1),
        mensaje="Actualización de librería UI disponible para el proyecto.",
    ),
    fechalectura="2023-12-07T10:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Revisión de código pendiente en el PR #123.",
    ),
    fechalectura="2023-12-06T15:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=3),
        mensaje="Nuevo reporte de bugs en el módulo de usuarios.",
    ),
    fechalectura="2023-12-05T17:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=1),
        mensaje="Sprint review programada para el viernes.",
    ),
    fechalectura="2023-12-04T11:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idusuario=Usuario.objects.get(idusuario=2),
        mensaje="Actualización de documentación técnica requerida.",
    ),
    fechalectura="2023-12-03T14:00:00Z",
)

Requerimiento.objects.create(
    descripcion="Módulo de gestión de usuarios y permisos",
    fechacreacion="2023-07-01T08:00:00Z",
    fechamodificacion="2023-07-01T08:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Desarrollo de interfaz de usuario responsive",
    fechacreacion="2023-07-02T09:00:00Z",
    fechamodificacion="2023-07-02T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Gestión de Inventarios"),
)

Requerimiento.objects.create(
    descripcion="Implementación de sistema de autenticación OAuth",
    fechacreacion="2023-08-15T10:00:00Z",
    fechamodificacion="2023-08-15T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Desarrollo de módulos de cursos interactivos",
    fechacreacion="2023-08-16T11:00:00Z",
    fechamodificacion="2023-08-16T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Plataforma E-learning"),
)

Requerimiento.objects.create(
    descripcion="Integración de pasarela de pagos",
    fechacreacion="2023-09-01T09:00:00Z",
    fechamodificacion="2023-09-01T09:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Sistema de seguimiento en tiempo real",
    fechacreacion="2023-09-02T10:00:00Z",
    fechamodificacion="2023-09-02T10:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="App Móvil de Delivery"),
)

Requerimiento.objects.create(
    descripcion="Implementación de dashboards analíticos",
    fechacreacion="2023-10-01T08:30:00Z",
    fechamodificacion="2023-10-01T08:30:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Integración con múltiples fuentes de datos",
    fechacreacion="2023-10-02T09:30:00Z",
    fechamodificacion="2023-10-02T09:30:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Sistema de Business Intelligence"),
)

Requerimiento.objects.create(
    descripcion="Sistema de tickets y seguimiento",
    fechacreacion="2023-11-15T11:00:00Z",
    fechamodificacion="2023-11-15T11:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Requerimiento.objects.create(
    descripcion="Chat en tiempo real para soporte",
    fechacreacion="2023-11-16T12:00:00Z",
    fechamodificacion="2023-11-16T12:00:00Z",
    idproyecto=Proyecto.objects.get(nombreproyecto="Portal de Atención al Cliente"),
)

Tarea.objects.create(
    nombretarea="Diseño de base de datos de usuarios",
    fechainicio="2023-07-05",
    fechafin="2023-07-15",
    duracionestimada=10,
    duracionactual=8,
    dificultad=2,
    estado="Completada",
    prioridad=1,
    costoestimado=1500.00,
    costoactual=1200.00,
    fechacreacion="2023-07-05T09:00:00Z",
    fechamodificacion="2023-07-15T16:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de usuarios y permisos"
    ),
)

# Create tasks for different requirements
Tarea.objects.create(
    nombretarea="Implementación de la pantalla de login",
    fechainicio="2023-09-05",
    fechafin="2023-09-15",
    duracionestimada=10,
    duracionactual=12,
    dificultad=3,
    estado="En Progreso",
    prioridad=1,
    costoestimado=2000.00,
    costoactual=2200.00,
    fechacreacion="2023-09-05T10:00:00Z",
    fechamodificacion="2023-09-10T12:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de usuarios y permisos"
    ),
)

Tarea.objects.create(
    nombretarea="Diseño de interfaz de usuario",
    fechainicio="2023-09-20",
    fechafin="2023-09-30",
    duracionestimada=15,
    duracionactual=13,
    dificultad=2,
    estado="Completada",
    prioridad=2,
    costoestimado=3000.00,
    costoactual=2800.00,
    fechacreacion="2023-09-20T09:00:00Z",
    fechamodificacion="2023-09-30T16:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Módulo de gestión de usuarios y permisos"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de dashboard analítico",
    fechainicio="2023-10-01",
    fechafin="2023-10-20",
    duracionestimada=20,
    duracionactual=18,
    dificultad=4,
    estado="En Progreso",
    prioridad=1,
    costoestimado=4500.00,
    costoactual=4000.00,
    fechacreacion="2023-10-01T08:00:00Z",
    fechamodificacion="2023-10-15T14:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Implementación de dashboards analíticos"
    ),
)

Tarea.objects.create(
    nombretarea="Configuración de base de datos",
    fechainicio="2023-10-05",
    fechafin="2023-10-15",
    duracionestimada=12,
    duracionactual=10,
    dificultad=3,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2500.00,
    costoactual=0.00,
    fechacreacion="2023-10-05T09:00:00Z",
    fechamodificacion="2023-10-05T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Integración con múltiples fuentes de datos"
    ),
)

Tarea.objects.create(
    nombretarea="Desarrollo de API REST",
    fechainicio="2023-10-15",
    fechafin="2023-10-30",
    duracionestimada=16,
    duracionactual=14,
    dificultad=3,
    estado="En Progreso",
    prioridad=1,
    costoestimado=3500.00,
    costoactual=3000.00,
    fechacreacion="2023-10-15T10:00:00Z",
    fechamodificacion="2023-10-25T15:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Sistema de tickets y seguimiento"
    ),
)

Tarea.objects.create(
    nombretarea="Implementación de chat en tiempo real",
    fechainicio="2023-11-01",
    fechafin="2023-11-15",
    duracionestimada=14,
    duracionactual=0,
    dificultad=4,
    estado="Pendiente",
    prioridad=3,
    costoestimado=4000.00,
    costoactual=0.00,
    fechacreacion="2023-11-01T09:00:00Z",
    fechamodificacion="2023-11-01T09:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Chat en tiempo real para soporte"
    ),
)

Tarea.objects.create(
    nombretarea="Pruebas de integración",
    fechainicio="2023-11-16",
    fechafin="2023-11-25",
    duracionestimada=10,
    duracionactual=0,
    dificultad=2,
    estado="Pendiente",
    prioridad=2,
    costoestimado=2000.00,
    costoactual=0.00,
    fechacreacion="2023-11-16T08:00:00Z",
    fechamodificacion="2023-11-16T08:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        descripcion="Chat en tiempo real para soporte"
    ),
)

# Create historical task records
Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
    fechacambio="2023-09-10T12:00:00Z",
    descripcioncambio="Se inició la tarea con estado: En Progreso",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
    fechacambio="2023-09-15T16:00:00Z",
    descripcioncambio="Se actualizó el progreso: 75% completado",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
    fechacambio="2023-09-20T09:00:00Z",
    descripcioncambio="Tarea creada con estado: Pendiente",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
    fechacambio="2023-09-30T16:00:00Z",
    descripcioncambio="Tarea completada satisfactoriamente",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
    fechacambio="2023-10-01T08:00:00Z",
    descripcioncambio="Se asignaron recursos adicionales a la tarea",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
    fechacambio="2023-10-15T14:00:00Z",
    descripcioncambio="Actualización de estimación: se requieren 2 días adicionales",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de base de datos"),
    fechacambio="2023-10-05T09:00:00Z",
    descripcioncambio="Tarea creada y asignada al equipo de desarrollo",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
    fechacambio="2023-10-15T10:00:00Z",
    descripcioncambio="Se inició el desarrollo de endpoints principales",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
    fechacambio="2023-10-25T15:00:00Z",
    descripcioncambio="Integración con servicios externos completada",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de chat en tiempo real"),
    fechacambio="2023-11-01T09:00:00Z",
    descripcioncambio="Se definieron los requerimientos técnicos",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de base de datos de usuarios"),
    fechacambio="2023-07-15T16:00:00Z",
    descripcioncambio="Tarea completada antes del tiempo estimado",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
    fechainicioreal="2023-09-05",
    fechafinreal="2023-09-15",
    porcentajecompletado=75.00,
    alertagenerada=True,
    fechamodificacion="2023-09-12T14:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
    fechainicioreal="2023-09-20",
    fechafinreal="2023-09-30",
    porcentajecompletado=100.00,
    alertagenerada=False,
    fechamodificacion="2023-09-30T16:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
    fechainicioreal="2023-10-01",
    fechafinreal=None,  # Still ongoing
    porcentajecompletado=45.00,
    alertagenerada=True,
    fechamodificacion="2023-10-15T14:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de base de datos"),
    fechainicioreal="2023-10-05",
    fechafinreal=None,  # Not started yet
    porcentajecompletado=0.00,
    alertagenerada=False,
    fechamodificacion="2023-10-05T09:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
    fechainicioreal="2023-10-15",
    fechafinreal=None,
    porcentajecompletado=60.00,
    alertagenerada=True,
    fechamodificacion="2023-10-25T15:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de chat en tiempo real"),
    fechainicioreal="2023-11-01",
    fechafinreal=None,
    porcentajecompletado=0.00,
    alertagenerada=False,
    fechamodificacion="2023-11-01T09:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de base de datos de usuarios"),
    fechainicioreal="2023-07-05",
    fechafinreal="2023-07-15",
    porcentajecompletado=100.00,
    alertagenerada=False,
    fechamodificacion="2023-07-15T16:00:00Z",
)

# Create Task-Resource assignments
Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
    idrecurso=Recurso.objects.get(nombrerecurso="Diseñador UX/UI"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
    idrecurso=Recurso.objects.get(nombrerecurso="Licencia Adobe Creative Suite"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
    idrecurso=Recurso.objects.get(nombrerecurso="DevOps Engineer"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de base de datos"),
    idrecurso=Recurso.objects.get(nombrerecurso="Servidor de Desarrollo"),
    cantidad=1,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
    idrecurso=Recurso.objects.get(nombrerecurso="Analista QA"),
    cantidad=2,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de chat en tiempo real"),
    idrecurso=Recurso.objects.get(nombrerecurso="Estación de Trabajo"),
    cantidad=3,
)

# Create alerts for different tasks
Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
    tipoalerta="retraso",
    mensaje="La tarea está retrasada según el cronograma establecido.",
    activa=True,
    fechacreacion="2023-09-12T14:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
    tipoalerta="riesgo",
    mensaje="Se identificaron problemas de compatibilidad con navegadores antiguos.",
    activa=True,
    fechacreacion="2023-09-25T10:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
    tipoalerta="presupuesto",
    mensaje="El costo actual está excediendo el presupuesto planificado.",
    activa=True,
    fechacreacion="2023-10-05T16:30:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Configuración de base de datos"),
    tipoalerta="bloqueo",
    mensaje="Dependencia bloqueante con el equipo de infraestructura.",
    activa=True,
    fechacreacion="2023-10-15T11:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
    tipoalerta="retraso",
    mensaje="La integración con servicios externos está tomando más tiempo del estimado.",
    activa=True,
    fechacreacion="2023-10-20T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Implementación de chat en tiempo real"),
    tipoalerta="riesgo",
    mensaje="Posibles problemas de escalabilidad identificados.",
    activa=False,
    fechacreacion="2023-11-01T15:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(nombretarea="Pruebas de integración"),
    tipoalerta="presupuesto",
    mensaje="Se requieren recursos adicionales para completar las pruebas.",
    activa=True,
    fechacreacion="2023-11-16T13:00:00Z",
)

# Create historical records for alerts
Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Implementación de la pantalla de login"),
        tipoalerta="retraso",
    ),
    fecharesolucion="2023-09-15T16:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Diseño de interfaz de usuario"),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2023-09-30T14:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Implementación de dashboard analítico"),
        tipoalerta="presupuesto",
    ),
    fecharesolucion="2023-10-10T11:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Configuración de base de datos"),
        tipoalerta="bloqueo",
    ),
    fecharesolucion="2023-10-20T15:30:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Desarrollo de API REST"),
        tipoalerta="retraso",
    ),
    fecharesolucion="2023-10-25T17:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idtarea=Tarea.objects.get(nombretarea="Implementación de chat en tiempo real"),
        tipoalerta="riesgo",
    ),
    fecharesolucion="2023-11-05T09:00:00Z",
)

# Create activities for different users and actions
Actividad.objects.create(
    nombre="Login usuario",
    descripcion="Inicio de sesión exitoso",
    fechacreacion="2023-12-01T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Login",
)

Actividad.objects.create(
    nombre="Creación de proyecto",
    descripcion="Se creó el proyecto 'Sistema de Gestión de Inventarios'",
    fechacreacion="2023-12-01T09:30:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

Actividad.objects.create(
    nombre="Modificación de tarea",
    descripcion="Se actualizó el estado de la tarea 'Implementación de dashboard analítico'",
    fechacreacion="2023-12-02T10:15:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Modificación",
)

Actividad.objects.create(
    nombre="Logout usuario",
    descripcion="Cierre de sesión exitoso",
    fechacreacion="2023-12-02T17:00:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Logout",
)

Actividad.objects.create(
    nombre="Asignación de recursos",
    descripcion="Se asignaron recursos al proyecto 'Plataforma E-learning'",
    fechacreacion="2023-12-03T11:30:00Z",
    idusuario=Usuario.objects.get(idusuario=3),
    accion="Modificación",
)

Actividad.objects.create(
    nombre="Eliminación de tarea",
    descripcion="Se eliminó una tarea del proyecto 'App Móvil de Delivery'",
    fechacreacion="2023-12-03T14:45:00Z",
    idusuario=Usuario.objects.get(idusuario=3),
    accion="Eliminación",
)

Actividad.objects.create(
    nombre="Creación de equipo",
    descripcion="Se creó el equipo 'Equipo de QA'",
    fechacreacion="2023-12-04T09:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

Actividad.objects.create(
    nombre="Modificación de requerimiento",
    descripcion="Se actualizó el requerimiento 'Sistema de tickets y seguimiento'",
    fechacreacion="2023-12-04T13:20:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Modificación",
)


# Actividades relacionadas con Equipos
Actividad.objects.create(
    nombre="Creación de Equipo",
    descripcion="Se creó el equipo 'Equipo de Desarrollo Web'",
    fechacreacion="2023-01-15T10:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

# Actividades relacionadas con Proyectos
Actividad.objects.create(
    nombre="Nuevo Proyecto Registrado",
    descripcion="Se creó el proyecto 'Sistema de Gestión de Inventarios'",
    fechacreacion="2023-07-01T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Creación",
)

# Actividades relacionadas con Recursos
Actividad.objects.create(
    nombre="Registro de Recurso",
    descripcion="Se registró el recurso 'Licencia Adobe Creative Suite'",
    fechacreacion="2023-07-01T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=3),
    accion="Creación",
)

# Actividades relacionadas con Requerimientos
Actividad.objects.create(
    nombre="Creación de Requerimiento",
    descripcion="Se agregó el requerimiento 'Módulo de gestión de usuarios y permisos'",
    fechacreacion="2023-07-01T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

# Actividades relacionadas con Tareas
Actividad.objects.create(
    nombre="Nueva Tarea Asignada",
    descripcion="Se creó la tarea 'Implementación de dashboard analítico'",
    fechacreacion="2023-10-01T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Creación",
)

# Actividades relacionadas con Monitoreo
Actividad.objects.create(
    nombre="Actualización de Monitoreo",
    descripcion="Se actualizó el progreso de la tarea 'Diseño de interfaz de usuario'",
    fechacreacion="2023-09-30T16:00:00Z",
    idusuario=Usuario.objects.get(idusuario=3),
    accion="Modificación",
)

# Actividades relacionadas con Alertas
Actividad.objects.create(
    nombre="Alerta Generada",
    descripcion="Se generó una alerta de retraso en la tarea 'Implementación de la pantalla de login'",
    fechacreacion="2023-09-12T14:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

# Actividades relacionadas con Notificaciones
Actividad.objects.create(
    nombre="Envío de Notificación",
    descripcion="Se envió notificación sobre reunión de planificación del sprint",
    fechacreacion="2023-12-10T08:00:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Creación",
)

# Actividades relacionadas con Miembros
Actividad.objects.create(
    nombre="Asignación de Miembro",
    descripcion="Se asignó el recurso 'Diseñador UX/UI' al 'Equipo de Diseño UX/UI'",
    fechacreacion="2023-03-15T10:00:00Z",
    idusuario=Usuario.objects.get(idusuario=3),
    accion="Creación",
)

# Actividades relacionadas con Recursos Materiales
Actividad.objects.create(
    nombre="Registro de Recurso Material",
    descripcion="Se registró la compra de 'Monitor 4K'",
    fechacreacion="2023-06-01T11:00:00Z",
    idusuario=Usuario.objects.get(idusuario=1),
    accion="Creación",
)

# Actividades relacionadas con Recursos Humanos
Actividad.objects.create(
    nombre="Registro de Recurso Humano",
    descripcion="Se registró el recurso humano 'DevOps Engineer'",
    fechacreacion="2023-08-01T09:00:00Z",
    idusuario=Usuario.objects.get(idusuario=2),
    accion="Creación",
)

print("Datos de prueba generados con éxito.")
