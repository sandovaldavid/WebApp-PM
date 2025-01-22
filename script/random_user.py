from faker import Faker
import uuid
from dashboard.models import Usuario
from django.contrib.auth.hashers import make_password
from django.utils import timezone

def generar_usuarios(num_usuarios, rol_user):
    fake = Faker()
    usuarios_creados = []
    
    for _ in range(num_usuarios):
        try:
            # Crear datos de usuario ficticios
            nombreusuario = fake.name()
            username = fake.user_name()
            email = fake.email()
            contrasena = fake.password(length=12)
            hashed_password = make_password(contrasena)
            rol = rol_user
            token = str(uuid.uuid4())
                        # Generar fecha aleatoria entre hace 1 año y hoy
            fechacreacion = fake.date_time_between(
                start_date='-1y',
                end_date='now',
                tzinfo=timezone.get_current_timezone()
            )

            # Crear el usuario
            usuario = Usuario.objects.create(
                nombreusuario=nombreusuario,
                username=username,
                email=email,
                contrasena=hashed_password,
                rol=rol,
                token=token,
                fechacreacion=fechacreacion,
                confirmado = True
            )
            usuarios_creados.append(usuario)
            print(f"Usuario creado: {username}")
            
        except Exception as e:
            print(f"Error creando usuario: {str(e)}")
            continue
            
    return usuarios_creados