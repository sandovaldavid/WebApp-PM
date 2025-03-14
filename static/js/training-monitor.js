/**
 * Monitoring functionality for neural network training process
 */

class TrainingMonitor {
    constructor(trainingId, options = {}) {
        this.trainingId = trainingId;
        this.eventSource = null;
        this.options = {
            progressBarSelector: '#training-progress',
            logContainerSelector: '#training-log',
            currentEpochSelector: '#current-epoch',
            totalEpochsSelector: '#total-epochs',
            remainingTimeSelector: '#remaining-time',
            statusSelector: '#training-status',
            chartSelector: '#training-chart',
            ...options
        };
        
        // Elementos DOM
        this.progressBar = document.querySelector(this.options.progressBarSelector);
        this.logContainer = document.querySelector(this.options.logContainerSelector);
        this.currentEpochElement = document.querySelector(this.options.currentEpochSelector);
        this.totalEpochsElement = document.querySelector(this.options.totalEpochsSelector);
        this.remainingTimeElement = document.querySelector(this.options.remainingTimeSelector);
        this.statusElement = document.querySelector(this.options.statusSelector);
        
        // Para gráficos
        this.chart = null;
        this.chartData = {
            labels: [],
            trainLoss: [],
            valLoss: []
        };
        
        this.lastHeartbeatTime = Date.now();
        this.connectionLost = false;
    }

