# Explicación de la Red Neural para Estimación de Tiempos de Tareas

## Descripción general del sistema

El sistema implementado consiste en una red neuronal recurrente (RNN) avanzada que estima el tiempo de ejecución de tareas en proyectos de desarrollo de software, utilizando múltiples variables de entrada como la complejidad, tipo de tarea, fase, recursos asignados, experiencia y otros factores.

## Función de cada archivo

### 1. `data_processor.py`
Este archivo contiene la clase `DataProcessor` que se encarga de:
- Cargar datos del CSV o de la base de datos
- Preprocesar los datos (normalización, codificación one-hot)
- Dividir los datos en conjuntos de entrenamiento y validación
- Guardar y cargar los preprocesadores para uso posterior
- Procesar una tarea individual para predicción

La clase utiliza técnicas de normalización (StandardScaler) y codificación (OneHotEncoder) para transformar las características categóricas y numéricas.

### 2. `rnn_model.py` (Mejorado)
Implementa la clase `AdvancedRNNEstimator`, el núcleo del sistema con importantes optimizaciones:
- Define una arquitectura avanzada y personalizable de red neural recurrente
- Construye un modelo híbrido con características numéricas y categóricas
- Utiliza GRU o LSTM como capas recurrentes
- Soporte para capas bidireccionales para mejor captura de patrones
- Sistema avanzado de regularización (L1, L2, dropout, recurrent dropout)
- Incluye normalización de capas (Layer Normalization) o normalización por lotes (Batch Normalization)
- Conexiones residuales opcionales para modelos más profundos
- Gradient clipping para evitar problemas de explosión de gradientes
- Multiple opciones de activación (ReLU, LeakyReLU, PReLU, tanh, selu)
- Diversos optimizadores configurables (Adam, RMSprop, Nadam, SGD)
- Tasa de aprendizaje adaptable con reducción automática
- Sistema avanzado para análisis de importancia de características
- Uso de `tf.data.Dataset` para entrenamiento optimizado con caching y prefetching
- Integración completa con TensorBoard para monitorización avanzada
- Visualizaciones mejoradas del proceso de entrenamiento

La arquitectura mejorada consta de tres ramas de entrada:
1. Una rama para datos numéricos procesados mediante redes recurrentes
2. Una rama para tipos de tarea (codificados one-hot)
3. Una rama para fases (codificadas one-hot)

### 3. `evaluator.py`
Este archivo contiene la clase `ModelEvaluator` que:
- Evalúa el rendimiento del modelo entrenado
- Calcula múltiples métricas (MAE, RMSE, R²)
- Genera visualizaciones de predicciones vs. valores reales
- Analiza la importancia de las características
- Evalúa el modelo en diferentes segmentos de datos

### 4. `train_model.py` (Optimizado)
Script principal para el entrenamiento del modelo con nuevas funcionalidades:
- Sistema avanzado de argumentos para personalización completa del entrenamiento
- Soporte para múltiples configuraciones de arquitectura y optimización
- Sistema de callbacks avanzados para monitorización y control
- Checkpoints automáticos para recuperar el mejor modelo
- Integración con TensorBoard para visualización avanzada y depuración
- Evaluación segmentada por tipos de tareas
- Análisis automático de importancia de características
- Registro detallado del proceso de entrenamiento y resultados
- Compatibilidad con regularización avanzada, como L1, L2, weight decay
- Soporte para TensorFlow optimizado con GPU
- Segmentación automática de datos para análisis por tamaño de tareas
- Generación automática de archivos ZIP con modelos y resultados
- Registro de modelos en la base de datos para seguimiento

### 5. `predict.py`
Script para realizar predicciones:
- Carga un modelo previamente entrenado
- Procesa nuevos datos para predicción
- Ofrece funciones para predicciones individuales o desde un CSV

### 6. `model_service.py`
Servicio para integrar la red neural con Django:
- Inicializa el modelo y preprocesadores
- Extrae características de tareas desde la base de datos
- Estima el tiempo de ejecución de tareas
- Guarda las estimaciones en la base de datos
- Proporciona métodos para reestimación y análisis de proyectos

### 7. `views_integration.py` y `urls.py`
Estos archivos implementan las APIs para acceder al modelo desde la aplicación:
- `estimate_task_api`: Estima el tiempo para una tarea específica
- `reestimate_task_api`: Reestima una tarea después de cambios
- `project_estimation_api`: Estima el tiempo total para completar un proyecto

### 8. `retrain_model.py`
Script para reentrenar automáticamente el modelo con nuevos datos:
- Recolecta datos de tareas completadas desde la base de datos
- Preprocesa y entrena un nuevo modelo
- Actualiza el modelo en producción
- Puede ejecutarse periódicamente mediante un cronjob

### 9. `__init__.py`
Inicializa el módulo y proporciona una función para obtener una instancia del servicio de estimación.

