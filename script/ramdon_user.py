from faker import Faker
from dashboard.models import Usuario  # Reemplaza 'myapp' con el nombre de tu aplicación
from django.apps import apps
import pytz


def generate_test_users(num_users=10):
    fake = Faker()
    timezone = pytz.timezone("UTC")  # Cambia 'UTC' por tu zona horaria si es necesario

    for _ in range(num_users):
        unique_username = fake.unique.user_name()
        unique_email = fake.unique.email()

        Usuario.objects.create(
            username = unique_username,
            nombreusuario=unique_username,
            email=unique_email,
            contrasena=fake.password(length=12),
            rol=fake.random_element(elements=["admin", "user", "manager"]),
            fechacreacion=fake.date_time_this_year(
                tzinfo=timezone
            ),  # Uso correcto de tzinfo
            fechamodificacion=fake.date_time_this_month(
                tzinfo=timezone
            ),  # Uso correcto de tzinfo
            token=fake.uuid4(),
            confirmado=fake.boolean(chance_of_getting_true=75),
        )

    print(f"{num_users} usuarios de prueba creados exitosamente.")


generate_test_users(10)  # Cambia 20 por el número de usuarios que deseas crear
