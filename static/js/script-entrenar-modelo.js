/**
 * Script para manejar el formulario de entrenamiento y la interacción con el backend.
 * Se integra con training-monitor.js para mostrar el progreso del entrenamiento.
 */

// Variables globales
let trainingMonitor = null;
let currentTrainingId = null;
let chartsInitialized = false;
let lossChart = null;
let predictionsChart = null;

// Ejecutar cuando el DOM esté completamente cargado
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar los elementos de la interfaz
    initializeUI();
    
    // Establecer los manejadores de eventos
    setupEventHandlers();
    
    // Inicializar el estado de la interfaz
    updateUIState();
    
    console.log('Script de entrenamiento inicializado correctamente');
});

/**
 * Inicializa los elementos de la interfaz de usuario
 */
function initializeUI() {
    // Mostrar/ocultar sección de subida de CSV según el método seleccionado
    const trainingMethod = document.getElementById('training_method');
    if (trainingMethod) {
        trainingMethod.addEventListener('change', function() {
            const csvSection = document.getElementById('csv_upload_section');
            const dbSection = document.getElementById('db_options_section');
            
            if (this.value === 'csv') {
                csvSection.classList.remove('hidden');
                dbSection.classList.add('hidden');
            } else {
                csvSection.classList.add('hidden');
                dbSection.classList.remove('hidden');
            }
        });
    }
    
    // Inicializar botón para limpiar logs
    const clearLogBtn = document.getElementById('clearLogBtn');
    if (clearLogBtn) {
        clearLogBtn.addEventListener('click', function() {
            const trainingLog = document.getElementById('trainingLog');
            if (trainingLog) {
                trainingLog.innerHTML = '<p class="log-line">Logs limpiados por el usuario.</p>';
            }
        });
    }
}

/**
 * Configura todos los manejadores de eventos
 */
function setupEventHandlers() {
    // Configurar el botón de inicio de entrenamiento
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    if (startTrainingBtn) {
        startTrainingBtn.addEventListener('click', startTraining);
    }
    
    // Botón para generar archivos de evaluación
    const generarArchivosBtn = document.getElementById('generar-archivos-btn');
    if (generarArchivosBtn) {
        generarArchivosBtn.addEventListener('click', generarArchivosEvaluacion);
    }
    
    // Botón para diagnosticar el entrenamiento
    const diagnosticarEntrenamientoBtn = document.getElementById('diagnosticar-entrenamiento-btn');
    if (diagnosticarEntrenamientoBtn) {
        diagnosticarEntrenamientoBtn.addEventListener('click', diagnosticarEntrenamiento);
    }
}

/**
 * Actualiza el estado de la interfaz según las condiciones actuales
 */
function updateUIState() {
    // Inicialmente ocultar la sección de resultados
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults) {
        trainingResults.classList.add('hidden');
    }
    
    // Ocultar la sección de evaluación
    const evaluationSection = document.getElementById('evaluationSection');
    if (evaluationSection) {
        evaluationSection.classList.add('hidden');
    }
    
    // Inicializar el estado del indicador de conexión SSE
    const sseStatusDot = document.getElementById('sseStatusDot');
    const sseStatusText = document.getElementById('sseStatusText');
    if (sseStatusDot && sseStatusText) {
        sseStatusDot.className = "w-2 h-2 rounded-full bg-gray-500 inline-block mr-2";
        sseStatusText.textContent = "Sin conexión";
    }
}

/**
 * Inicia el proceso de entrenamiento
 */
function startTraining() {
    console.log('Iniciando proceso de entrenamiento');
    
    // Validar formulario
    if (!validateForm()) {
        return;
    }
    
    // Mostrar sección de resultados
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults) {
        trainingResults.classList.remove('hidden');
    }
    
    // Obtener los datos del formulario
    const form = document.getElementById('trainingForm');
    const formData = new FormData(form);
    
    // Deshabilitar botón de inicio
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    if (startTrainingBtn) {
        startTrainingBtn.disabled = true;
        startTrainingBtn.classList.add('opacity-50', 'cursor-not-allowed');
        startTrainingBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Iniciando...';
    }
    
    // Actualizar estado visual
    updateTrainingStatus("Enviando configuración...", 0);
    
    // Enviar solicitud al servidor
    fetch(URLS.iniciarEntrenamiento, {
        method: 'POST',
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Guardar ID de entrenamiento
            currentTrainingId = data.training_id;
            
            // Inicializar monitor de entrenamiento
            initializeTrainingMonitor(data.training_id, data.model_name);
            
            // Actualizar interfaz
            updateUIAfterTrainingStart(data);
        } else {
            handleTrainingError(data.error || 'Error desconocido al iniciar entrenamiento');
        }
    })
    .catch(error => {
        handleTrainingError('Error al iniciar entrenamiento: ' + error.message);
    });
}

