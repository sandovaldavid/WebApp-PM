import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
import os
import sys
from django.db import connection

# Añadir la ruta del proyecto para importar modelos de Django
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "webapp.settings")
import django

django.setup()

from dashboard.models import TipoTarea, Fase


class DataProcessor:
    def __init__(self, data_path=None, use_db=False):
        """Inicializa el procesador de datos.

        Args:
            data_path: Ruta al archivo CSV de datos
            use_db: Si True, obtiene tipos de tareas y fases de la base de datos
        """
        self.data_path = data_path
        self.use_db = use_db
        self.scalers = {}
        self.encoders = {}
        self.X_train = None
        self.X_val = None
        self.y_train = None
        self.y_val = None

    def load_data(self):
        """Carga datos desde el CSV"""
        try:
            if self.data_path:
                # Especificar encoding='utf-8' para manejar caracteres especiales correctamente
                self.data = pd.read_csv(self.data_path, encoding="utf-8")
                print(f"Datos cargados correctamente. Forma: {self.data.shape}")
                return self.data
            else:
                raise ValueError("Ruta de datos no especificada")
        except Exception as e:
            print(f"Error al cargar datos: {e}")
            return None

    def get_db_categories(self):
        """Obtiene categorías de tipos de tareas y fases desde la base de datos"""
        if not self.use_db:
            return None, None

        try:
            tipos_tarea = list(TipoTarea.objects.all().values_list("nombre", flat=True))
            fases = list(Fase.objects.all().values_list("nombre", flat=True))

            if not tipos_tarea:
                tipos_tarea = [
                    "Frontend",
                    "Backend",
                    "Database",
                    "Testing",
                    "Arquitectura",
                ]
            if not fases:
                fases = [
                    "Inicio/Conceptualización",
                    "Elaboración/Requisitos",
                    "Construcción/Desarrollo",
                    "Transición/Implementación",
                    "Mantenimiento",
                ]

            print(f"Tipos de tarea desde BD: {tipos_tarea}")
            print(f"Fases desde BD: {fases}")

            return tipos_tarea, fases
        except Exception as e:
            print(f"Error al obtener categorías de la BD: {e}")
            # Valores por defecto en caso de error
            return ["Frontend", "Backend", "Database", "Testing", "Arquitectura"], [
                "Inicio/Conceptualización",
                "Elaboración/Requisitos",
                "Construcción/Desarrollo",
                "Transición/Implementación",
                "Mantenimiento",
            ]

    def preprocess_data(self, test_size=0.2, val_size=0.15):
        """Procesa los datos para entrenar el modelo con control del tamaño de conjuntos

        Args:
            test_size: Proporción del conjunto de datos a usar como prueba (0.0-1.0)
            val_size: Proporción del conjunto de datos a usar como validación (0.0-1.0)

        Returns:
            Tupla de (X_train, X_val, y_train, y_val, feature_dims)
        """
        if hasattr(self, "data") and self.data is not None:
            df = self.data.copy()

            # Verificar y corregir la columna de tamaño de tarea
            if "Tamaño_Tarea" in df.columns:
                tamano_col = "Tamaño_Tarea"
            elif "TamaÃ±o_Tarea" in df.columns:
                tamano_col = "TamaÃ±o_Tarea"
                df["Tamaño_Tarea"] = df[tamano_col]  # Crear columna con nombre correcto
            else:
                raise ValueError("No se encuentra la columna de tamaño de tarea")

            # Verificar columnas requeridas
            required_cols = [
                "Complejidad",
                "Tipo_Tarea",
                "Fase_Tarea",
                "Cantidad_Recursos",
                "Carga_Trabajo_R1",
                "Experiencia_R1",
                "Experiencia_Equipo",
                "Claridad_Requisitos",
                "Tamaño_Tarea",
                "Tiempo_Ejecucion",
            ]

            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise ValueError(f"Columnas faltantes en dataset: {missing_cols}")

            # Validar y rellenar valores faltantes en cargas de trabajo y experiencia
            for i in range(1, 4):  # Para recursos 1, 2, y 3
                carga_col = f"Carga_Trabajo_R{i}"
                exp_col = f"Experiencia_R{i}"

                # Si existe la columna pero tiene valores nulos
                if carga_col in df.columns:
                    df[carga_col] = df[carga_col].fillna(0)
                else:
                    df[carga_col] = 0

                if exp_col in df.columns:
                    df[exp_col] = df[exp_col].fillna(0)
                else:
                    df[exp_col] = 0

            # Obtener categorías desde la BD (si use_db=True)
            tipos_tarea_db, fases_db = self.get_db_categories()

            # Crear encoders para categorías
            tipo_encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")
            fase_encoder = OneHotEncoder(sparse_output=False, handle_unknown="ignore")

            # Ajustar encoders con todas las categorías posibles
            if self.use_db:
                tipo_encoder.fit(np.array(tipos_tarea_db).reshape(-1, 1))
                fase_encoder.fit(np.array(fases_db).reshape(-1, 1))
            else:
                tipo_encoder.fit(df[["Tipo_Tarea"]])
                fase_encoder.fit(df[["Fase_Tarea"]])

            # Transformar las categorías
            tipo_encoded = tipo_encoder.transform(df[["Tipo_Tarea"]])
            fase_encoded = fase_encoder.transform(df[["Fase_Tarea"]])

            # Guardar encoders
            self.encoders["tipo_tarea"] = tipo_encoder
            self.encoders["fase"] = fase_encoder

            # Características numéricas
            numeric_features = [
                "Complejidad",
                "Cantidad_Recursos",
                "Carga_Trabajo_R1",
                "Experiencia_R1",
                "Carga_Trabajo_R2",
                "Experiencia_R2",
                "Carga_Trabajo_R3",
                "Experiencia_R3",
                "Experiencia_Equipo",
                "Claridad_Requisitos",
                "Tamaño_Tarea",
            ]

            # Escalar características numéricas
            scaler = StandardScaler()
            numeric_data = df[numeric_features].values
            numeric_scaled = scaler.fit_transform(numeric_data)

            # Guardar el scaler
            self.scalers["numeric"] = scaler

            # Combinar todas las características
            X = np.hstack((numeric_scaled, tipo_encoded, fase_encoded))
            y = df["Tiempo_Ejecucion"].values

            # Guardar dimensiones y nombres de características para referencia
            self.feature_dims = {
                "numeric": len(numeric_features),
                "tipo_tarea": tipo_encoded.shape[1],
                "fase": fase_encoded.shape[1],
            }

            # Dividir en conjunto de entrenamiento y conjunto restante
            X_train, X_temp, y_train, y_temp = train_test_split(
                X, y, test_size=test_size, random_state=42
            )

            # Dividir el conjunto restante en validación y prueba
            # Si val_size es 0, usar todo como validación
            if val_size <= 0:
                X_val, X_test, y_val, y_test = X_temp, [], y_temp, []
            else:
                # val_size relativo al tamaño de X_temp
                val_ratio = val_size / test_size if test_size > 0 else 0.5
                X_val, X_test, y_val, y_test = train_test_split(
                    X_temp, y_temp, test_size=val_ratio, random_state=42
                )

            # Almacenar también los datos de prueba por si se necesitan
            self.X_train = X_train
            self.X_val = X_val
            self.y_train = y_train
            self.y_val = y_val
            self.X_test = X_test if "X_test" in locals() else None
            self.y_test = y_test if "y_test" in locals() else None

            print("Preprocesamiento completo.")
            print(f"Dimensiones de features: {self.feature_dims}")
            print(f"X_train: {X_train.shape}, y_train: {y_train.shape}")
            print(f"X_val: {X_val.shape}, y_val: {y_val.shape}")
            if len(X_test) > 0:
                print(f"X_test: {X_test.shape}, y_test: {y_test.shape}")

            return X_train, X_val, y_train, y_val, self.feature_dims
        else:
            raise ValueError("No hay datos para procesar. Ejecute load_data primero.")

    def save_preprocessors(self, output_dir="models"):
        """Guarda los preprocessors para uso posterior"""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        joblib.dump(self.scalers, os.path.join(output_dir, "scalers.pkl"))
        joblib.dump(self.encoders, os.path.join(output_dir, "encoders.pkl"))
        joblib.dump(self.feature_dims, os.path.join(output_dir, "feature_dims.pkl"))

        print(f"Preprocessors guardados en {output_dir}")

    def load_preprocessors(self, input_dir="models"):
        """Carga preprocessors guardados"""
        try:
            self.scalers = joblib.load(os.path.join(input_dir, "scalers.pkl"))
            self.encoders = joblib.load(os.path.join(input_dir, "encoders.pkl"))
            self.feature_dims = joblib.load(os.path.join(input_dir, "feature_dims.pkl"))
            print("Preprocessors cargados correctamente")
            return True
        except Exception as e:
            print(f"Error al cargar preprocessors: {e}")
            return False

    def process_single_task(self, task_data):
        """Procesa una única tarea para predicción

        Args:
            task_data: Diccionario con datos de la tarea

        Returns:
            np.array: Datos procesados listos para el modelo
        """
        if not hasattr(self, "scalers") or not hasattr(self, "encoders"):
            raise ValueError(
                "Preprocessors no cargados. Ejecute load_preprocessors primero."
            )

        # Crear un DataFrame de una sola fila
        task_df = pd.DataFrame([task_data])

        # Rellenar valores faltantes en los recursos
        for i in range(1, 4):
            carga_col = f"Carga_Trabajo_R{i}"
            exp_col = f"Experiencia_R{i}"

            if carga_col not in task_df.columns:
                task_df[carga_col] = 0
            if exp_col not in task_df.columns:
                task_df[exp_col] = 0

        # Características numéricas
        numeric_features = [
            "Complejidad",
            "Cantidad_Recursos",
            "Carga_Trabajo_R1",
            "Experiencia_R1",
            "Carga_Trabajo_R2",
            "Experiencia_R2",
            "Carga_Trabajo_R3",
            "Experiencia_R3",
            "Experiencia_Equipo",
            "Claridad_Requisitos",
            "Tamaño_Tarea",
        ]

        # Escalar datos numéricos
        numeric_data = task_df[numeric_features].values
        numeric_scaled = self.scalers["numeric"].transform(numeric_data)

        # Codificar tipo de tarea
        tipo_encoded = self.encoders["tipo_tarea"].transform(task_df[["Tipo_Tarea"]])

        # Codificar fase
        fase_encoded = self.encoders["fase"].transform(task_df[["Fase_Tarea"]])

        # Combinar todas las características
        X = np.hstack((numeric_scaled, tipo_encoded, fase_encoded))

        return X


if __name__ == "__main__":
    # Ejemplo de uso
    processor = DataProcessor(
        data_path="/e:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/estimacion_tiempos_optimizado.csv",
        use_db=True,
    )
    data = processor.load_data()

    if data is not None:
        X_train, X_val, y_train, y_val, feature_dims = processor.preprocess_data()
        processor.save_preprocessors()
