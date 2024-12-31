from django.utils.timezone import now
from dashboard.models import (
    Actividad,
    Administrador,
    Alerta,
    Cliente,
    Desarrollador,
    Entradamodeloestimacionrnn,
    Equipo,
    Historialalerta,
    Historialnotificacion,
    Historialreporte,
    Historialreporteusuario,
    Historialtarea,
    Jefeproyecto,
    Miembro,
    Modeloestimacionrnn,
    Monitoreotarea,
    Notificacion,
    Proyecto,
    Recurso,
    Recursohumano,
    Recursomaterial,
    Reporte,
    Reporteusuario,
    Requerimiento,
    Resultadosrnn,
    Rolmoduloacceso,
    Salidamodeloestimacionrnn,
    Tarea,
    Tarearecurso,
    Tester,
    Tiporecurso,
    Usuario,
    Usuariorolmodulo,
)

print("Generando datos de prueba...")

Usuario.objects.create(
    username="usuario1",
    nombreusuario="usuario_prueba_1",
    email="usuario.prueba@example.com",
    contrasena="contrasena_segura123",
    rol="admin",
    fechacreacion=now(),
    fechamodificacion=now(),
)
Usuario.objects.create(
    username="usuario2",
    nombreusuario="usuario_prueba_2",
    email="usuario2.prueba@example.com",
    contrasena="contrasena_segura123",
    rol="admin",
    fechacreacion=now(),
    fechamodificacion=now(),
)

Usuario.objects.create(
    username="usuario3",
    nombreusuario="usuario_prueba_3",
    email="usuario3.prueba@example.com",
    contrasena="contrasena_segura123",
    rol="admin",
    fechacreacion=now(),
    fechamodificacion=now(),
)

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

Proyecto.objects.create(
    nombreproyecto="Desarrollo de Aplicación Web",
    descripcion="Desarrollo de una plataforma web para gestión de proyectos.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
    fechainicio="2023-06-01",
    fechafin="2023-12-01",
    presupuesto=50000.00,
    estado="En progreso",
    fechacreacion="2023-06-01T09:00:00Z",
    fechamodificacion="2023-08-01T10:30:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Campaña Publicitaria 2024",
    descripcion="Estrategia de marketing para el lanzamiento de productos nuevos.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
    fechainicio="2024-01-01",
    fechafin="2024-03-01",
    presupuesto=20000.00,
    estado="Planificado",
    fechacreacion="2023-12-01T08:30:00Z",
    fechamodificacion="2023-12-01T08:30:00Z",
)

Proyecto.objects.create(
    nombreproyecto="Campaña Publicitaria 2030",
    descripcion="Estrategia de marketing para el lanzamiento de productos nuevos.",
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
    fechainicio="2024-01-01",
    fechafin="2024-03-01",
    presupuesto=100000.00,
    estado="Planificado",
    fechacreacion="2023-12-01T08:30:00Z",
    fechamodificacion="2023-12-01T08:30:00Z",
)

Recurso.objects.create(
    nombrerecurso=" Programador Web",
    idtiporecurso=1,
    disponibilidad=True,
    fechacreacion="2023-02-15T11:00:00Z",
    fechamodificacion="2023-02-15T11:00:00Z",
)

Recurso.objects.create(
    nombrerecurso="Laptop de Desarrollo",
    idtiporecurso=2,
    disponibilidad=True,
    fechacreacion="2023-05-10T09:30:00Z",
    fechamodificacion="2023-05-10T09:30:00Z",
)

Recurso.objects.create(
    nombrerecurso="Licencia de Software",
    idtiporecurso=3,
    disponibilidad=False,
    fechacreacion="2023-07-20T15:45:00Z",
    fechamodificacion="2023-07-20T15:45:00Z",
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(
        idrecurso=1
    ),  # Asegúrate de tener un Recurso con idrecurso=1
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Desarrollo Web"),
)

Miembro.objects.create(
    idrecurso=Recurso.objects.get(
        idrecurso=2
    ),  # Asegúrate de tener un Recurso con idrecurso=2
    idequipo=Equipo.objects.get(nombreequipo="Equipo de Marketing"),
)

Recursohumano.objects.create(
    idrecurso=Recurso.objects.get(
        idrecurso=1
    ),  # Asegúrate de tener el recurso con idrecurso=1
    cargo="Desarrollador Backend",
    habilidades="Python, Django, SQL, Docker",
    tarifahora=40.00,
    idusuario=Usuario.objects.get(
        idusuario=1
    ),  # Asegúrate de tener un Usuario con idusuario=1
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(
        idrecurso=2
    ),  # Asegúrate de tener el recurso con idrecurso=3
    costounidad=120.00,
    fechacompra="2023-06-01",
)

