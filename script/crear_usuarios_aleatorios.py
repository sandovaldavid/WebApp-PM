from random_user import generar_usuarios

print("=== Script de creación de usuarios aleatorios ===")

# Roles a crear
roles = ["administrador", "jefeproyecto", "desarrollador", "tester", "cliente"]

# Cantidad por cada rol
cantidad = 5

# Generar usuarios para cada rol
for rol in roles:
    print(f"\nGenerando {cantidad} usuarios con rol '{rol}'...")
    usuarios = generar_usuarios(cantidad, rol)
    print(f"Se crearon {len(usuarios)} usuarios con rol {rol}")

print("\n=== Proceso completado ===")
