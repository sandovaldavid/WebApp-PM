from faker import Faker
import uuid
from dashboard.models import Usuario

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
            rol = rol_user
            token = str(uuid.uuid4())

            # Crear el usuario
            usuario = Usuario.objects.create(
                nombreusuario=nombreusuario,
                username=username,
                email=email,
                contrasena=contrasena,
                rol=rol,
                token=token
            )
            usuarios_creados.append(usuario)
            print(f"Usuario creado: {username}")
            
        except Exception as e:
            print(f"Error creando usuario: {str(e)}")
            continue
            
    return usuarios_creados