Recursomaterial.objects.create(
    idrecurso=Recurso.objects.get(
        idrecurso=3
    ),  # Asegúrate de tener el recurso con idrecurso=3
    costounidad=140.00,
    fechacompra="2023-06-01",
)


Notificacion.objects.create(
    idusuario=Usuario.objects.get(
        idusuario=1
    ),  # Asegúrate de tener un Usuario con idusuario=1
    mensaje="Se ha asignado un nuevo proyecto a tu equipo.",
    leido=False,
    fechacreacion="2023-11-15T14:30:00Z",
    prioridad="alta",
    categoria="Backend",
    archivada=False,
    fecha_recordatorio="2023-11-16T09:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(
        idusuario=2
    ),  # Asegúrate de tener un Usuario con idusuario=2
    mensaje="El proyecto X ha cambiado de estado a completado.",
    leido=True,
    fechacreacion="2023-12-01T10:00:00Z",
    prioridad="media",
    categoria="Frontend",
    archivada=False,
    fecha_recordatorio="2023-12-02T08:00:00Z",
)

Notificacion.objects.create(
    idusuario=Usuario.objects.get(
        idusuario=3
    ),  # Asegúrate de tener un Usuario con idusuario=3
    mensaje="Tienes una nueva tarea pendiente en el proyecto Y.",
    leido=False,
    fechacreacion="2023-12-05T16:45:00Z",
    prioridad="baja",
    categoria="QA",
    archivada=False,
    fecha_recordatorio="2023-12-06T10:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idnotificacion=1
    ),  # Asegúrate de tener la notificación con idnotificacion=1
    fechalectura="2023-11-15T15:00:00Z",
)

Historialnotificacion.objects.create(
    idnotificacion=Notificacion.objects.get(
        idnotificacion=2
    ),  # Asegúrate de tener la notificación con idnotificacion=2
    fechalectura="2023-12-01T10:30:00Z",
)

Requerimiento.objects.create(
    descripcion="Desarrollo de la funcionalidad de autenticación de usuarios.",
    fechacreacion="2023-09-01T10:00:00Z",
    fechamodificacion="2023-09-02T11:00:00Z",
    idproyecto=Proyecto.objects.get(
        idproyecto=1
    ),  # Asegúrate de tener un Proyecto con idproyecto=1
)

Requerimiento.objects.create(
    descripcion="Integración de la API para la gestión de pagos.",
    fechacreacion="2023-10-01T14:30:00Z",
    fechamodificacion="2023-10-05T15:00:00Z",
    idproyecto=Proyecto.objects.get(
        idproyecto=2
    ),  # Asegúrate de tener un Proyecto con idproyecto=2
)

Requerimiento.objects.create(
    descripcion="Mejoras en la interfaz de usuario para la vista de reportes.",
    fechacreacion="2023-11-01T09:00:00Z",
    fechamodificacion="2023-11-10T16:00:00Z",
    idproyecto=Proyecto.objects.get(
        idproyecto=3
    ),  # Asegúrate de tener un Proyecto con idproyecto=3
)

Tarea.objects.create(
    nombretarea="Implementación de la pantalla de login",
    fechainicio="2023-09-05",
    fechafin="2023-09-15",
    duracionestimada=10,
    duracionactual=12,
    dificultad=3,
    estado="En progreso",
    prioridad=1,
    costoestimado=2000.00,
    costoactual=2200.00,
    fechacreacion="2023-09-05T10:00:00Z",
    fechamodificacion="2023-09-10T12:00:00Z",
    idrequerimiento=Requerimiento.objects.get(
        idrequerimiento=1
    ),  # Asegúrate de tener un Requerimiento con idrequerimiento=1
)

Tarea.objects.create(
    nombretarea="Conexión con la API de pagos",
    fechainicio="2023-10-10",
    fechafin="2023-10-20",
    duracionestimada=8,
    duracionactual=9,
    dificultad=4,
    estado="Completada",
    prioridad=2,
    costoestimado=1500.00,
    costoactual=1600.00,
    fechacreacion="2023-10-10T14:00:00Z",
    fechamodificacion="2023-10-15T15:30:00Z",
    idrequerimiento=Requerimiento.objects.get(
        idrequerimiento=2
    ),  # Asegúrate de tener un Requerimiento con idrequerimiento=2
)

