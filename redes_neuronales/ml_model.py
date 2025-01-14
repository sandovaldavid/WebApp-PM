from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.losses import MeanSquaredError

def crear_modelo():
    modelo = Sequential([
        Dense(64, input_shape=(3,), activation='relu'),
        Dense(32, activation='relu'),
        Dense(1, activation='linear')
    ])
    modelo.compile(optimizer='adam', loss=MeanSquaredError())
    return modelo