## Explicación de la Red Neural Mejorada

La red neural implementada es de tipo recurrente (RNN), específicamente utilizando celdas GRU (Gated Recurrent Unit) o LSTM (Long Short-Term Memory). Su arquitectura avanzada está diseñada para capturar la naturaleza secuencial y las dependencias temporales que existen en las tareas de desarrollo de software.

### Características utilizadas:
1. **Complejidad**: Nivel de dificultad de la tarea (1-5)
2. **Tipo de Tarea**: Categoría (Backend, Frontend, Database, Testing, etc.)
3. **Fase**: Etapa en el ciclo de vida (Conceptualización, Desarrollo, etc.)
4. **Recursos Humanos**: Cantidad y calidad de los recursos asignados
5. **Carga de Trabajo**: Nivel de ocupación de cada recurso
6. **Experiencia**: Nivel de experiencia de los recursos y del equipo
7. **Claridad de Requisitos**: Qué tan bien definidos están los requisitos
8. **Tamaño**: Estimación en story points de la magnitud de la tarea

### Arquitectura Mejorada:
- **Entrada Numérica**: Procesa las características numéricas mediante una transformación a representación recurrente
- **Entrada Categórica**: Procesa tipos de tarea y fases mediante codificación one-hot y capas densas
- **Combinación**: Une todas las características y las procesa a través de capas densas configurables
- **Regularización Avanzada**: Utiliza combinaciones de dropout, recurrent dropout, regularización L1 y L2
- **Normalización Configurable**: Aplica batch normalization o layer normalization según configuración
- **Activaciones Avanzadas**: Soporte para ReLU, LeakyReLU, PReLU, tanh, selu
- **Conexiones Residuales**: Opción para utilizar skip connections en redes profundas
- **Gradient Clipping**: Control de explosión de gradientes para entrenamiento estable
- **Salida**: Una sola neurona con activación lineal que predice el tiempo en horas

### Nuevas Funcionalidades de Optimización:
- **Diferentes Optimizadores**: Adam, RMSprop, Nadam, SGD con configuraciones personalizables
- **Learning Rate Adaptable**: Reducción automática cuando el entrenamiento se estanca
- **Pipeline de Datos Optimizado**: Uso de tf.data.Dataset con caching y prefetching
- **Early Stopping Mejorado**: Detección inteligente de estancamiento en el entrenamiento
- **Checkpoints Automáticos**: Guardado del mejor modelo durante el entrenamiento
- **Análisis de Importancia**: Método avanzado para determinar las características más relevantes
- **TensorBoard Integration**: Visualización completa del entrenamiento y arquitectura
- **Evaluación por Segmentos**: Análisis de rendimiento según tamaño y tipo de tarea

## Cómo ejecutar la red neural mejorada

### 1. Entrenamiento del modelo avanzado

Para entrenar el modelo desde cero con configuraciones optimizadas:

```bash
cd /e:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/
python train_model.py --data-path estimacion_tiempos_optimizado.csv --use-db --output-dir models --rnn-type GRU --bidirectional --activation leaky_relu --optimizer adam --learning-rate 0.001 --batch-size 32 --dropout-rate 0.3 --use-layer-norm --tensorboard --epochs 150
```

Opciones disponibles extendidas:
- `--data-path`: Ruta al CSV con datos de entrenamiento
- `--use-db`: Obtener categorías de tipos de tarea y fases desde la BD
- `--output-dir`: Directorio para guardar el modelo y resultados
- `--epochs`: Número de épocas para entrenar (por defecto: 100)
- `--bidirectional`: Usar capa RNN bidireccional
- `--rnn-type`: Tipo de capa recurrente ('GRU' o 'LSTM')
- `--batch-size`: Tamaño del lote para entrenamiento
- `--optimizer`: Optimizador a utilizar ('adam', 'rmsprop', 'nadam', 'sgd')
- `--learning-rate`: Tasa de aprendizaje inicial
- `--activation`: Función de activación ('relu', 'leaky_relu', 'prelu', 'tanh', 'selu')
- `--dropout-rate`: Tasa de dropout para regularización
- `--use-layer-norm`: Usar normalización de capas
- `--use-residual`: Usar conexiones residuales
- `--tensorboard`: Habilitar logs detallados para TensorBoard
- `--early-stopping-patience`: Paciencia para early stopping

### 2. Realizar predicciones

Para predecir tiempos con el modelo entrenado:

```bash
cd /e:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/
python predict.py --input-file nuevas_tareas.csv --output-file predicciones.csv
```

Donde el archivo CSV de entrada debe contener columnas con los parámetros requeridos (Complejidad, Tipo_Tarea, etc.)

### 3. Integración con Django

Para usar la red neural desde la aplicación Django:

