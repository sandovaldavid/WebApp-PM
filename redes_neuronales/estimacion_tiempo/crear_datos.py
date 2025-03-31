import numpy as np
import pandas as pd

# Definir valores posibles para las categorías
tipos_tarea = [
    "Frontend",
    "Backend",
    "Database",
    "Testing",
    "Documentación",
    "DevOps",
    "Análisis",
]
fases_tarea = [
    "Inicio/Conceptualización",
    "Elaboración/Requisitos",
    "Construcción/Desarrollo",
    "Transición/Implementación",
    "Mantenimiento",
]
tamanos_tarea = [1, 2, 3, 5, 8, 13, 21, 34]  # Números de Fibonacci


def estimar_tiempo(
    tipo_tarea,
    fase_tarea,
    complejidad,
    cantidad_recursos,
    experiencia_equipo,
    claridad_requisitos,
    tamaño_tarea,
    carga_trabajo,
    experiencia_recurso,
):
    # Factores de calibración basados en COCOMO
    A = 2.5  # Factor de calibración ajustable
    B = 0.5  # Factor exponencial del esfuerzo

    # Pesos según el tipo de tarea
    pesos_tipo_tarea = {
        "Frontend": 1.2,
        "Backend": 1.5,
        "Database": 1.3,
        "Testing": 1.1,
        "Documentación": 0.9,
        "DevOps": 1.6,
        "Análisis": 1.4,
    }

    # Pesos según la fase de la tarea
    pesos_fase_tarea = {
        "Inicio/Conceptualización": 1.3,
        "Elaboración/Requisitos": 1.2,
        "Construcción/Desarrollo": 1.5,
        "Transición/Implementación": 1.4,
        "Mantenimiento": 1.1,
    }

    # Obtener los valores
    C1 = pesos_tipo_tarea[tipo_tarea]
    C3 = pesos_fase_tarea[fase_tarea]
    C2 = complejidad
    C4 = claridad_requisitos
    C5 = experiencia_equipo
    S = tamaño_tarea
    R = cantidad_recursos

    # Calcular el factor de productividad del equipo
    productividad_equipo = sum(
        experiencia_recurso[i] / carga_trabajo[i]
        for i in range(R)
        if carga_trabajo[i] is not None and experiencia_recurso[i] is not None
    )
    productividad_equipo /= R  # Promedio

    # Nueva fórmula de estimación con mayor peso en complejidad y claridad de requisitos
    T = (
        A
        * (S**B)
        * (((2 * C2) + C3) / 3)
        * (1 + C4 / 3)
        * (1 + C5 / 10)
        * (1 / productividad_equipo)
    )

    return round(T, 2)


# Función para generar datos sintéticos
def generar_datos(n):
    datos = []
    for i in range(n):
        tipo_tarea = np.random.choice(tipos_tarea)
        fase_tarea = np.random.choice(fases_tarea)
        complejidad = np.random.randint(1, 6)
        cantidad_recursos = np.random.randint(1, 4)
        experiencia_equipo = np.random.randint(1, 6)
        claridad_requisitos = np.random.randint(1, 6)
        tamaño_tarea = np.random.choice(tamanos_tarea)

        # Asignar recursos y sus cargas de trabajo/experiencia
        carga_trabajo = [None, None, None]
        experiencia_recurso = [None, None, None]
        for j in range(cantidad_recursos):
            carga_trabajo[j] = np.random.randint(1, 4)
            experiencia_recurso[j] = np.random.randint(1, 6)

        # Generar un tiempo de ejecución basado en los factores
        # Calcular el tiempo de ejecución basado en una fórmula más realista
        tiempo_ejecucion = estimar_tiempo(
            tipo_tarea,
            fase_tarea,
            complejidad,
            cantidad_recursos,
            experiencia_equipo,
            claridad_requisitos,
            tamaño_tarea,
            carga_trabajo,
            experiencia_recurso,
        )

        tiempo_ejecucion = max(10, int(tiempo_ejecucion))  # Evitar tiempos negativos

        # Simulación de tareas y proyectos
        tarea = f"Implementación de módulo {tipo_tarea.lower()}"
        descripcion = f"Desarrollo de la funcionalidad {tipo_tarea.lower()} en la fase de {fase_tarea.lower()}"
        proyecto = f"Proyecto de {tipo_tarea.lower()}"

        datos.append(
            [
                i + 4,
                "Mid-Level",
                tarea,
                descripcion,
                proyecto,
                complejidad,
                tipo_tarea,
                fase_tarea,
                cantidad_recursos,
                carga_trabajo[0],
                experiencia_recurso[0],
                carga_trabajo[1],
                experiencia_recurso[1],
                carga_trabajo[2],
                experiencia_recurso[2],
                experiencia_equipo,
                claridad_requisitos,
                tamaño_tarea,
                tiempo_ejecucion,
            ]
        )
    return datos


file_path = "E:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/estimacion_tiempos_20k.csv"
df_provided = pd.read_csv(file_path)
nuevos_datos_2k = generar_datos(2000)

columnas = df_provided.columns
# Crear un DataFrame para los nuevos datos
df_100k = pd.DataFrame(nuevos_datos_2k, columns=columnas)

# Guardar el nuevo CSV con 100,000 registros
csv_output_path_100k = "E:/Tesis/APP_2.0/estimacion_tiempos_2k.csv"
df_100k.to_csv(csv_output_path_100k, index=False)
csv_output_path_100k
