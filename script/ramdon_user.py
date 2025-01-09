import uuid

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from faker import Faker

from dashboard.models import Usuario


def generar_usuarios(num_usuarios=10):
    fake = Faker()
    for _ in range(num_usuarios):
        # Crear datos de usuario ficticios
        nombre_usuario = fake.user_name()
        username = fake.user_name()
        email = fake.email()
        contrasena = fake.password(length=12)
        rol = fake.random_element(elements=["Administrador", "user"])
        token = str(uuid.uuid4())  # Generar un token único
        confirmado = fake.boolean(
            chance_of_getting_true=75
        )  # Generar confirmación aleatoria

        # Crear el usuario
        try:
            usuario = Usuario.objects.create(
                username=username,
                nombreusuario=nombre_usuario,
                email=email,
                contrasena=make_password(
                    contrasena
                ),  # Asegurarse de encriptar la contraseña
                rol=rol,
                token=token,
                confirmado=True,
                fechacreacion=timezone.now(),
                fechamodificacion=timezone.now(),
            )

            print(f"Usuario {nombre_usuario} - {email} - {contrasena} - {rol}")
        except Exception as e:
            print(f"Error al crear usuario {nombre_usuario}: {str(e)}")


# Llamar a la función para generar 10 usuarios de prueba
generar_usuarios(10)
