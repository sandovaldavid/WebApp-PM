
// Función para cargar las métricas más recientes cuando sea necesario
// Esta función no se llamará automáticamente, solo cuando sea necesario
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
                
                // Mostrar nombre del modelo
                document.getElementById('savedModelName').textContent = 'tiempo_estimator';
                
                // Si el modelo es principal, mostrar indicación
                document.getElementById('setAsMainModel').classList.remove('hidden');
                
                console.log("✓ Métricas actualizadas manualmente");
            }
        })
        .catch(error => console.error('Error al cargar métricas:', error));
}

// ELIMINAR CÓDIGO AUTOMÁTICO
// Se eliminan:
// 1. La función forceShowMetrics
// 2. El MutationObserver que detectaba logs y llamaba a forceShowMetrics
// 3. El temporizador que verificaba cada 15 segundos

// Sobrescribir la función handleTrainingComplete de window
// Solo para asegurar compatibilidad con training-monitor.js
window.handleTrainingComplete = function(data) {
    console.log("Entrenamiento completado, mostrando métricas finales:", data);
    
    // Mostrar sección de métricas finales
    const finalMetrics = document.getElementById('finalMetrics');
    if (finalMetrics) {
        finalMetrics.classList.remove('hidden');
        
        // Si hay métricas en los datos, actualizarlas
        if (data && data.metrics) {
            const metrics = data.metrics;
            
            if (metrics.mse) document.getElementById('metricMSE').textContent = metrics.mse.toFixed(4);
            if (metrics.mae) document.getElementById('metricMAE').textContent = metrics.mae.toFixed(4);
            if (metrics.rmse) document.getElementById('metricRMSE').textContent = metrics.rmse.toFixed(4);
            if (metrics.r2) document.getElementById('metricR2').textContent = metrics.r2.toFixed(4);
            
            // Solo si no hay métricas en los datos, intentar cargarlas del servidor
            if (!metrics.mse && !metrics.mae) {
                loadLatestMetrics();
            }
        } else {
            // Si no hay datos de métricas, cargar del servidor
            loadLatestMetrics();
        }
    }
    
    // Actualizar estado visual
    const spinnerElement = document.getElementById('trainingSpinner');
    if (spinnerElement) {
        spinnerElement.classList.remove('spinner');
        spinnerElement.innerHTML = `
            <svg class="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
            </svg>
        `;
    }
    
    // Mostrar mensaje de éxito si no existe
    const trainingResults = document.getElementById('trainingResults');
    if (trainingResults && !document.querySelector('.bg-green-50')) {
        const successMessage = document.createElement('div');
        successMessage.className = 'mt-4 p-3 bg-green-50 border border-green-200 rounded-md text-green-800';
        successMessage.innerHTML = `
            <div class="flex items-center">
                <svg class="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
                <span class="font-medium">¡Entrenamiento completado con éxito!</span>
            </div>
        `;
        finalMetrics.parentNode.insertBefore(successMessage, finalMetrics);
    }
    
    // Solicitar evaluación automática después de un breve retraso
    setTimeout(() => {
        const modelId = data?.model_id || (window.trainingMonitor?.trainingId) || null;
        if (modelId && typeof requestModelEvaluation === 'function') {
            console.log("Iniciando evaluación automática con ID:", modelId);
            requestModelEvaluation(modelId);
        }
    }, 3000);
};