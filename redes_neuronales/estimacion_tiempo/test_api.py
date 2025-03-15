import os
import sys
import requests
import json
from getpass import getpass

# Configurar el path del proyecto Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")

import django

django.setup()


def login_django():
    """Iniciar sesión en Django para obtener cookies de sesión"""
    username = input("Usuario: ")
    password = getpass("Contraseña: ")

    session = requests.Session()

    # Obtener token CSRF
    response = session.get('http://localhost:8000/login/')
    if response.status_code != 200:
        print(f"Error al obtener token CSRF: {response.status_code}")
        return None

    # El token CSRF normalmente está en una cookie
    csrftoken = session.cookies.get('csrftoken')

    # Iniciar sesión
    login_data = {
        'username': username,
        'password': password,
        'csrfmiddlewaretoken': csrftoken,
    }

    headers = {'Referer': 'http://localhost:8000/login/', 'X-CSRFToken': csrftoken}

    response = session.post(
        'http://localhost:8000/login/', data=login_data, headers=headers
    )

    if response.status_code == 200 and 'login' not in response.url:
        print("Inicio de sesión exitoso")
        return session
    else:
        print("Error al iniciar sesión")
        return None


def test_estimacion_tarea(session, tarea_id):
    """Prueba la API de estimación de tiempo para una tarea"""
    url = 'http://localhost:8000/redes-neuronales/estimacion/api/estimacion/tarea'

    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': session.cookies.get('csrftoken'),
    }

    data = {'tarea_id': tarea_id}

    response = session.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(response.json())


def test_reestimacion_tarea(session, tarea_id):
    """Prueba la API de reestimación de una tarea"""
    url = 'http://localhost:8000/redes-neuronales/estimacion/api/estimacion/tarea/reestimar'

    headers = {
        'Content-Type': 'application/json',
        'X-CSRFToken': session.cookies.get('csrftoken'),
    }

    data = {'tarea_id': tarea_id}

    response = session.post(url, json=data, headers=headers)
    print(f"Status: {response.status_code}")
    print(response.json())


def test_estimacion_proyecto(session, proyecto_id):
    """Prueba la API de estimación de proyecto"""
    url = f'http://localhost:8000/redes-neuronales/estimacion/api/estimacion/proyecto/{proyecto_id}'

    response = session.get(url)
    print(f"Status: {response.status_code}")
    print(response.json())


if __name__ == "__main__":
    print("=== Test de APIs de Estimación de Tiempo ===")

    # Iniciar sesión
    session = login_django()
    if not session:
        exit(1)

    while True:
        print("\nSeleccione una opción:")
        print("1. Estimar tiempo para una tarea")
        print("2. Reestimar una tarea")
        print("3. Estimar completitud de un proyecto")
        print("4. Salir")

        option = input("Opción: ")

        if option == "1":
            tarea_id = int(input("ID de la tarea: "))
            test_estimacion_tarea(session, tarea_id)
        elif option == "2":
            tarea_id = int(input("ID de la tarea: "))
            test_reestimacion_tarea(session, tarea_id)
        elif option == "3":
            proyecto_id = int(input("ID del proyecto: "))
            test_estimacion_proyecto(session, proyecto_id)
        elif option == "4":
            print("Saliendo...")
            break
        else:
            print("Opción no válida")