/**
 * Inicializa el monitor de entrenamiento
 * @param {string} trainingId - ID del entrenamiento
 * @param {string} modelName - Nombre del modelo
 */
function initializeTrainingMonitor(trainingId, modelName) {
    console.log(`Inicializando monitor de entrenamiento para ID: ${trainingId}`);
    
    // Actualizar el indicador de status
    const sseStatusDot = document.getElementById('sseStatusDot');
    const sseStatusText = document.getElementById('sseStatusText');
    if (sseStatusDot) sseStatusDot.className = "w-2 h-2 rounded-full bg-yellow-500 inline-block mr-2";
    if (sseStatusText) sseStatusText.textContent = "Conectando...";
    
    // Configuración de callbacks
    const callbacks = {
        onComplete: handleTrainingComplete,
        onError: handleTrainingError,
        onProgress: handleTrainingProgress
    };
    
    // Inicializar monitor (evitar instanciar múltiples veces)
    if (trainingMonitor) {
        trainingMonitor.stop(); // Detener monitor anterior si existe
    }
    
    // Crear instancia de TrainingMonitor con los selectores correctos
    trainingMonitor = new TrainingMonitor(trainingId, {
        logContainerSelector: '#trainingLog',
        progressBarSelector: '#trainingProgress',
        statusSelector: '#trainingStatus',
        currentEpochSelector: '#currentEpoch',
        remainingTimeSelector: '#remainingTime',
        trainLossSelector: '#trainLoss',
        valLossSelector: '#valLoss',
        onComplete: callbacks.onComplete,
        onError: callbacks.onError,
        onProgress: callbacks.onProgress
    });
    
    // Guardar el nombre del modelo para usarlo más tarde
    trainingMonitor.modelName = modelName;
    
    // Iniciar el monitoreo
    trainingMonitor.start();
}

/**
 * Actualiza la interfaz después de iniciar el entrenamiento
 */
function updateUIAfterTrainingStart(data) {
    // Actualizar nombre del modelo en la interfaz
    const savedModelName = document.getElementById('savedModelName');
    if (savedModelName) {
        savedModelName.textContent = data.model_name;
    }
    
    // Si se configuró como modelo principal, mostrar indicador
    const setAsMainModel = document.getElementById('setAsMainModel');
    if (setAsMainModel) {
        if (data.save_as_main) {
            setAsMainModel.classList.remove('hidden');
        } else {
            setAsMainModel.classList.add('hidden');
        }
    }
    
    // Desplazar hacia la sección de resultados
    document.getElementById('trainingResults').scrollIntoView({ 
        behavior: 'smooth'
    });
}

/**
 * Valida el formulario antes de enviar
 * @returns {boolean} Verdadero si el formulario es válido
 */
function validateForm() {
    const trainingMethod = document.getElementById('training_method').value;
    
    // Si es CSV, validar que haya archivo
    if (trainingMethod === 'csv') {
        const csvFile = document.getElementById('csv_file').files[0];
        if (!csvFile) {
            alert('Por favor, seleccione un archivo CSV.');
            return false;
        }
        
        // Validar extensión
        if (!csvFile.name.toLowerCase().endsWith('.csv')) {
            alert('El archivo debe ser de formato CSV.');
            return false;
        }
    }
    
    // Validaciones generales
    const epochs = parseInt(document.getElementById('epochs').value);
    if (isNaN(epochs) || epochs < 10) {
        alert('El número de épocas debe ser al menos 10.');
        return false;
    }
    
    return true;
}

/**
 * Maneja el evento de progreso del entrenamiento
 */
function handleTrainingProgress(data) {
    // Este método es llamado por el TrainingMonitor
    // No necesitamos implementación adicional aquí ya que
    // TrainingMonitor ya actualiza la interfaz
    
    // Si tenemos datos de historia y las gráficas están inicializadas, actualizar
    if (data.history && chartsInitialized && lossChart) {
        updateCharts(data.history);
    }
}

