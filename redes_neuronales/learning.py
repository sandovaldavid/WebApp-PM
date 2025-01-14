import numpy as np
from ml_model import crear_modelo

# Datos ficticios de ejemplo (complejidad, prioridad, número de subtareas)
X = np.array([[3, 2, 5], [5, 3, 10], [1, 1, 2]])
y = np.array([10, 20, 3])  # Duración en horas

modelo = crear_modelo()
modelo.fit(X, y, epochs=100, verbose=1)
modelo.save('modelo_estimacion.h5')