Tarea.objects.create(
    nombretarea="Rediseño de la página de reportes",
    fechainicio="2023-11-05",
    fechafin="2023-11-15",
    duracionestimada=7,
    duracionactual=8,
    dificultad=2,
    estado="Pendiente",
    prioridad=3,
    costoestimado=1200.00,
    costoactual=1300.00,
    fechacreacion="2023-11-05T09:30:00Z",
    fechamodificacion="2023-11-07T10:30:00Z",
    idrequerimiento=Requerimiento.objects.get(
        idrequerimiento=3
    ),  # Asegúrate de tener un Requerimiento con idrequerimiento=3
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=1),  # Asegúrate de tener una tarea con idtarea=1
    fechacambio="2023-09-10T12:00:00Z",
    descripcioncambio="Se actualizó el estado de la tarea a 'En progreso'.",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=2),  # Asegúrate de tener una tarea con idtarea=2
    fechacambio="2023-10-15T15:30:00Z",
    descripcioncambio="La tarea se completó y el estado cambió a 'Completada'.",
)

Historialtarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=3),  # Asegúrate de tener una tarea con idtarea=3
    fechacambio="2023-11-07T10:00:00Z",
    descripcioncambio="Se actualizó la duración estimada de la tarea a 8 días.",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=1),  # Asegúrate de tener una tarea con idtarea=1
    fechainicioreal="2023-09-05",
    fechafinreal="2023-09-15",
    porcentajecompletado=75.00,
    alertagenerada=True,
    fechamodificacion="2023-09-12T14:00:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=2),  # Asegúrate de tener una tarea con idtarea=2
    fechainicioreal="2023-10-10",
    fechafinreal="2023-10-20",
    porcentajecompletado=100.00,
    alertagenerada=False,
    fechamodificacion="2023-10-18T16:30:00Z",
)

Monitoreotarea.objects.create(
    idtarea=Tarea.objects.get(idtarea=3),  # Asegúrate de tener una tarea con idtarea=3
    fechainicioreal="2023-11-05",
    fechafinreal="2023-11-15",
    porcentajecompletado=50.00,
    alertagenerada=False,
    fechamodificacion="2023-11-10T09:00:00Z",
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(idtarea=1),  # Asegúrate de tener una tarea con idtarea=1
    idrecurso=Recurso.objects.get(
        idrecurso=1
    ),  # Asegúrate de tener un recurso con idrecurso=1
    cantidad=3,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(idtarea=2),  # Asegúrate de tener una tarea con idtarea=2
    idrecurso=Recurso.objects.get(
        idrecurso=2
    ),  # Asegúrate de tener un recurso con idrecurso=2
    cantidad=5,
)

Tarearecurso.objects.create(
    idtarea=Tarea.objects.get(idtarea=3),  # Asegúrate de tener una tarea con idtarea=3
    idrecurso=Recurso.objects.get(
        idrecurso=3
    ),  # Asegúrate de tener un recurso con idrecurso=3
    cantidad=2,
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(idtarea=1),  # Asegúrate de tener una tarea con idtarea=1
    tipoalerta="Vencimiento de tarea",
    mensaje="La tarea está cerca de su fecha de vencimiento. Por favor, revisa el progreso.",
    activa=True,
    fechacreacion="2023-12-10T09:00:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(idtarea=2),  # Asegúrate de tener una tarea con idtarea=2
    tipoalerta="Retraso en tarea",
    mensaje="La tarea ha superado su fecha límite. Es necesario tomar medidas inmediatas.",
    activa=True,
    fechacreacion="2023-12-05T14:30:00Z",
)

Alerta.objects.create(
    idtarea=Tarea.objects.get(idtarea=3),  # Asegúrate de tener una tarea con idtarea=3
    tipoalerta="Finalización de tarea",
    mensaje="La tarea ha sido completada con éxito.",
    activa=False,
    fechacreacion="2023-11-25T18:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idalerta=1
    ),  # Asegúrate de tener una alerta con idalerta=1
    fecharesolucion="2023-12-10T10:00:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idalerta=2
    ),  # Asegúrate de tener una alerta con idalerta=2
    fecharesolucion="2023-12-06T08:30:00Z",
)

Historialalerta.objects.create(
    idalerta=Alerta.objects.get(
        idalerta=3
    ),  # Asegúrate de tener una alerta con idalerta=3
    fecharesolucion="2023-11-25T18:30:00Z",
)

print("Datos de prueba generados con éxito.")
