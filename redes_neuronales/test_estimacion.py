from estimacion import predecir_duracion

def test_estimaciones():
    # Test cases with different complexity levels
    test_cases = [
        # (complejidad, prioridad, subtareas)
        (1, 1, 2),    # Tarea simple, baja prioridad, pocas subtareas
        (3, 2, 5),    # Tarea media, prioridad normal, subtareas moderadas
        (5, 3, 10),   # Tarea compleja, alta prioridad, muchas subtareas
        (4, 2, 7),    # Tarea media-alta, prioridad normal, subtareas moderadas
        (2, 3, 3),    # Tarea simple, alta prioridad, pocas subtareas
    ]

    print("\nPruebas de Estimación de Duración:")
    print("====================================")
    
    for comp, prior, sub in test_cases:
        estimacion = predecir_duracion(comp, prior, sub)
        print(f"\nComplejidad: {comp}")
        print(f"Prioridad: {prior}")
        print(f"Subtareas: {sub}")
        print(f"Estimación de duración: {estimacion:.2f} horas")
        print("------------------------------------")

if __name__ == "__main__":
    test_estimaciones()