/**
 * Maneja la finalización exitosa del entrenamiento
 */
function handleTrainingComplete(data) {
    console.log('Entrenamiento completado:', data);
    console.log('Datos completos recibidos:', JSON.stringify(data, null, 2));
    
    // Habilitar nuevamente el botón de inicio
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    if (startTrainingBtn) {
        startTrainingBtn.disabled = false;
        startTrainingBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        startTrainingBtn.innerHTML = '<i class="fas fa-cogs mr-1"></i> Iniciar Entrenamiento';
    }
    
    // Actualizar el indicador de status
    const sseStatusDot = document.getElementById('sseStatusDot');
    const sseStatusText = document.getElementById('sseStatusText');
    if (sseStatusDot) sseStatusDot.className = "w-2 h-2 rounded-full bg-green-500 inline-block mr-2";
    if (sseStatusText) sseStatusText.textContent = "Entrenamiento completado";
    
    // Mostrar métricas finales
    const finalMetrics = document.getElementById('finalMetrics');
    if (finalMetrics) {
        finalMetrics.classList.remove('hidden');
    }
    
    // MEJORADO: Actualizar valores de métricas con manejo robusto de mayúsculas/minúsculas y valores nulos
    if (data.metrics) {
        // Normalizar métricas para manejar inconsistencia de mayúsculas/minúsculas
        const metrics = normalizeMetrics(data.metrics);
        
        // Actualizar los elementos de la interfaz con manejo seguro de nulos
        updateMetricElement('metricMSE', metrics.MSE);
        updateMetricElement('metricMAE', metrics.MAE);
        updateMetricElement('metricRMSE', metrics.RMSE);
        updateMetricElement('metricR2', metrics.R2);
    } else if (data.result && data.result.metrics) {
        // Caso alternativo: las métricas están anidadas en data.result.metrics
        const metrics = normalizeMetrics(data.result.metrics);
        
        updateMetricElement('metricMSE', metrics.MSE);
        updateMetricElement('metricMAE', metrics.MAE);
        updateMetricElement('metricRMSE', metrics.RMSE);
        updateMetricElement('metricR2', metrics.R2);
    } else {
        console.warn('No se encontraron métricas en los datos recibidos');
    }
    
    try {
        // Inicializar gráfico de pérdida si hay datos de historial
        if (data.history && data.history.loss) {
            console.log('Inicializando gráfico de pérdida con datos:', data.history);
            initializeCharts(data.history);
            chartsInitialized = true;
        } 
        // Si no hay history pero hay epoch_logs, intentar construir un historial
        else if (data.epoch_logs && Array.isArray(data.epoch_logs)) {
            console.log('Construyendo historial a partir de epoch_logs');
            const history = {
                loss: [],
                val_loss: []
            };
            
            data.epoch_logs.forEach(log => {
                if (log.loss !== undefined) history.loss.push(parseFloat(log.loss));
                if (log.val_loss !== undefined) history.val_loss.push(parseFloat(log.val_loss));
            });
            
            if (history.loss.length > 0) {
                initializeCharts(history);
                chartsInitialized = true;
            } else {
                console.warn('No se pudieron extraer datos de pérdida de los logs');
                // Crear un gráfico vacío para que al menos se muestre algo
                createEmptyChart('lossChart', 'No hay datos de pérdida disponibles');
            }
        } else {
            console.warn('No hay datos de historial para inicializar el gráfico de pérdida');
            createEmptyChart('lossChart', 'No hay datos de pérdida disponibles');
        }
        
        // Inicializar gráfico de predicciones si hay datos
        if (data.predictions && data.y_test) {
            console.log('Inicializando gráfico de predicciones');
            initializePredictionsChart(data.predictions, data.y_test);
        } else {
            console.warn('No hay datos de predicciones para inicializar el gráfico');
            createEmptyChart('predictionsChart', 'No hay datos de predicciones disponibles');
        }
    } catch (error) {
        console.error('Error al inicializar los gráficos:', error);
        
        // Crear gráficos de error para que el usuario sepa qué sucedió
        createEmptyChart('lossChart', 'Error al crear el gráfico: ' + error.message);
        createEmptyChart('predictionsChart', 'Error al crear el gráfico: ' + error.message);
    }
    
    // Solicitar evaluación automática después de un breve retraso
    setTimeout(async () => {
        try {
            const enrichedData = await enrichTrainingData(data);
            
            // Intentar inicializar gráficos con los datos enriquecidos
            if (!chartsInitialized && (enrichedData.history || enrichedData.predictions)) {
                try {
                    if (enrichedData.history && enrichedData.history.loss) {
                        initializeCharts(enrichedData.history);
                    }
                    if (enrichedData.predictions && enrichedData.y_test) {
                        initializePredictionsChart(enrichedData.predictions, enrichedData.y_test);
                    }
                    console.log('Gráficos inicializados exitosamente con datos enriquecidos');
                } catch (chartError) {
                    console.error('Error al inicializar gráficos con datos enriquecidos:', chartError);
                }
            }
            
            // Continuar con la evaluación normal para mostrar las imágenes
            requestModelEvaluation(currentTrainingId);
        } catch (err) {
            console.error('Error al procesar datos enriquecidos:', err);
            requestModelEvaluation(currentTrainingId);
        }
    }, 3000);
}