1. **Añadir las URLs**: En tu `urls.py` principal, incluir:
   ```python
   path('estimacion/', include('redes_neuronales.estimacion_tiempo.urls')),
   ```

2. **Llamar al servicio**:
   ```python
   from redes_neuronales.estimacion_tiempo import get_estimacion_service
   
   service = get_estimacion_service()
   success, estimated_time, message = service.estimate_and_save(tarea_id)
   ```

3. **Usar las APIs**:
   - POST a `/estimacion/api/estimacion/tarea` con `{"tarea_id": 123}`
   - POST a `/estimacion/api/estimacion/tarea/reestimar` con `{"tarea_id": 123}`
   - GET a `/estimacion/api/estimacion/proyecto/123`

### 4. Reentrenamiento automático

Para reentrenar el modelo con datos de la base de datos:

```bash
cd /e:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/
python retrain_model.py
```

Este proceso puede automatizarse usando un cronjob para ejecutarse periódicamente (semanal o mensualmente).

### 5. Visualización avanzada con TensorBoard

Para visualizar el entrenamiento y la arquitectura del modelo:

```bash
cd /e:/Tesis/APP_2.0/WebApp-PM/redes_neuronales/estimacion_tiempo/
tensorboard --logdir=models/logs
```

Luego abra su navegador en `http://localhost:6006` para ver:
- Gráficas de pérdida y métricas en tiempo real
- Histogramas de pesos y gradientes
- Visualización de la arquitectura del modelo
- Perfiles de rendimiento para optimización

## Beneficios de las Mejoras

1. **Mayor Precisión**: Las técnicas avanzadas de regularización y normalización mejoran la capacidad predictiva del modelo.

2. **Entrenamiento Optimizado**: El uso de `tf.data.Dataset` y técnicas de optimización aceleran significativamente el entrenamiento.

3. **Robustez Mejorada**: Las técnicas como gradient clipping y conexiones residuales hacen el modelo más estable y robusto.

4. **Análisis Detallado**: Las nuevas capacidades de análisis permiten entender mejor qué factores influyen más en la estimación.

5. **Adaptabilidad**: La arquitectura configurable permite adaptar el modelo a diferentes contextos y conjuntos de datos.

6. **Monitorización Avanzada**: La integración con TensorBoard proporciona herramientas potentes para visualizar y entender el entrenamiento.

7. **Segmentación de Análisis**: La evaluación por segmentos permite identificar dónde el modelo funciona mejor y dónde necesita mejoras.

8. **Flujo de Trabajo Optimizado**: El proceso completo desde el entrenamiento hasta la evaluación está automatizado y documentado.

## Verificación del funcionamiento

Para verificar que todo está funcionando correctamente:

1. **Verificar las métricas de evaluación**:
   - Ver el archivo `models/metrics_history.json` para seguimiento histórico
   - Revisar los gráficos en `models/training_history.png`
   - Explorar segmentación de rendimiento en `models/segmented_evaluation.png`
   - Un buen modelo debería tener un R² > 0.7 y un MAE razonable

2. **Analizar la importancia de características**:
   - Revisar `models/feature_importance.csv` para ver qué variables son más predictivas
   - Visualizar el gráfico en `models/feature_importance.png`

3. **Explorar TensorBoard para análisis profundo**:
   - Verificar el comportamiento de la tasa de aprendizaje
   - Analizar la distribución de pesos y activaciones
   - Identificar potenciales problemas como vanishing/exploding gradients

4. **Probar predicciones individuales**:
   Crear un script simple:
   ```python
   from rnn_model import AdvancedRNNEstimator
   from data_processor import DataProcessor
   
   # Cargar modelo y preprocessors
   processor = DataProcessor()
   processor.load_preprocessors('models')
   model = AdvancedRNNEstimator.load('models', 'tiempo_estimator')
   
   # Datos de ejemplo
   task_data = {
     'Complejidad': 3,
     'Tipo_Tarea': 'Backend',
     'Fase_Tarea': 'Construcción/Desarrollo',
     'Cantidad_Recursos': 2,
     'Carga_Trabajo_R1': 0.8,
     'Experiencia_R1': 4,
     'Carga_Trabajo_R2': 0.6,
     'Experiencia_R2': 3,
     'Carga_Trabajo_R3': 0,
     'Experiencia_R3': 0,
     'Experiencia_Equipo': 3,
     'Claridad_Requisitos': 0.7,
     'Tamaño_Tarea': 8
   }
   
   # Procesar y predecir
   X = processor.process_single_task(task_data)
   prediction = model.predict(X, processor.feature_dims)
   print(f"Tiempo estimado: {prediction[0]:.2f} horas")
   ```

Siguiendo estos pasos, podrás entrenar, evaluar y utilizar la red neural avanzada para estimar tiempos de tareas en tu aplicación de gestión de proyectos con mayor precisión y un control detallado del proceso.