from django.utils.timezone import now
from dashboard.models import (
    Administrador,
    Jefeproyecto,
    Desarrollador,
    Tester
)
from script.random_user import generar_usuarios

print("Iniciando generación de datos de prueba...")

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

print("Proceso finalizado")