/**
 * Normaliza métricas para manejar inconsistencias de mayúsculas/minúsculas
 * @param {Object} metrics - Objeto con métricas del modelo
 * @returns {Object} Objeto normalizado con claves en mayúsculas
 */
function normalizeMetrics(metrics) {
    const normalized = {};
    
    // Crear un mapping de claves para buscar con varias formas posibles
    const keyMappings = {
        'MSE': ['MSE', 'mse', 'mean_squared_error', 'error_cuadratico_medio'],
        'MAE': ['MAE', 'mae', 'mean_absolute_error', 'error_absoluto_medio'],
        'RMSE': ['RMSE', 'rmse', 'root_mean_squared_error'],
        'R2': ['R2', 'r2', 'r-squared', 'coeficiente_determinacion']
    };
    
    // Para cada métrica normalizada, buscar en todas las variantes posibles
    for (const [normalKey, variants] of Object.entries(keyMappings)) {
        let found = false;
        for (const variant of variants) {
            if (metrics[variant] !== undefined) {
                normalized[normalKey] = metrics[variant];
                found = true;
                break;
            }
        }
        
        // Si no se encontró ninguna variante, asignar un valor predeterminado
        if (!found) {
            normalized[normalKey] = null;
        }
    }
    
    return normalized;
}

/**
 * Actualiza un elemento de métrica de forma segura
 * @param {string} elementId - ID del elemento HTML
 * @param {number|null} value - Valor a mostrar
 */
function updateMetricElement(elementId, value) {
    const element = document.getElementById(elementId);
    if (element) {
        if (value !== null && value !== undefined) {
            // Para R², usar 4 decimales; para el resto, usar 2
            const decimals = elementId === 'metricR2' ? 4 : 2;
            element.textContent = typeof value === 'number' ? value.toFixed(decimals) : value.toString();
        } else {
            element.textContent = "N/D";
        }
        
        // Añadir animación para destacar la actualización
        element.classList.add('highlight-update');
        setTimeout(() => {
            element.classList.remove('highlight-update');
        }, 1500);
    } else {
        console.warn(`Elemento ${elementId} no encontrado en el DOM`);
    }
}

/**
 * Maneja errores durante el entrenamiento
 */
function handleTrainingError(error) {
    console.error('Error en entrenamiento:', error);
    
    // Mostrar error en los logs
    const trainingLog = document.getElementById('trainingLog');
    if (trainingLog) {
        const errorMessage = document.createElement('p');
        errorMessage.className = 'log-line';
        errorMessage.style.color = '#ff6b6b';
        errorMessage.textContent = `ERROR: ${error}`;
        trainingLog.appendChild(errorMessage);
        trainingLog.scrollTop = trainingLog.scrollHeight;
    }
    
    // Actualizar status visual
    updateTrainingStatus(`Error: ${error}`, 0);
    
    // Actualizar el indicador de status
    const sseStatusDot = document.getElementById('sseStatusDot');
    const sseStatusText = document.getElementById('sseStatusText');
    if (sseStatusDot) sseStatusDot.className = "w-2 h-2 rounded-full bg-red-500 inline-block mr-2";
    if (sseStatusText) sseStatusText.textContent = "Error de conexión";
    
    // Habilitar nuevamente el botón
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    if (startTrainingBtn) {
        startTrainingBtn.disabled = false;
        startTrainingBtn.classList.remove('opacity-50', 'cursor-not-allowed');
        startTrainingBtn.innerHTML = '<i class="fas fa-cogs mr-1"></i> Reintentar';
    }
}

