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
    
    // Inicializar botón para volver a configuración
    const backToConfigBtn = document.getElementById('backToConfigBtn');
    if (backToConfigBtn) {
        backToConfigBtn.addEventListener('click', function() {
            // Usar true para reiniciar completamente (como una nueva carga de página)
            resetTrainingState(true);
            location.reload();
            //showConfigPanel(true);
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
    
    // Botón para nuevo entrenamiento
    const newTrainingBtn = document.getElementById('newTrainingBtn');
    if (newTrainingBtn) {
        newTrainingBtn.addEventListener('click', function() {
            // Usar true para reiniciar completamente (como una nueva carga de página)
            resetTrainingState(true);
            location.reload();
            //showConfigPanel(true);
        });
    }
}

/**
 * Actualiza el estado de la interfaz según las condiciones actuales
 */
function updateUIState() {

    // Verificar si hay un entrenamiento activo
    const storedTraining = getStoredTrainingState();

    if (!storedTraining) {
        // Si no hay entrenamiento activo, mostrar panel de configuración
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
        
        // Asegurar que el panel de configuración esté visible
        //showConfigPanel();        
    } else {
        console.log("Recuperando entrenamiento almacenado:", storedTraining);
        
        // Verificar si el entrenamiento sigue activo en el servidor antes de restaurarlo
        fetch(URLS.checkActiveTraining)
            .then(response => response.json())
            .then(data => {
                const serverTrainings = data.success ? data.active_trainings : [];
                const trainingStillActive = serverTrainings.some(
                    t => t.training_id === storedTraining.trainingId
                );
                
                if (trainingStillActive) {
                    // El entrenamiento sigue activo, restaurar interfaz
                    setupTrainingInterface(storedTraining.trainingId, storedTraining.modelName);
                    showNotification('Entrenamiento en curso restaurado', 'info');
                } else {
                    // El entrenamiento ya no está activo, mostrar panel de configuración
                    clearTrainingState();
                    showConfigPanel();
                }
            })
            .catch(error => {
                // En caso de error, mostrar el panel de configuración
                console.error("Error al verificar entrenamientos:", error);
                showConfigPanel();
            });
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
    
    // Obtener los datos del formulario
    const form = document.getElementById('trainingForm');
    const formData = new FormData(form);
    console.log('Datos del formulario:', formData);
    
    // Deshabilitar botón de inicio
    const startTrainingBtn = document.getElementById('startTrainingBtn');
    if (startTrainingBtn) {
        startTrainingBtn.disabled = true;
        startTrainingBtn.classList.add('opacity-50', 'cursor-not-allowed');
        startTrainingBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Iniciando...';
    }
    
    // Ocultar panel de configuración y mostrar resultados
    hideConfigPanel();
    
    // Mostrar sección de resultados
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults) {
        trainingResults.classList.remove('hidden');
        // Añadir animación de entrada
        trainingResults.classList.add('animate-fadeIn');
        setTimeout(() => trainingResults.classList.remove('animate-fadeIn'), 500);
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
            saveTrainingState(data.training_id, data.model_name);
            
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

    // Guardar ID de entrenamiento actual
    currentTrainingId = trainingId;
    
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
    

    // Mostrar nombre del modelo
    document.getElementById('savedModelName').textContent = data.model_name;

    // Mostrar métricas finales
    const finalMetrics = document.getElementById('finalMetrics');
    if (finalMetrics) {
        finalMetrics.classList.remove('hidden');
    }
    
    // Mostrar botón para volver a la configuración
    showBackToConfigButton();
    
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
        loadLatestMetrics();
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

    if (data.save_as_main) {

        // Limpiar estado de entrenamiento activo
        clearTrainingState();

        // Mostrar notificación sobre la opción de recargar
        showNotification(
            'Entrenamiento completado. Para usar el nuevo modelo inmediatamente sin reiniciar, haz click en "Recargar modelo sin reiniciar"', 
            'info', 
            10000  // 10 segundos
        );
        
        // Resaltar el botón de recarga
        const reloadBtn = document.getElementById('reload-model-btn');
        if (reloadBtn) {
            reloadBtn.classList.add('animate-pulse', 'bg-green-100', 'border-green-400');
            setTimeout(() => {
                reloadBtn.classList.remove('animate-pulse', 'bg-green-100', 'border-green-400');
            }, 5000);
        }
    }
    
    setTimeout(() => {
        requestModelEvaluation(currentTrainingId);
    }, 1000);
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
    
    // Mostrar botón para volver a la configuración
    showBackToConfigButton();
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
 * Inicializa los gráficos de pérdida mejorados
 */
function initializeCharts(history) {
    // Calcular estadísticas
    const lastTrainLoss = history.loss[history.loss.length - 1];
    const lastValLoss = history.val_loss[history.val_loss.length - 1];
    
    // Actualizar resumen de estadísticas
    document.getElementById('finalTrainLoss').textContent = lastTrainLoss.toFixed(4);
    document.getElementById('finalValLoss').textContent = lastValLoss.toFixed(4);
    
    // Gráfico de pérdida con diseño mejorado
    const lossCtx = document.getElementById('lossChart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: Array.from({ length: history.loss.length }, (_, i) => i + 1),
            datasets: [{
                label: 'Entrenamiento',
                data: history.loss,
                borderColor: 'rgba(79, 70, 229, 1)',
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderWidth: 2,
                tension: 0.2,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: 'rgba(79, 70, 229, 1)',
            }, {
                label: 'Validación',
                data: history.val_loss,
                borderColor: 'rgba(236, 72, 153, 1)',
                backgroundColor: 'rgba(236, 72, 153, 0.1)',
                borderWidth: 2,
                tension: 0.2,
                fill: true,
                pointRadius: 0,
                pointHoverRadius: 5,
                pointHoverBackgroundColor: 'rgba(236, 72, 153, 1)',
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#6B7280',
                    bodyColor: '#111827',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 5,
                    usePointStyle: true,
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y.toFixed(6)}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Época',
                        color: '#6B7280',
                        font: {
                            weight: 'bold',
                            size: 12
                        }
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    type: 'linear',
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Pérdida',
                        color: '#6B7280',
                        font: {
                            weight: 'bold',
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(243, 244, 246, 1)'
                    }
                }
            }
        }
    });
}

/**
 * Inicializa el gráfico de predicciones vs valores reales mejorado
 */
function initializePredictionsChart(predictions, yTest) {
    // Calcular estadísticas
    const correlation = calculateCorrelation(predictions, yTest);
    document.getElementById('predictionCorrelation').textContent = correlation.toFixed(2);
    
    // Calcular precisión personalizada (usando R2)
    const accuracy = calculateR2Score(predictions, yTest);
    document.getElementById('predictionAccuracy').textContent = accuracy.toFixed(2);
    
    const predictionsCtx = document.getElementById('predictionsChart').getContext('2d');
    predictionsChart = new Chart(predictionsCtx, {
        type: 'scatter',
        data: {
            datasets: [{
                label: 'Predicciones',
                data: yTest.map((real, i) => ({
                    x: real,
                    y: predictions[i]
                })),
                backgroundColor: 'rgba(59, 130, 246, 0.7)',
                borderColor: 'rgba(59, 130, 246, 1)',
                borderWidth: 1,
                pointRadius: 5,
                pointHoverRadius: 7,
                pointStyle: 'circle'
            },
            {
                // Línea ideal (y=x)
                label: 'Línea ideal',
                data: (() => {
                    const min = Math.min(...yTest);
                    const max = Math.max(...yTest);
                    return [{ x: min, y: min }, { x: max, y: max }];
                })(),
                type: 'line',
                backgroundColor: 'transparent',
                borderColor: 'rgba(156, 163, 175, 0.8)',
                borderWidth: 2,
                borderDash: [5, 5],
                pointRadius: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10,
                        padding: 20
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(255, 255, 255, 0.9)',
                    titleColor: '#6B7280',
                    bodyColor: '#111827',
                    borderColor: '#E5E7EB',
                    borderWidth: 1,
                    padding: 10,
                    boxPadding: 5,
                    callbacks: {
                        label: function(context) {
                            return `Real: ${context.parsed.x.toFixed(2)}, Predicho: ${context.parsed.y.toFixed(2)}`;
                        },
                        afterLabel: function(context) {
                            const error = context.parsed.y - context.parsed.x;
                            return `Error: ${error.toFixed(2)} (${(error*100/context.parsed.x).toFixed(1)}%)`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Valores reales',
                        color: '#6B7280',
                        font: {
                            weight: 'bold',
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(243, 244, 246, 0.8)'
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Predicciones',
                        color: '#6B7280',
                        font: {
                            weight: 'bold',
                            size: 12
                        }
                    },
                    grid: {
                        color: 'rgba(243, 244, 246, 0.8)'
                    }
                }
            }
        }
    });
}

/**
 * Calcula el coeficiente de correlación de Pearson
 */
function calculateCorrelation(x, y) {
    const xMean = x.reduce((a, b) => a + b, 0) / x.length;
    const yMean = y.reduce((a, b) => a + b, 0) / y.length;
    
    const numerator = x.map((xi, i) => (xi - xMean) * (y[i] - yMean))
                       .reduce((a, b) => a + b, 0);
    
    const xDev = Math.sqrt(x.map(xi => Math.pow(xi - xMean, 2))
                            .reduce((a, b) => a + b, 0));
    const yDev = Math.sqrt(y.map(yi => Math.pow(yi - yMean, 2))
                            .reduce((a, b) => a + b, 0));
    
    return numerator / (xDev * yDev);
}

/**
 * Calcula el R² score (coeficiente de determinación)
 */
function calculateR2Score(pred, actual) {
    const mean = actual.reduce((a, b) => a + b, 0) / actual.length;
    
    const totalSS = actual.map(y => Math.pow(y - mean, 2))
                         .reduce((a, b) => a + b, 0);
    
    const residualSS = actual.map((y, i) => Math.pow(y - pred[i], 2))
                            .reduce((a, b) => a + b, 0);
    
    return 1 - (residualSS / totalSS);
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

    // NUEVO: Actualizar valores en las tarjetas principales
    if (data.metrics) {
        // Error Medio (MAE)
        updateEvaluationMetric('metricMAEDisplay', data.metrics.MAE);
        
        // Precisión R²
        updateEvaluationMetric('metricR2Display', data.metrics.R2);
        
        // RMSE
        updateEvaluationMetric('metricRMSEDisplay', data.metrics.RMSE);
        
        // Precisión Global
        updateEvaluationMetric('metricGlobalDisplay', data.global_precision, true);
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

    // NUEVO: Mostrar imagen de métricas por segmentos
    if (data.segmented_metrics_image) {
        const segmentedMetricsImg = document.getElementById('segmentedMetricsImg');
        if (segmentedMetricsImg) {
            segmentedMetricsImg.src = data.segmented_metrics_image + '?t=' + new Date().getTime();
        }
    }
    
    // Mostrar botón para volver a configuración de forma prominente
    showBackToConfigButton();
}

/**
 * Actualiza un valor de métrica en la interfaz con formato apropiado
 * @param {string} elementId - ID del elemento a actualizar
 * @param {number} value - Valor de la métrica
 * @param {boolean} isPercentage - Si el valor debe mostrarse como porcentaje
 */
function updateEvaluationMetric(elementId, value, isPercentage = false) {
    const element = document.getElementById(elementId);
    if (!element) return;
    
    if (value !== undefined && value !== null) {
        if (isPercentage) {
            // Convertir a porcentaje y mostrar con 1 decimal
            element.textContent = (value * 100).toFixed(1);
        } else {
            // Mostrar con 2 decimales para métricas normales
            element.textContent = typeof value === 'number' ? value.toFixed(2) : value;
        }
    } else {
        element.textContent = "N/D";
    }
    
    // Añadir efecto de actualización
    element.classList.add('pulse-update');
    setTimeout(() => {
        element.classList.remove('pulse-update');
    }, 1500);
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
 * Función para cargar las métricas más recientes cuando sea necesario
 */
function loadLatestMetrics() {
    fetch('/redes-neuronales/model-status/')
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success' && data.metrics) {
                // Actualizar métricas en la interfaz
                const metrics = data.metrics;
                
                document.getElementById('metricMSE').textContent = metrics.MSE ? metrics.MSE.toFixed(2) : '--';
                document.getElementById('metricMAE').textContent = metrics.MAE ? metrics.MAE.toFixed(2) : '--';
                document.getElementById('metricRMSE').textContent = metrics.RMSE ? metrics.RMSE.toFixed(2) : '--';
                document.getElementById('metricR2').textContent = metrics.R2 ? metrics.R2.toFixed(4) : '--';
                
                // Si el modelo es principal, mostrar indicación
                document.getElementById('setAsMainModel').classList.remove('hidden');
                
                console.log("✓ Métricas actualizadas manualmente");
            }
        })
        .catch(error => console.error('Error al cargar métricas:', error));
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

/**
 * Muestra el panel de configuración y oculta los resultados y evaluación
 * @param {boolean} resetTraining - Si es true, reinicia el estado como si fuera una nueva carga de página
 * DEJADA FUERA DE FUNCIONAMIENTO POR PROBLEMAS DE VISUALIZACIÓN
 */
function showConfigPanel(resetTraining = false) {
    // Mostrar panel de configuración
    const configPanel = document.getElementById('configurationPanel');
    if (configPanel) {
        configPanel.classList.remove('hidden');
        configPanel.classList.add('animate-fadeIn');
        setTimeout(() => configPanel.classList.remove('animate-fadeIn'), 500);
    }
    
    // Ocultar botón de volver
    const backToConfigBtn = document.getElementById('backToConfigBtn');
    if (backToConfigBtn) {
        backToConfigBtn.classList.add('hidden');
    }
    
    // Ocultar COMPLETAMENTE los resultados del entrenamiento (no solo minimizar)
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults) {
        trainingResults.classList.add('hidden');
        trainingResults.classList.remove('opacity-60', 'scale-95');
    }
    
    // Ocultar la sección de evaluación del modelo
    const evaluationSection = document.getElementById('evaluationSection');
    if (evaluationSection) {
        evaluationSection.classList.add('hidden');
    }
    
    // Si resetTraining es true, reiniciar el estado como si fuera una nueva carga
    if (resetTraining) {
        // Reiniciar el estado del entrenamiento
        if (trainingMonitor) {
            trainingMonitor.stop();
            trainingMonitor = null;
        }
        
        // Limpiar ID de entrenamiento actual
        currentTrainingId = null;
        
        // Reiniciar el estado de las gráficas
        chartsInitialized = false;
        lossChart = null;
        predictionsChart = null;
        
        // Reiniciar el formulario de entrenamiento
        const trainingForm = document.getElementById('trainingForm');
        if (trainingForm) {
            trainingForm.reset();
            
            // SOLUCIÓN: Limpiar explícitamente el campo de archivo CSV
            const csvFileInput = document.getElementById('csv_file');
            if (csvFileInput) {
                // Crear un nuevo elemento input file que reemplace al actual
                const newFileInput = document.createElement('input');
                newFileInput.type = 'file';
                newFileInput.id = csvFileInput.id;
                newFileInput.name = csvFileInput.name;
                newFileInput.className = csvFileInput.className;
                newFileInput.accept = csvFileInput.accept || '.csv';
                
                // Reemplazar el elemento actual con el nuevo
                csvFileInput.parentNode.replaceChild(newFileInput, csvFileInput);
            }
        }
        
        // Limpiar el registro de entrenamiento
        const trainingLog = document.getElementById('trainingLog');
        if (trainingLog) {
            trainingLog.innerHTML = '<p class="log-line">Listo para iniciar un nuevo entrenamiento.</p>';
        }
        
        // Ocultar métricas finales si están visibles
        const finalMetrics = document.getElementById('finalMetrics');
        if (finalMetrics) {
            finalMetrics.classList.add('hidden');
        }
        
        // Reiniciar las métricas a valores vacíos
        const metricElements = ['metricMSE', 'metricMAE', 'metricRMSE', 'metricR2'];
        metricElements.forEach(id => {
            const element = document.getElementById(id);
            if (element) element.textContent = '--';
        });
        
        // Reiniciar el estado de indicadores de progreso
        updateTrainingStatus("Esperando inicio de entrenamiento", 0);
        
        // SOLUCIÓN: Reiniciar el spinner de entrenamiento
        const trainingSpinner = document.getElementById('trainingSpinner');
        if (trainingSpinner) {
            // Asegurar que el elemento se muestre correctamente
            trainingSpinner.classList.remove('hidden');
            trainingSpinner.classList.add('pulse-ring');
        }
        
        // Reiniciar los estados de los indicadores
        const sseStatusDot = document.getElementById('sseStatusDot');
        const sseStatusText = document.getElementById('sseStatusText');
        if (sseStatusDot && sseStatusText) {
            // Limpiar todas las clases posibles y reiniciar
            sseStatusDot.className = "w-2 h-2 rounded-full bg-gray-500 inline-block mr-2";
            sseStatusText.textContent = "Sin conexión";
        }
        
        console.log('Estado del entrenamiento reiniciado completamente');
    }
    
    // Scroll hacia arriba para mostrar el panel de configuración
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

/**
 * Reinicia el estado del entrenamiento y muestra el panel de configuración
 * @param {*} resetTraining 
 */

function resetTrainingState(resetTraining= false) {
    if (resetTraining) {
        // Reiniciar el estado del entrenamiento
        if (trainingMonitor) {
            trainingMonitor.stop();
            trainingMonitor = null;
        }
        
        // Limpiar ID de entrenamiento actual
        currentTrainingId = null;
        
        // Reiniciar el estado de las gráficas
        chartsInitialized = false;
        lossChart = null;
        predictionsChart = null;

    }
}

/**
 * Oculta el panel de configuración y muestra los resultados
 */
function hideConfigPanel() {
    // Ocultar panel de configuración
    const configPanel = document.getElementById('configurationPanel');
    if (configPanel) {
        configPanel.classList.add('hidden');
    }
    
    // Mostrar resultados con normalidad
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults) {
        trainingResults.classList.remove('hidden', 'opacity-60', 'scale-95');
    }
}

/**
 * Muestra el botón para volver al panel de configuración
 */
function showBackToConfigButton() {
    const backToConfigBtn = document.getElementById('backToConfigBtn');
    if (backToConfigBtn) {
        backToConfigBtn.classList.remove('hidden');
        backToConfigBtn.classList.add('animate-fadeIn');
        setTimeout(() => backToConfigBtn.classList.remove('animate-fadeIn'), 500);
    }
}


/**
 * Solicita la generación de un informe de evaluación del modelo
 */
function generateModelReport() {
    // Verificar que tenemos un ID de modelo válido
    if (!currentTrainingId) {
        alert('No hay un modelo evaluado para generar el informe.');
        return;
    }
    
    // Referencia al botón
    const reportBtn = document.getElementById('generateReportBtn');
    const originalContent = reportBtn.innerHTML;
    
    // Cambiar el botón a estado de carga
    reportBtn.disabled = true;
    reportBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Generando...';
    
    // Mostrar notificación de proceso iniciado
    showNotification('Generando informe de evaluación...', 'info');
    
    // Enviar solicitud al servidor
    fetch(`${URLS.generarInforme}`, {
        method: 'POST',
        headers: {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({ 
            model_id: currentTrainingId,
            include_charts: true,
            include_metrics: true,
            include_feature_importance: true
        })
    })
    .then(response => {
        // Si es un PDF o blob, manejarlo diferente
        if (response.headers.get('Content-Type') === 'application/pdf') {
            return response.blob().then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `evaluacion_modelo_${currentTrainingId.substring(0, 8)}.pdf`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
                return { success: true, message: 'Informe descargado correctamente' };
            });
        }
        
        return response.json();
    })
    .then(data => {
        if (data.success) {
            showNotification('Informe generado correctamente', 'success');
        } else {
            showNotification(`Error: ${data.message}`, 'error');
        }
    })
    .catch(error => {
        console.error('Error al generar informe:', error);
        showNotification('Error al generar informe', 'error');
    })
    .finally(() => {
        // Restaurar el botón a su estado original
        reportBtn.disabled = false;
        reportBtn.innerHTML = originalContent;
    });
}

/**
 * Muestra una notificación temporal
 * @param {string} message - Mensaje a mostrar
 * @param {string} type - Tipo de notificación: 'success', 'error', 'info', 'warning'
 */
function showNotification(message, type = 'info') {
    // Crear elemento de notificación
    const notification = document.createElement('div');
    
    // Configurar clases según el tipo
    const baseClasses = 'fixed bottom-4 right-4 px-6 py-3 rounded-lg shadow-lg z-50 transition-all duration-500 transform translate-y-0 opacity-100';
    let typeClasses = '';
    let icon = '';
    
    switch(type) {
        case 'success':
            typeClasses = 'bg-green-50 text-green-800 border border-green-200';
            icon = '<i class="fas fa-check-circle text-green-500 mr-2"></i>';
            break;
        case 'error':
            typeClasses = 'bg-red-50 text-red-800 border border-red-200';
            icon = '<i class="fas fa-exclamation-circle text-red-500 mr-2"></i>';
            break;
        case 'warning':
            typeClasses = 'bg-yellow-50 text-yellow-800 border border-yellow-200';
            icon = '<i class="fas fa-exclamation-triangle text-yellow-500 mr-2"></i>';
            break;
        default: // info
            typeClasses = 'bg-blue-50 text-blue-800 border border-blue-200';
            icon = '<i class="fas fa-info-circle text-blue-500 mr-2"></i>';
    }
    
    notification.className = `${baseClasses} ${typeClasses}`;
    notification.innerHTML = `<div class="flex items-center">${icon}<span>${message}</span></div>`;
    
    // Añadir a DOM
    document.body.appendChild(notification);
    
    // Animar entrada
    setTimeout(() => {
        notification.style.transform = 'translateY(0)';
        notification.style.opacity = '1';
    }, 10);
    
    // Animar salida y eliminar
    setTimeout(() => {
        notification.style.transform = 'translateY(20px)';
        notification.style.opacity = '0';
        setTimeout(() => notification.remove(), 500);
    }, 4000);
}


function mostrarResultadosImportancia(data) {
    // Mostrar gráfico de importancia
    document.getElementById('featureImportanceImg').src = '/static/media/evaluacion/' + data.model_id + '/global_feature_importance.png';
    
    // Mostrar también métricas por característica
    document.getElementById('metricsImportanceImg').src = '/static/media/evaluacion/' + data.model_id + '/feature_importance_metrics.png';
    
    // Mostrar interacciones si están disponibles
    if (data.has_interactions) {
        document.getElementById('interactionsImg').src = '/static/media/evaluacion/' + data.model_id + '/feature_interactions.png';
        document.getElementById('interactions-section').classList.remove('hidden');
    }
}

// Funciones para almacenamiento del estado de entrenamiento
function saveTrainingState(trainingId, modelName) {
    localStorage.setItem('activeTrainingId', trainingId);
    localStorage.setItem('activeModelName', modelName);
    localStorage.setItem('trainingTimestamp', Date.now());
}

function clearTrainingState() {
    localStorage.removeItem('activeTrainingId');
    localStorage.removeItem('activeModelName');
    localStorage.removeItem('trainingTimestamp');
}

function getStoredTrainingState() {
    const trainingId = localStorage.getItem('activeTrainingId');
    const modelName = localStorage.getItem('activeModelName');
    const timestamp = localStorage.getItem('trainingTimestamp');
    
    if (trainingId && modelName) {
        return {
            trainingId,
            modelName,
            timestamp
        };
    }
    
    return null;
}

// Agregar cerca de los otros event listeners, al final del DOMContentLoaded
document.getElementById('open-tensorboard').addEventListener('click', function() {
    const modelId = currentTrainingId || lastTrainingId;
    
    // Mostrar indicador de carga
    this.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Iniciando...';
    this.disabled = true;
    
    // Llamar al endpoint para iniciar/abrir TensorBoard
    fetch(URLS.openTensorBoard + '?model_id=' + modelId)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.url) {
                // Abrir TensorBoard en una nueva pestaña
                window.open(data.url, '_blank');
            } else {
                // Mostrar error si hay problemas
                showNotification(data.message || 'Error al iniciar TensorBoard', 'error');
            }
        })
        .catch(err => {
            showNotification('Error de conexión: ' + err.message, 'error');
        })
        .finally(() => {
            // Restaurar el botón
            this.innerHTML = '<i class="fas fa-chart-line mr-2"></i>Abrir TensorBoard';
            this.disabled = false;
        });
});

// Añadir estilos para las animaciones
(function() {
    const style = document.createElement('style');
    style.textContent = `
        .animate-fadeIn {
            animation: fadeIn 0.5s ease-in-out;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .scale-95 {
            transform: scale(0.95);
        }
    `;
    document.head.appendChild(style);
})();

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