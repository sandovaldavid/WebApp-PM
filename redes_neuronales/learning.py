import os
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from ml_model import crear_modelo

# Obtener la ruta absoluta del directorio actual
current_dir = os.path.dirname(os.path.abspath(__file__))
# Construir la ruta al archivo CSV
csv_path = os.path.join(os.path.dirname(current_dir), 'data', 'estimacion_tiempos.csv')

# Cargar los datos
datos = pd.read_csv(csv_path)
X = datos[['complejidad', 'prioridad', 'subtareas']].values
y = datos['duracion'].values

modelo = crear_modelo()
modelo.fit(X, y, epochs=100, verbose=1)
modelo.save('modelo_estimacion_nuevo.h5')