/**
 * Actualiza el estado del entrenamiento en la interfaz
 */
function updateTrainingStatus(status, progress) {
    const trainingStatus = document.getElementById('trainingStatus');
    const trainingProgress = document.getElementById('trainingProgress');
    
    if (trainingStatus) trainingStatus.textContent = status;
    if (trainingProgress) trainingProgress.style.width = `${progress}%`;
}

/**
 * Inicializa los gráficos de pérdida
 */
function initializeCharts(history) {
    // Gráfico de pérdida
    const lossCtx = document.getElementById('lossChart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: Array.from({ length: history.loss.length }, (_, i) => i + 1),
            datasets: [{
                label: 'Pérdida de entrenamiento',
                data: history.loss,
                borderColor: 'rgba(79, 70, 229, 1)',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 2,
                tension: 0.1
            }, {
                label: 'Pérdida de validación',
                data: history.val_loss,
                borderColor: 'rgba(236, 72, 153, 1)',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                borderWidth: 2,
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de predicciones vs valores reales
 */
function initializePredictionsChart(predictions, yTest) {
    const predictionsCtx = document.getElementById('predictionsChart').getContext('2d');
    predictionsChart = new Chart(predictionsCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Predicciones vs. Reales',
                data: yTest.map((real, i) => ({
                    x: real,
                    y: predictions[i]
                })),
                backgroundColor: 'rgba(79, 70, 229, 0.7)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 1,
                pointRadius: 4
            },
            {
                // Línea ideal (y=x)
                label: 'Ideal',
                data: (() => {
                    const min = Math.min(...yTest);
                    const max = Math.max(...yTest);
                    return [{ x: min, y: min }, { x: max, y: max }];
                })(),
                type: 'line',
                backgroundColor: 'rgba(156, 163, 175, 0.2)',
                borderColor: 'rgba(156, 163, 175, 1)',
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            plugins: {
                title: {
                    display: false
                },
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Valores reales'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Predicciones'
                    }
                }
            }
        }
    });
}

/**
 * Actualiza los gráficos con nuevos datos
 */
function updateCharts(history) {
    if (!lossChart) return;
    
    lossChart.data.labels = Array.from({ length: history.loss.length }, (_, i) => i + 1);
    lossChart.data.datasets[0].data = history.loss;
    lossChart.data.datasets[1].data = history.val_loss;
    lossChart.update();
}

/**
 * Solicita evaluación del modelo
 */