    start() {
        // Iniciar la conexión SSE
        const url = `/redes-neuronales/monitor-entrenamiento/?training_id=${this.trainingId}`;
        
        console.log(`Iniciando monitoreo de entrenamiento: ${this.trainingId}`);
        
        if (this.eventSource) {
            this.eventSource.close();
        }
        
        this.eventSource = new EventSource(url);
        
        // Configurar manejadores de eventos
        this.eventSource.onopen = (e) => {
            console.log('Conexión SSE establecida');
            this.updateStatus('Conectado - Entrenamiento en curso');
            this.connectionLost = false;
        };
        
        this.eventSource.onerror = (e) => {
            console.error('Error en conexión SSE', e);
            this.updateStatus('Error de conexión - Reintentando...');
            
            // Verificar si la conexión se perdió por mucho tiempo
            const now = Date.now();
            if (now - this.lastHeartbeatTime > 10000 && !this.connectionLost) {
                this.connectionLost = true;
                this.addLogMessage('Error: Se perdió la conexión con el servidor', 'error');
                
                // Reintentar después de un tiempo
                setTimeout(() => {
                    if (this.connectionLost) {
                        this.restart();
                    }
                }, 5000);
            }
        };
        
        // Evento para mensajes normales (logs, errores)
        this.eventSource.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                this.handleUpdate(data);
            } catch (error) {
                console.error('Error al procesar evento:', error, e.data);
            }
        };
        
        // Evento específico para actualizaciones de progreso
        this.eventSource.addEventListener('progress', (e) => {
            try {
                const data = JSON.parse(e.data);
                this.handleProgressUpdate(data);
            } catch (error) {
                console.error('Error al procesar evento de progreso:', error, e.data);
            }
        });
        
        // Evento de finalización
        this.eventSource.addEventListener('complete', (e) => {
            try {
                const data = JSON.parse(e.data);
                this.handleCompletion(data);
            } catch (error) {
                console.error('Error al procesar evento de finalización:', error, e.data);
            }
        });
        
        // Evento de error específico
        this.eventSource.addEventListener('error', (e) => {
            try {
                const data = JSON.parse(e.data);
                this.handleError(data);
            } catch (error) {
                console.error('Error al procesar evento de error:', error, e.data);
            }
        });
        
        // Heartbeat para detectar desconexiones
        this.eventSource.addEventListener('heartbeat', (e) => {
            this.lastHeartbeatTime = Date.now();
            this.connectionLost = false;
        });
        
        // Añadir un evento para manejar el cierre explícito
        this.eventSource.addEventListener('close', (e) => {
            try {
                console.log('Conexión SSE cerrada por el servidor');
                this.stop();
            } catch (error) {
                console.error('Error al procesar evento de cierre:', error);
            }
        });
        
        // Inicializar el gráfico si está disponible
        this.initChart();
    }
    
    restart() {
        console.log('Reiniciando conexión SSE...');
        if (this.eventSource) {
            this.eventSource.close();
        }
        this.start();
    }
    
    stop() {
        if (this.eventSource) {
            this.eventSource.close();
            this.eventSource = null;
            console.log('Monitoreo detenido');
        }
    }
    
    handleUpdate(data) {
        // Procesar diferentes tipos de mensajes
        switch(data.type) {
            case 'log':
                this.addLogMessage(data.message, data.level);
                break;
            case 'error':
                this.handleError(data);
                break;
            case 'batch_progress':
                // Estos son frecuentes, no hacemos nada especial
                break;
            default:
                console.log('Evento no manejado:', data);
        }
    }
    
    handleProgressUpdate(data) {
        // Actualizar barra de progreso
        if (this.progressBar) {
            const percent = data.progress_percent || (data.epoch / data.total_epochs * 100);
            this.progressBar.style.width = `${percent}%`;
            this.progressBar.setAttribute('aria-valuenow', percent);
        }
        
        // Actualizar información de época
        if (this.currentEpochElement) {
            this.currentEpochElement.textContent = data.epoch;
        }
        
        if (this.totalEpochsElement && data.total_epochs) {
            this.totalEpochsElement.textContent = data.total_epochs;
        }
        
        // Actualizar tiempo restante
        if (this.remainingTimeElement && data.remaining_time) {
            this.remainingTimeElement.textContent = data.remaining_time;
        }
        
        // Actualizar gráfico si tenemos datos de pérdida
        if (data.train_loss !== undefined && data.stage === 'epoch_end') {
            this.updateChart(data);
        }
    }
    
    handleCompletion(data) {
        this.addLogMessage('🎉 Entrenamiento completado exitosamente!', 'success');
        this.updateStatus('Completado');
        
        if (this.progressBar) {
            this.progressBar.style.width = '100%';
            this.progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
            this.progressBar.classList.add('bg-success');
        }
        
        // Mostrar métricas finales - mejorar visualización de métricas
        if (data.metrics || data.metrics_summary || (data.result && data.result.metrics)) {
            const metrics = data.metrics || data.metrics_summary || (data.result && data.result.metrics) || {};
            
            // Formatear las métricas principales
            const r2 = metrics.R2 !== undefined ? metrics.R2 : 
                       (metrics.r2 !== undefined ? metrics.r2 : 'N/A');
            const mae = metrics.MAE !== undefined ? metrics.MAE : 
                       (metrics.mae !== undefined ? metrics.mae : 'N/A');
            const accuracy = metrics.Accuracy !== undefined ? metrics.Accuracy : 
                           (metrics.accuracy !== undefined ? metrics.accuracy : 'N/A');
            
            // Añadir una línea de resumen
            this.addLogMessage(`📊 Resumen de métricas:`, 'info');
            this.addLogMessage(`  • R²: ${typeof r2 === 'number' ? r2.toFixed(4) : r2}`, 'info');
            this.addLogMessage(`  • MAE: ${typeof mae === 'number' ? mae.toFixed(2) : mae}`, 'info');
            this.addLogMessage(`  • Accuracy: ${typeof accuracy === 'number' ? (accuracy * 100).toFixed(2) + '%' : accuracy}`, 'info');
        }
        
        // Mostrar mensaje de finalización con instrucciones
        this.addLogMessage('✅ El modelo ha sido guardado y está listo para ser utilizado.', 'success');
        this.addLogMessage('💡 Puede cerrar esta ventana o realizar un nuevo entrenamiento.', 'info');
        
        // Actualizar título o badges si existen
        const badgeElement = document.querySelector('#training-status-badge');
        if (badgeElement) {
            badgeElement.textContent = 'Completado';
            badgeElement.className = 'badge bg-success';
        }
        
        // Activar botones si existen
        const newTrainingBtn = document.querySelector('#new-training-btn');
        if (newTrainingBtn) {
            newTrainingBtn.disabled = false;
        }
        
        // IMPORTANTE: Cerrar la conexión SSE
        this.stop();
        
        // Si hay un callback de finalización, llamarlo
        if (typeof this.options.onComplete === 'function') {
            this.options.onComplete(data);
        }
        
        // Notificar al usuario con una notificación del navegador si está en segundo plano
        if (document.hidden && Notification && Notification.permission === 'granted') {
            new Notification('Entrenamiento completado', {
                body: 'El entrenamiento del modelo ha finalizado exitosamente.',
                icon: '/static/img/favicon.ico'
            });
        }
    }
    
    handleError(data) {
        this.addLogMessage(`Error: ${data.message}`, 'error');
        this.updateStatus('Error');
        
        if (this.progressBar) {
            this.progressBar.classList.remove('bg-info', 'bg-success', 'progress-bar-striped', 'progress-bar-animated');
            this.progressBar.classList.add('bg-danger');
        }
        
        this.stop();
    }
    
    addLogMessage(message, level = 'info') {
        if (!this.logContainer) return;
        
        const logEntry = document.createElement('div');
        logEntry.classList.add('log-entry', `log-${level}`);
        
        // Añadir timestamp
        const timestamp = new Date().toLocaleTimeString();
        logEntry.innerHTML = `<span class="log-time">[${timestamp}]</span> ${message}`;
        
        // Añadir al contenedor y hacer scroll
        this.logContainer.appendChild(logEntry);
        this.logContainer.scrollTop = this.logContainer.scrollHeight;
    }
    
    updateStatus(status) {
        if (this.statusElement) {
            this.statusElement.textContent = status;
        }
    }
    
    initChart() {
        const chartElement = document.querySelector(this.options.chartSelector);
        if (!chartElement || typeof Chart === 'undefined') {
            return;
        }
        
        // Destruir gráfico anterior si existe
        if (this.chart) {
            this.chart.destroy();
        }
        
        const ctx = chartElement.getContext('2d');
        this.chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'Pérdida (Train)',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        tension: 0.1
                    },
                    {
                        label: 'Pérdida (Validación)',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        tension: 0.1
                    }
                ]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: false
                    }
                }
            }
        });
    }
    
    updateChart(data) {
        if (!this.chart) return;
        
        this.chartData.labels.push(data.epoch);
        this.chartData.trainLoss.push(data.train_loss);
        this.chartData.valLoss.push(data.val_loss || null);
        
        // Limitar puntos para evitar problemas de rendimiento
        const maxPoints = 50;
        if (this.chartData.labels.length > maxPoints) {
            const skipFactor = Math.ceil(this.chartData.labels.length / maxPoints);
            
            this.chart.data.labels = this.chartData.labels.filter((_, i) => i % skipFactor === 0);
            this.chart.data.datasets[0].data = this.chartData.trainLoss.filter((_, i) => i % skipFactor === 0);
            this.chart.data.datasets[1].data = this.chartData.valLoss.filter((_, i) => i % skipFactor === 0);
        } else {
            this.chart.data.labels = this.chartData.labels;
            this.chart.data.datasets[0].data = this.chartData.trainLoss;
            this.chart.data.datasets[1].data = this.chartData.valLoss;
        }
        
        this.chart.update();
    }
}

// Exportar para uso global
window.TrainingMonitor = TrainingMonitor;
