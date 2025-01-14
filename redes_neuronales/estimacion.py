# estimacion.py
import numpy as np
from tensorflow.keras.models import load_model

modelo = load_model('modelo_estimacion_nuevo.h5')

def predecir_duracion(complejidad, prioridad, subtareas):
    datos = np.array([[complejidad, prioridad, subtareas]])
    prediccion = modelo.predict(datos)
    return float(prediccion[0][0])