function requestModelEvaluation(modelId) {
    console.log('Solicitando evaluación para el modelo:', modelId);
    
    // Mostrar la sección de evaluación
    const evaluationSection = document.getElementById('evaluationSection');
    if (evaluationSection) {
        evaluationSection.classList.remove('hidden');
        
        // Mostrar progreso de evaluación
        const evaluationProgress = document.getElementById('evaluationProgress');
        const evaluationResults = document.getElementById('evaluationResults');
        if (evaluationProgress && evaluationResults) {
            evaluationProgress.classList.remove('hidden');
            evaluationResults.classList.add('hidden');
        }
        
        // Desplazar hacia la sección
        evaluationSection.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Enviar solicitud al servidor - CAMBIO DE GET A POST
    fetch(`${URLS.evaluarModelo}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ model_id: modelId })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Error en la respuesta del servidor');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            displayEvaluationResults(data);
        } else {
            handleEvaluationError(data.error || 'Error desconocido en evaluación');
        }
    })
    .catch(error => {
        handleEvaluationError('Error al evaluar modelo: ' + error.message);
    });
}

/**
 * Muestra los resultados de la evaluación
 */
function displayEvaluationResults(data) {
    // Ocultar progreso y mostrar resultados
    const evaluationProgress = document.getElementById('evaluationProgress');
    const evaluationResults = document.getElementById('evaluationResults');
    if (evaluationProgress && evaluationResults) {
        evaluationProgress.classList.add('hidden');
        evaluationResults.classList.remove('hidden');
    }
    
    // Mostrar métricas
    const metricsDisplay = document.getElementById('metricsDisplay');
    if (metricsDisplay && data.metrics) {
        let metricsHtml = '<ul class="space-y-2">';
        for (const [metric, value] of Object.entries(data.metrics)) {
            metricsHtml += `
                <li class="flex justify-between items-center border-b pb-1">
                    <span>${metric.replace(/_/g, ' ').toUpperCase()}</span>
                    <span class="font-semibold">${typeof value === 'number' ? value.toFixed(4) : value}</span>
                </li>`;
        }
        metricsHtml += '</ul>';
        metricsDisplay.innerHTML = metricsHtml;
    }
    
    // Mostrar imágenes si están disponibles
    if (data.feature_importance_image) {
        const featureImportanceImg = document.getElementById('featureImportanceImg');
        if (featureImportanceImg) {
            featureImportanceImg.src = data.feature_importance_image + '?t=' + new Date().getTime();
        }
    }
    
    if (data.evaluation_plots_image) {
        const evaluationPlotsImg = document.getElementById('evaluationPlotsImg');
        if (evaluationPlotsImg) {
            evaluationPlotsImg.src = data.evaluation_plots_image + '?t=' + new Date().getTime();
        }
    }
}

/**
 * Maneja errores durante la evaluación
 */
function handleEvaluationError(error) {
    console.error('Error en evaluación:', error);
    
    // Ocultar progreso y mostrar mensaje de error en sección de resultados
    const evaluationProgress = document.getElementById('evaluationProgress');
    const evaluationResults = document.getElementById('evaluationResults');
    if (evaluationProgress && evaluationResults) {
        evaluationProgress.classList.add('hidden');
        evaluationResults.classList.remove('hidden');
        evaluationResults.innerHTML = `
            <div class="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded">
                <p class="font-medium">Error en la evaluación:</p>
                <p>${error}</p>
                <button id="retryEvaluationBtn" class="mt-2 px-3 py-1 bg-red-100 hover:bg-red-200 rounded">
                    Reintentar
                </button>
            </div>
        `;
        
        // Configurar botón de reintento
        document.getElementById('retryEvaluationBtn').addEventListener('click', function() {
            requestModelEvaluation(currentTrainingId);
        });
    }
}

/**
 * Función para generar archivos de evaluación
 */
function generarArchivosEvaluacion() {
    const btn = document.getElementById('generar-archivos-btn');
    if (!btn) return;    

    const originalContent = btn.innerHTML;

    if (!currentTrainingId) {
        alert('No hay un modelo de entrenamiento activo para generar archivos.');
        return;
    }
    
    btn.disabled = true;
    btn.innerHTML = `<svg class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> Procesando...`;
    
    fetch(`${URLS.generarArchivos}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('✅ ' + data.message);
            location.reload();
        } else {
            alert('❌ ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error al procesar la solicitud.');
    })
    .finally(() => {
        btn.disabled = false;
        btn.innerHTML = originalContent;
    });
}

/**
 * Función para diagnosticar problemas de entrenamiento
 */
