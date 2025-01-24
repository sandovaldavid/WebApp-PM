## 1. ¿Qué hace nuestro sistema?
Imagina un experto que aprende a estimar cuánto tiempo tardará una tarea basándose en experiencias anteriores. Nuestra red neuronal hace exactamente eso, pero de forma automatizada.

## 2. ¿Cómo funciona?

### Entrada de Datos

1. Recibe 3 tipos de información:
   - Detalles básicos de la tarea:
     * Complejidad (1-5)
     * Prioridad (1-3)
   
   - Tipo de tarea:
     * Backend (programación interna)
     * Frontend (interfaces visuales)
     * Base de datos
     * Pruebas
     * Despliegue
   
   - Información del requerimiento:
     * Promedio de complejidad
     * Número de tareas
     * Prioridad media


### Proceso (como una receta de cocina)

1. Preparación de ingredientes:
   - Normalización: Convierte todos los números a una escala similar
   - Codificación: Traduce los tipos de tarea a números que la red puede entender

2. Procesamiento en capas:
   - Capa de Embedding: Como un traductor que convierte tipos de tarea en características útiles
   - Capa LSTM: Como una memoria que recuerda patrones importantes
   - Capas Densas: Como el cerebro que toma decisiones finales

3. Características adicionales:
   - Dropout: Como un filtro que evita que la red se vuelva "perezosa"
   - BatchNormalization: Como un equilibrador que mantiene todo en orden


### Aprendizaje

1. La red aprende como un estudiante:
   - Hace una predicción
   - Compara con el tiempo real
   - Ajusta sus cálculos
   - Repite el proceso miles de veces

2. Mejora continua:
   - Guarda el mejor modelo (como guardar la mejor receta)
   - Se adapta si comete errores grandes
   - Aprende de diferentes tipos de tareas


## 3. Ejemplo Práctico


Imagina una tarea:
- Complejidad: 4/5
- Prioridad: Alta (1/3)
- Tipo: Backend
- Parte de un requerimiento grande

La red:
1. Procesa estos datos
2. Los compara con su "experiencia" (datos de entrenamiento)
3. Estima: "Esta tarea tardará aproximadamente 15 días"


## 4. ¿Por qué es útil?


1. Consistencia:
   - No se cansa
   - No tiene sesgos personales
   - Aprende de todos los proyectos anteriores

2. Precisión:
   - Considera múltiples factores simultáneamente
   - Mejora con cada nueva estimación
   - Se adapta a diferentes tipos de proyectos


## 5. Resultados


El sistema:
- Predice tiempos con un margen de error razonable
- Identifica qué factores son más importantes
- Ayuda a planificar mejor los proyectos