function diagnosticarEntrenamiento() {

    const btn = document.getElementById('diagnosticar-entrenamiento-btn');
    if (!btn) return;    

    const originalContent = btn.innerHTML;

    if (!currentTrainingId) {
        alert('No hay un entrenamiento activo para diagnosticar.');
        return;
    }  
    
    // Cambiar el botón a estado "cargando"
    btn.disabled = true;
    btn.innerHTML = `<svg class="animate-spin h-4 w-4 mr-1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
    </svg> Diagnosticando...`;
        
    fetch(`${URLS.diagnosticarEntrenamiento}?training_id=${currentTrainingId}`, {
        method: 'GET',
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showDiagnosticResults(data);         
            console.log('Diagnóstico completado:', data);
        } else {
            alert(`Error en el diagnóstico: ${data.error || 'Error desconocido'}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error de comunicación con el servidor');
    })
    .finally(() => {
        // Restaurar el botón
        btn.disabled = false;
        btn.innerHTML = originalContent;
    });
}

/**
 * Función para mostrar resultados del diagnóstico
 */
function showDiagnosticResults(data) {
    // Creamos un modal para mostrar los resultados
    const modal = document.createElement('div');
    modal.className = 'fixed inset-0 bg-gray-500 bg-opacity-75 flex items-center justify-center z-50';
    modal.id = 'diagnosticModal';

    // Analizar problemas encontrados
    let issuesHtml = '';
    const issues = data.epoch_logs.issues || [];
    if (issues.length > 0) {
        issuesHtml = `<div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <h4 class="font-semibold text-yellow-800 mb-2">Se encontraron ${issues.length} problemas:</h4>
            <ul class="list-disc pl-5 text-yellow-700">
                ${issues.map(issue => `<li>${issue.message}</li>`).join('')}
            </ul>
        </div>`;
    } else {
        issuesHtml = `<div class="mb-4 p-3 bg-green-50 border border-green-200 rounded">
            <h4 class="font-semibold text-green-800">¡Todo funciona correctamente!</h4>
            <p class="text-green-700">No se detectaron problemas en la comunicación de logs.</p>
        </div>`;
    }

    // Información sobre los logs de época encontrados
    const epochsFound = data.epoch_logs.in_cache.epochs_found || [];
    const totalFound = data.epoch_logs.total_found || 0;

    const epochLogsInfo = `<div class="mb-4">
        <h4 class="font-semibold mb-2">Logs de época encontrados:</h4>
        <ul class="list-none space-y-1">
            <li><span class="font-medium">En caché:</span> ${data.epoch_logs.in_cache.count || 0}</li>
            <li><span class="font-medium">En cola IPC:</span> ${data.epoch_logs.in_queue.queue_size || 0}</li>
            <li><span class="font-medium">Épocas detectadas:</span> ${epochsFound.length > 0 ? epochsFound.sort((a,b) => a-b).join(', ') : 'Ninguna'}</li>
            <li><span class="font-medium">Total encontrados:</span> ${totalFound}</li>
        </ul>
    </div>`;

    // Últimas actualizaciones recibidas
    let updatesHtml = '';
    const lastUpdates = data.last_updates || [];
    if (lastUpdates.length > 0) {
        updatesHtml = `<div class="mb-4">
            <h4 class="font-semibold mb-2">Últimas actualizaciones:</h4>
            <ul class="list-none space-y-0.5 text-sm bg-gray-50 p-2 rounded max-h-32 overflow-y-auto">
                ${lastUpdates.map(u => {
                    const time = new Date(u.timestamp * 1000).toLocaleTimeString();
                    const type = u.type;
                    const details = u.is_epoch_log ? ` (Época ${u.epoch_number || u.epoch})` : '';
                    return `<li>[${time}] ${type}${details}</li>`;
                }).join('')}
            </ul>
        </div>`;
    }

    // Conexión y estado general
    const connectionStatus = `<div class="grid grid-cols-2 gap-4 mb-4">
        <div>
            <h4 class="font-semibold mb-2">Estado de conexión:</h4>
            <ul class="list-none space-y-1">
                <li class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full mr-2 ${data.epoch_logs.connection_status?.redis_connected ? 'bg-green-500' : 'bg-red-500'}"></span>
                    <span class="font-medium">Redis:</span> ${data.epoch_logs.connection_status?.redis_connected ? 'Conectado' : 'No conectado'}
                </li>
                <li class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full mr-2 ${data.epoch_logs.connection_status?.ipc_queue_available ? 'bg-green-500' : 'bg-yellow-500'}"></span>
                    <span class="font-medium">Cola IPC:</span> ${data.epoch_logs.connection_status?.ipc_queue_available ? 'Disponible' : 'No disponible'}
                </li>
                <li><span class="font-medium">Estado en sesión:</span> ${data.epoch_logs.connection_status?.cache_status || 'desconocido'}</li>
                <li><span class="font-medium">Timestamp en caché:</span> ${data.epoch_logs.connection_status?.cache_timestamp ? new Date(data.epoch_logs.connection_status.cache_timestamp).toLocaleString() : 'N/A'}</li>
            </ul>
        </div>
        <div>
            <h4 class="font-semibold mb-2">Estado del proceso:</h4>
            <ul class="list-none space-y-1">
                <li class="flex items-center">
                    <span class="inline-block w-3 h-3 rounded-full mr-2 ${data.epoch_logs.process_info?.is_active ? 'bg-green-500' : 'bg-gray-500'}"></span>
                    <span class="font-medium">Proceso activo:</span> ${data.epoch_logs.process_info?.is_active ? 'Sí' : 'No'}
                </li>
                <li><span class="font-medium">Tipo:</span> ${data.epoch_logs.process_info?.is_direct ? 'Directo' : 'Indirecto/Desconocido'}</li>
                <li><span class="font-medium">Estado:</span> ${data.epoch_logs.process_info?.status || 'N/A'}</li>
            </ul>
        </div>
    </div>`;

    // Modal completo
    modal.innerHTML = `
    <div class="bg-white rounded-lg shadow-xl w-11/12 max-w-2xl p-6 max-h-[90vh] overflow-y-auto">
        <div class="flex justify-between items-center mb-4 pb-2 border-b">
            <h3 class="text-xl font-bold text-gray-800">Diagnóstico de Entrenamiento</h3>
            <button id="closeModal" class="text-gray-400 hover:text-gray-600">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"></path>
                </svg>
            </button>
        </div>
        
        ${issuesHtml}
        ${epochLogsInfo}
        ${connectionStatus}
        ${updatesHtml}
        
        <div class="mt-5 text-right">
            <button id="closeModalBtn" class="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700">
                Cerrar
            </button>
        </div>
    </div>`;

    // Añadir modal al DOM
    document.body.appendChild(modal);

    // Manejar cierre del modal
    document.getElementById('closeModal').addEventListener('click', () => modal.remove());
    document.getElementById('closeModalBtn').addEventListener('click', () => modal.remove());

    // Añadir entrada de log
    if (typeof addLogEntry === 'function') {
        addLogEntry(`Diagnóstico completado. ${issues.length > 0 ? `Se encontraron ${issues.length} problemas.` : '¡Todo funciona correctamente!'}`, 
                issues.length > 0 ? "warning" : "success");
    }
}

/**
 * Enriquece los datos recibidos del backend con datos completos de evaluación
 */
async function enrichTrainingData(data) {
    console.log('Enriqueciendo datos de entrenamiento con evaluación completa...');
    
    try {
        // Hacer solicitud de evaluación
        const response = await fetch(`${URLS.evaluarModelo}`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
            },
            body: JSON.stringify({ model_id: data.model_id || data.training_id })
        });
        
        if (!response.ok) {
            throw new Error('Error al obtener métricas de evaluación');
        }
        
        const evaluationData = await response.json();
        
        if (!evaluationData.success) {
            throw new Error(evaluationData.message || 'Error en evaluación');
        }
        
        // Combinar datos
        const enrichedData = { ...data };
        
        // Añadir métricas si no existen o están vacías
        if (!enrichedData.metrics || Object.keys(enrichedData.metrics).length === 0) {
            enrichedData.metrics = evaluationData.metrics || {};
        }
        
        // Añadir historia, predicciones y datos de prueba
        enrichedData.history = evaluationData.history || {};
        enrichedData.predictions = evaluationData.predictions || [];
        enrichedData.y_test = evaluationData.y_test || [];
        
        console.log('Datos enriquecidos:', enrichedData);
        return enrichedData;
        
    } catch (error) {
        console.error('Error al enriquecer datos:', error);
        return data; // Devolver datos originales si falla
    }
}

/**
 * Crea un gráfico vacío con un mensaje
 */
function createEmptyChart(canvasId, message) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Sin datos'],
            datasets: [{
                label: message,
                data: [0],
                backgroundColor: 'rgba(200, 200, 200, 0.2)',
                borderColor: 'rgba(200, 200, 200, 1)',
                borderWidth: 1
            }]
        },
        options: {
            plugins: {
                legend: {
                    display: true,
                    position: 'top'
                },
                tooltip: {
                    callbacks: {
                        label: function() {
                            return message;
                        }
                    }
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    ticks: {
                        display: false
                    }
                }
            }
        }
    });
}

// Añadir estilos para la animación de actualización de métricas
(function() {
    const style = document.createElement('style');
    style.textContent = `
        .highlight-update {
            animation: metric-update 1.5s ease;
        }
        @keyframes metric-update {
            0% { background-color: rgba(79, 70, 229, 0); }
            30% { background-color: rgba(79, 70, 229, 0.3); }
            100% { background-color: rgba(79, 70, 229, 0); }
        }
    `;
    document.head.appendChild(style);
})();