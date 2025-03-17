/**
 * TrainingMonitor - Clase para manejar el monitoreo en tiempo real del entrenamiento de redes neuronales
 */
class TrainingMonitor {
    /**
     * Inicializa el monitor de entrenamiento
     * @param {string} trainingId - ID del proceso de entrenamiento
     * @param {Object} options - Opciones de configuración
     */
    constructor(trainingId, options = {}) {
        this.trainingId = trainingId;
        this.source = null;
        this.isComplete = false;
        this.connectionAttempts = 0;
        this.maxConnectionAttempts = 3;
        
        // Elementos DOM
        this.elements = {
            trainingLog: document.querySelector(options.logContainerSelector || '#trainingLog'),
            trainingProgress: document.querySelector(options.progressBarSelector || '#trainingProgress'),
            trainingStatus: document.querySelector(options.statusSelector || '#trainingStatus'),
            currentEpoch: document.querySelector(options.currentEpochSelector || '#currentEpoch'),
            remainingTime: document.querySelector(options.remainingTimeSelector || '#remainingTime'),
            trainLoss: document.querySelector(options.trainLossSelector || '#trainLoss'),
            valLoss: document.querySelector(options.valLossSelector || '#valLoss')
        };
        
        // Verificar si todos los elementos existen
        for (const [key, element] of Object.entries(this.elements)) {
            if (!element) {
                console.warn(`Elemento DOM '${key}' no encontrado`);
            }
        }
        
        // Callbacks
        this.callbacks = {
            onComplete: options.onComplete || null,
            onError: options.onError || null,
            onProgress: options.onProgress || null,
        };

        // Inicializar conjunto de épocas procesadas
        this._epochsProcessed = new Set();
        
        // Añadir contador para verificación de épocas faltantes
        this._lastEpochReceived = 0;
        this._checkMissingEpochsTimer = null;
        
        console.log("TrainingMonitor inicializado con ID:", trainingId);
    }
    
    /**
     * Inicia el monitoreo del entrenamiento
     */
    start() {
        // Cerrar cualquier conexión previa
        if (this.source) {
            this.source.close();
        }
        
        // URL base para el monitoreo
        let baseUrl = '/redes-neuronales/monitor-entrenamiento/';
        
        // Crear nueva conexión EventSource
        try {
            console.log("Iniciando conexión SSE:", `${baseUrl}?training_id=${this.trainingId}`);
            this.source = new EventSource(`${baseUrl}?training_id=${this.trainingId}`);
            
            // Añadir mensaje inicial
            this.addLogEntry("Conexión establecida con el servidor. Iniciando entrenamiento...", "info");
            
            // Configurar manejadores de eventos
            this._setupEventHandlers();
            
        } catch (e) {
            console.error("Error al iniciar conexión SSE:", e);
            this.addLogEntry(`Error al conectar con el servidor: ${e.message}`, "error");
            
            if (this.callbacks.onError) {
                this.callbacks.onError({message: `Error de conexión: ${e.message}`});
            }
        }
    }
    
    /**
     * Detiene el monitoreo del entrenamiento
     */
    stop() {
        if (this.source) {
            this.source.close();
            this.source = null;
            console.log("Conexión SSE cerrada");
        }
    }
    
    /**
     * Intenta reconectar si la conexión se pierde
     * @private
     */
    _reconnect() {
        if (this.connectionAttempts >= this.maxConnectionAttempts) {
            this.addLogEntry("No se pudo establecer conexión con el servidor. Por favor, recargue la página.", "error");
            return;
        }
        
        this.connectionAttempts++;
        this.addLogEntry(`Intentando reconectar (intento ${this.connectionAttempts})...`, "warning");
        
        setTimeout(() => {
            this.start();
        }, 1000 * this.connectionAttempts); // Esperar más tiempo en cada intento
    }

    /**
     * Configura los manejadores de eventos para EventSource
     * @private
     */
    _setupEventHandlers() {
        // Manejar conexión abierta
        this.source.onopen = () => {
            console.log("Conexión SSE abierta");
            this.connectionAttempts = 0;
            this.addLogEntry("Conexión establecida con el servidor", "success");
            
            // Actualizar indicador visual
            const statusDot = document.getElementById('sseStatusDot');
            const statusText = document.getElementById('sseStatusText');
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-green-500 inline-block mr-2";
            if (statusText) statusText.textContent = "Conexión SSE activa";
        };

        // Manejar eventos de error con mejor recuperación
        this.source.onerror = (event) => {
            console.error("Error en la conexión SSE:", event);
            
            // Actualizar indicador visual
            const statusDot = document.getElementById('sseStatusDot');
            const statusText = document.getElementById('sseStatusText');
            if (statusDot) statusDot.className = "w-2 h-2 rounded-full bg-red-500 inline-block mr-2";
            if (statusText) statusText.textContent = "Conexión interrumpida";
            
            // Intentar reconectar automáticamente si no hay demasiados intentos
            if (!this.isComplete && this.connectionAttempts < this.maxConnectionAttempts) {
                this.connectionAttempts++;
                const delay = Math.min(1000 * this.connectionAttempts, 5000);
                console.log(`Reintentando conexión en ${delay/1000} segundos (intento ${this.connectionAttempts})`);
                
                this.addLogEntry(`Conexión interrumpida. Reintentando en ${delay/1000} segundos...`, "warning");
                
                setTimeout(() => {
                    if (this.source) {
                        this.source.close();
                    }
                    this.start();
                }, delay);
            } else if (!this.isComplete && this.connectionAttempts >= this.maxConnectionAttempts) {
                this.addLogEntry("No se pudo restablecer la conexión.", "error");
            }
        };

        // MEJORA: Manejador unificado para eventos "log" con mejor detección
        this.source.addEventListener('log', (event) => {
            try {
                // Debug más detallado para ayudar a identificar problemas
                console.log("%cEvento LOG recibido:", "background:#333; color:yellow; padding:3px 5px;", event.data);
                
                const data = JSON.parse(event.data);
                
                // MEJORA: Sistema mejorado de detección de logs de época
                // 1. Detectar por flags explícitos
                let isEpochLog = Boolean(data.is_epoch_log) || Boolean(data.is_real_epoch);
                
                // 2. Detectar por contenido del mensaje si no tiene flags
                if (!isEpochLog && data.message && typeof data.message === 'string') {
                    // Patrón mejorado para detectar épocas en diferentes formatos
                    const epochPattern = /Época \d+\/\d+|Epoch \d+\/\d+|\[EPOCH LOG\]|>>> ÉPOCA/i;
                    
                    if (epochPattern.test(data.message)) {
                        console.log("%c¡PATRÓN DE ÉPOCA DETECTADO EN MENSAJE!", "background:red; color:white; padding:3px 5px; font-weight:bold;", data.message);
                        isEpochLog = true;
                        
                        // Actualizar flags si faltan
                        data.is_epoch_log = true;
                        data.is_real_epoch = true;
                        
                        // Extraer número de época si falta
                        if (!data.epoch_number) {
                            const epochMatch = data.message.match(/(?:Época|Epoch) (\d+)\/(\d+)/);
                            if (epochMatch && epochMatch.length >= 3) {
                                data.epoch_number = parseInt(epochMatch[1]);
                                data.total_epochs = parseInt(epochMatch[2]);
                                console.log(`Extraídos epoch_number=${data.epoch_number}, total_epochs=${data.total_epochs}`);
                            }
                        }
                    }
                }
                
                // MEJORA: También verificar atributo from_specialized_cache que agregamos en backend
                if (data.from_specialized_cache) {
                    console.log("%c¡DATOS DE CACHÉ ESPECIALIZADA ENCONTRADOS!", "background:blue; color:white; padding:3px 5px; font-weight:bold;");
                    isEpochLog = true;
                }
                
                // MEJORA: Procesar según tipo con logs detallados para diagnóstico
                if (isEpochLog) {
                    console.log("%c¡LOG DE ÉPOCA DETECTADO! Procesando...", "background:green; color:white; font-size:14px; padding:5px; font-weight:bold;");
                    
                    // Extraer números de época
                    const epochNum = data.epoch_number || data.epoch || 0;
                    const totalEpochs = data.total_epochs || 100;
                    
                    // MEJORA DE CONSISTENCIA: Usar mismo criterio para duplicados que en 'epoch'
                    // Si la época ya está procesada y no viene de una fuente especializada, omitirla
                    if (this._epochsProcessed.has(epochNum) && !data.from_specialized_cache) {
                        // Aún actualizar indicadores básicos
                        if (this.elements.currentEpoch) {
                            this.elements.currentEpoch.textContent = `${epochNum}/${totalEpochs}`;
                            this._animateElement(this.elements.currentEpoch);
                        }
                        const progress = (epochNum / totalEpochs) * 100;
                        this.updateTrainingStatus(`Entrenando [Época ${epochNum}/${totalEpochs}]`, progress);
                        
                        console.log(`Log de época ${epochNum} ya procesado, actualizando solo indicadores`);
                        return; // Evitar agregar duplicados al log
                    }
                    
                    // Si llegamos aquí, procesar el log normalmente
                    // Registrar como procesada
                    this._epochsProcessed.add(epochNum);
                    console.log(`Época ${epochNum} añadida al conjunto de procesadas`);
                    
                    // Añadir a la interfaz con formato especial
                    this.addEpochLogEntry(data.message, data.level || 'info', data);
                    
                    // Actualizar indicadores de progreso
                    if (epochNum && totalEpochs) {
                        // Actualizar contador de época con animación
                        if (this.elements.currentEpoch) {
                            this.elements.currentEpoch.textContent = `${epochNum}/${totalEpochs}`;
                            this._animateElement(this.elements.currentEpoch);
                        }
                        
                        // Actualizar barra de progreso
                        const progress = (epochNum / totalEpochs) * 100;
                        this.updateTrainingStatus(`Entrenando [Época ${epochNum}/${totalEpochs}]`, progress);
                        
                        // MEJORA: También actualizar loss si viene en el mensaje
                        const lossMatch = data.message.match(/loss: ([\d\.]+)/);
                        const valLossMatch = data.message.match(/val_loss: ([\d\.]+)/);
                        
                        if (lossMatch && this.elements.trainLoss) {
                            const loss = parseFloat(lossMatch[1]);
                            this.elements.trainLoss.textContent = loss.toFixed(4);
                            this._animateElement(this.elements.trainLoss);
                        }
                        
                        if (valLossMatch && this.elements.valLoss) {
                            const valLoss = parseFloat(valLossMatch[1]);
                            this.elements.valLoss.textContent = valLoss.toFixed(4);
                            this._animateElement(this.elements.valLoss);
                        }
                    }
                } else {
                    // Logs normales (no de época)
                    // Ignorar mensajes de debug
                    if (data.message && typeof data.message === 'string' && !data.message.startsWith('[DEBUG]')) {
                        this.addLogEntry(data.message, data.level || 'info');
                    }
                }
            } catch (e) {
                console.error("Error al procesar evento de log:", e, "Data:", event.data);
                try {
                    this.addLogEntry(`Error al procesar mensaje del servidor: ${e.message}`, "error");
                } catch (e2) {
                    console.error("Error secundario:", e2);
                }
            }
        });

        // MEJORA: Manejador de eventos 'epoch' más consistente con el de 'log'
        this.source.addEventListener('epoch', (event) => {
            try {
                console.log("%cEvento EPOCH recibido:", "background:#6200ea; color:white; padding:3px 5px;", event.data);
                const data = JSON.parse(event.data);
                
                // Extraer número de época
                let epochNum = data.epoch_number || data.epoch || null;
                if (!epochNum && data.message) {
                    const epochMatch = data.message.match(/(?:Época|Epoch) (\d+)\/(\d+)/);
                    if (epochMatch && epochMatch.length >= 3) {
                        epochNum = parseInt(epochMatch[1]);
                        data.epoch_number = epochNum;
                        data.total_epochs = parseInt(epochMatch[2]);
                    }
                }
                
                // Si no tenemos número de época, no podemos procesarlo correctamente
                if (!epochNum) {
                    console.log("No se pudo determinar el número de época, intentando procesar de todas formas");
                    this.addEpochLogEntry(data.message || "Log de época (sin información detallada)", data.level || 'info', data);
                    return;
                }
                
                // MEJORA: Permitir forzar la actualización de una época ya procesada si
                // el evento viene de una fuente especializada o tiene la flag de forzar
                const forceUpdate = data.from_specialized_cache || data.force_update || false;
                
                // Verificar si ya se procesó esta época
                if (this._epochsProcessed.has(epochNum) && !forceUpdate) {
                    console.log(`Evento 'epoch' duplicado para época ${epochNum}, omitiendo...`);
                    
                    // MEJORA: Actualizar al menos los indicadores visuales para mantener consistencia
                    const totalEpochs = data.total_epochs || 100;
                    if (this.elements.currentEpoch) {
                        this.elements.currentEpoch.textContent = `${epochNum}/${totalEpochs}`;
                    }
                    const progress = (epochNum / totalEpochs) * 100;
                    this.updateTrainingStatus(`Entrenando [Época ${epochNum}/${totalEpochs}]`, progress);
                    
                    return;
                }
                
                // Registrar esta época como la última recibida para detectar huecos
                if (epochNum > this._lastEpochReceived) {
                    // Verificar si hay épocas faltantes
                    if (this._lastEpochReceived > 0 && epochNum > this._lastEpochReceived + 1) {
                        console.warn(`Posible hueco en logs de época: recibida época ${epochNum} después de época ${this._lastEpochReceived}`);
                        
                        // Añadir una notificación visual sutil
                        const gapMessage = `⚠️ Posible salto detectado: de Época ${this._lastEpochReceived} a Época ${epochNum}`;
                        this.addLogEntry(gapMessage, "warning");
                    }
                    this._lastEpochReceived = epochNum;
                }
                
                // Registro explícito de origen del log para diagnóstico
                let source = "evento específico";
                if (data.from_specialized_cache) {
                    source = "caché especializada";
                }
                console.log(`Procesando log de época ${epochNum} desde ${source}`);
                
                // Añadir marca de origen
                data.event_source = "specific_epoch_event";
                
                // Registrar como procesada y mostrarla
                this._epochsProcessed.add(epochNum);
                this.addEpochLogEntry(data.message, data.level || 'info', data);
                
                // Programar verificación de épocas faltantes después de cada log de época
                this._scheduleCheckForMissingEpochs();
                
            } catch (e) {
                console.error("Error al procesar evento de época específico:", e, "Data:", event.data);
            }
        });

        // Mejora para mensajes genéricos
        this.source.onmessage = (event) => {
            try {
                console.log("📩 Mensaje genérico recibido:", event.data);
                const data = JSON.parse(event.data);
                
                // Procesar según el tipo si está disponible
                if (data.type === 'complete' || (data.success === true && data.metrics)) {
                    console.log("🔍 Detectado mensaje de tipo 'complete' en formato genérico");
                    
                    // Marcar como completado
                    this.isComplete = true;
                    
                    // Actualizar interfaz
                    this.updateTrainingStatus("Entrenamiento completado", 100);
                    this._replaceSpinnerWithCheck();
                    
                    // IMPORTANTE: Llamar a AMBAS formas de finalización
                    if (typeof window.handleTrainingComplete === 'function') {
                        window.handleTrainingComplete(data);
                    }
                    
                    if (this.callbacks.onComplete) {
                        this.callbacks.onComplete(data);
                    }
                } else {
                    this.addLogEntry(`Mensaje del servidor: ${JSON.stringify(data)}`, "info");
                }
            } catch (e) {
                console.error("Error al procesar mensaje:", e);
            }
        };
        
        // Manejar eventos de progreso
        this.source.addEventListener('progress', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("Evento de progreso:", data);
                this._updateProgress(data);
                
                // Ya no duplicamos los logs aquí, ahora solo gestionamos el progreso visual
                // y dejamos los logs de época como eventos de tipo 'log'
                
                // Llamar callback personalizado si existe
                if (this.callbacks.onProgress) {
                    this.callbacks.onProgress(data);
                }
            } catch (e) {
                console.error("Error al procesar evento de progreso:", e, "Data:", event.data);
            }
        });
        
        // Manejar eventos de progreso por batch (más frecuentes)
        this.source.addEventListener('batch_progress', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("Evento de progreso batch:", data);
                this._updateBatchProgress(data);
            } catch (e) {
                console.error("Error al procesar evento de batch:", e, "Data:", event.data);
            }
        });
        
        // Mejora específica para evento 'complete'
        this.source.addEventListener('complete', (event) => {
            try {
                console.log("🟢 Evento 'complete' recibido:", event.data);
                const data = JSON.parse(event.data);
                
                // Marcar como completado
                this.isComplete = true;
                
                // Actualizar estado visual
                this.updateTrainingStatus("Entrenamiento completado", 100);
                this.addLogEntry("🎉 ¡Entrenamiento completado con éxito!", "success");
                
                // Reemplazar spinner con ícono de verificación
                this._replaceSpinnerWithCheck();
                
                // IMPORTANTE: Disparar evento global para asegurar que cualquier manejador pueda responder
                const completeEvent = new CustomEvent('training_complete', { detail: data });
                window.dispatchEvent(completeEvent);
                
                // IMPORTANTE: Llamar a AMBAS formas de finalización
                if (typeof window.handleTrainingComplete === 'function') {
                    console.log("📣 Llamando a window.handleTrainingComplete");
                    window.handleTrainingComplete(data);
                }
                
                if (this.callbacks.onComplete) {
                    console.log("📣 Llamando a this.callbacks.onComplete");
                    this.callbacks.onComplete(data);
                }
            } catch (e) {
                console.error("Error al procesar evento de finalización:", e);
            }
        });

        // NUEVO: Evento post_processing_complete (tareas posteriores completadas)
        this.source.addEventListener('post_processing_complete', (event) => {
            try {
                console.log("Post-procesamiento completado:", event.data);
                const data = JSON.parse(event.data);
                
                this.addLogEntry("✅ Post-procesamiento completado: " + data.message, "success");
                
                // Mostrar sección de evaluación
                const evaluationSection = document.getElementById('evaluationSection');
                if (evaluationSection) {
                    evaluationSection.classList.remove('hidden');
                    
                    // Opcionalmente iniciar evaluación automática
                    setTimeout(() => {
                        const modelId = data.model_id || this.trainingId;
                        if (typeof requestModelEvaluation === 'function') {
                            requestModelEvaluation(modelId);
                        }
                    }, 1000);
                }
                
            } catch (e) {
                console.error("Error al procesar evento post-procesamiento:", e);
            }
        });

        // Manejar eventos de error
        this.source.addEventListener('error', (event) => {
            console.error("Error en la conexión SSE:", event);
            
            if (event.target.readyState === EventSource.CLOSED) {
                this.addLogEntry("Conexión cerrada.", "warning");
                if (!this.isComplete) {
                    this._reconnect();
                }
            } else if (event.target.readyState === EventSource.CONNECTING) {
                this.addLogEntry("Reconectando...", "warning");
            } else {
                if (!this.isComplete) {
                    this._reconnect();
                }
            }
        });
        
        // Manejar cierre explícito desde el servidor
        this.source.addEventListener('close', (event) => {
            try {
                const data = JSON.parse(event.data);
                this.addLogEntry(`Conexión finalizada: ${data.message}`, "info");
                
                // Si el mensaje indica que el stream finalizó correctamente, mostrar check
                if (data.message && data.message.includes("Stream finalizado correctamente")) {
                    this.isComplete = true;
                    this.updateTrainingStatus("Completado", 100);
                    this._replaceSpinnerWithCheck();
                }
                
                this.stop();
            } catch (e) {
                console.error("Error al procesar evento de cierre:", e, "Data:", event.data);
            }
        });
        
        // Manejar heartbeats para mantener la conexión viva
        this.source.addEventListener('heartbeat', (event) => {
            // Solo loguear en consola para no sobrecargar la UI
            console.log("Heartbeat recibido:", new Date().toLocaleTimeString());
            
            // MEJORA: Verificar si hay épocas nuevas en el heartbeat
            try {
                const data = JSON.parse(event.data);
                if (data.stats && data.stats.total_epochs > this._epochsProcessed.size) {
                    console.log("%cDetección de épocas en el heartbeat:", "background:orange; color:black;", 
                        `Épocas en el servidor: ${data.stats.total_epochs}, Épocas procesadas: ${this._epochsProcessed.size}`);
                    
                    // Si detectamos que hay épocas sin procesar, mostrar mensaje
                    if (data.stats.total_epochs - this._epochsProcessed.size > 2) {
                        this.addLogEntry(`Detectadas ${data.stats.total_epochs - this._epochsProcessed.size} épocas sin mostrar. Reconectando...`, "warning");
                        // Intentar reconectar para recuperar datos faltantes
                        setTimeout(() => {
                            if (this.source) {
                                this.source.close();
                                this.start();
                            }
                        }, 500);
                    }
                }
            } catch(e) {
                console.error("Error procesando heartbeat:", e);
            }
        });

        // NUEVO: Evento para diagnósticos
        this.source.addEventListener('diagnostic', (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log("Diagnóstico recibido:", data);
                
                if (data.cycles_without_updates > 500) {
                    this.addLogEntry(`Diagnóstico: ${data.cycles_without_updates} ciclos sin actualizaciones.`, "warning");
                }
            } catch (e) {
                console.error("Error al procesar diagnóstico:", e);
            }
        });

        // NUEVO: Evento para heartbeats (mantener conexión viva)
        this.source.addEventListener('heartbeat', (event) => {
            // Solo registrar en consola para no llenar el log
            try {
                const data = JSON.parse(event.data);
                // Actualizar el último tiempo de heartbeat recibido
                this._lastHeartbeatTime = Date.now();
                
                // Disparar evento personalizado para monitoreo de conexión
                const heartbeatEvent = new CustomEvent('training_heartbeat', { detail: data });
                window.dispatchEvent(heartbeatEvent);
                
            } catch (e) {
                console.error("Error al procesar heartbeat:", e);
            }
        });

        // También capturar mensajes genéricos (para compatibilidad)
        this.source.onmessage = (event) => {
            try {
                console.log("Mensaje genérico recibido:", event.data);
                const data = JSON.parse(event.data);
                
                // Procesar según el tipo si está disponible
                if (data.type === 'complete') {
                    // Disparar manualmente el evento complete para asegurar que se procese
                    const customEvent = new MessageEvent('complete', { data: event.data });
                    this.source.dispatchEvent(customEvent);
                } else {
                    this.addLogEntry(`Mensaje del servidor: ${JSON.stringify(data)}`, "info");
                }
            } catch (e) {
                console.error("Error al procesar mensaje:", e);
            }
        };
    }
    
    /**
     * Programa una verificación diferida de épocas faltantes
     * @private
     */
    _scheduleCheckForMissingEpochs() {
        // Cancelar verificación anterior si existe
        if (this._checkMissingEpochsTimer) {
            clearTimeout(this._checkMissingEpochsTimer);
        }
        
        // Programar nueva verificación
        this._checkMissingEpochsTimer = setTimeout(() => {
            this._checkForMissingEpochs();
        }, 5000); // Verificar 5 segundos después del último log de época
    }
    
    /**
     * Verifica si hay épocas faltantes y notifica al usuario
     * @private
     */
    _checkForMissingEpochs() {
        // Solo verificar si ya hemos recibido algunas épocas
        if (this._lastEpochReceived < 3) return;
        
        const missingEpochs = [];
        
        // Buscar épocas faltantes en la secuencia
        for (let i = 1; i < this._lastEpochReceived; i++) {
            if (!this._epochsProcessed.has(i)) {
                missingEpochs.push(i);
            }
        }
        
        // Notificar si hay épocas faltantes
        if (missingEpochs.length > 0) {
            const formattedMissing = missingEpochs.length <= 5 
                ? missingEpochs.join(', ')
                : `${missingEpochs.slice(0, 5).join(', ')} y ${missingEpochs.length - 5} más`;
                
            const message = `ℹ️ No se han recibido logs para algunas épocas: ${formattedMissing}. Esto puede afectar la visualización del progreso.`;
            this.addLogEntry(message, "info");
            
            console.log("Épocas faltantes detectadas:", missingEpochs);
        }
    }
    
    /**
     * Añade específicamente un log de época con formato especial mejorado
     */
    addEpochLogEntry(message, level = 'info', data = null) {
        if (!this.elements.trainingLog) {
            console.warn("No se encontró el elemento trainingLog");
            return;
        }
        
        // Log de diagnóstico detallado
        console.log("%cAñadiendo log de época al DOM:", "background:purple; color:white; padding:2px 5px;", message, data);

        // Si no tenemos mensaje pero tenemos datos, construir uno
        if ((!message || message.trim() === '') && data) {
            if (data.epoch_number !== undefined && data.total_epochs !== undefined) {
                message = `Época ${data.epoch_number}/${data.total_epochs}`;
                if (data.loss !== undefined) {
                    message += ` - loss: ${data.loss.toFixed(4)}`;
                }
                if (data.val_loss !== undefined) {
                    message += ` - val_loss: ${data.val_loss.toFixed(4)}`;
                }
            } else {
                message = "Log de época recibido (sin detalles)";
            }
        }
        
        // MEJORA: Crear el contenedor con estilos más llamativos
        const epochLogContainer = document.createElement('div');
        epochLogContainer.className = 'epoch-log-container epoch-real-log';
        
        // Estilos mejorados para destacar más visualmente
        epochLogContainer.style.borderLeft = '4px solid #00ff00';
        epochLogContainer.style.backgroundColor = 'rgba(0, 50, 0, 0.2)';
        epochLogContainer.style.boxShadow = '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)';
        
        // MEJORA: Si es un log de reintento, darle un estilo especial
        const isRetry = data && data.is_retry;
        
        // MEJORA: Agregar información de origen para diagnóstico
        let source = "normal";
        if (data) {
            if (data.from_specialized_cache) {
                source = "caché especializada";
                // Marcador visual para logs de caché especializada
                epochLogContainer.style.borderRight = '4px solid #00aaff';
            }
            else if (data.event_source === "specific_epoch_event") {
                source = "evento específico";
                // Marcador visual para logs de eventos específicos
                epochLogContainer.style.borderRight = '4px solid #ff9900';
            }
            else if (isRetry) {
                source = "reintento";
                // Marcador visual para logs de reintentos
                epochLogContainer.style.borderRight = '4px solid #ff3366';
                epochLogContainer.style.backgroundColor = 'rgba(50, 0, 0, 0.2)';
            }
        }
        
        // Identificar el número de época para manejar posibles duplicados
        let epochNum = null;
        if (data && (data.epoch_number || data.epoch)) {
            epochNum = data.epoch_number || data.epoch;
        } else if (message) {
            const epochMatch = message.match(/(?:Época|Epoch) (\d+)/);
            if (epochMatch && epochMatch[1]) {
                epochNum = parseInt(epochMatch[1]);
            }
        }
        
        // Si tenemos número de época, usarlo como identificador
        if (epochNum) {
            epochLogContainer.dataset.epoch = epochNum;
            epochLogContainer.dataset.source = source;
            
            // IMPORTANTE: Verificar si ya existe un log para esta época
            const existingLog = this.elements.trainingLog.querySelector(`.epoch-log-container[data-epoch="${epochNum}"]`);
            if (existingLog) {
                console.log(`Reemplazando log existente para época ${epochNum}`);
                existingLog.remove();
            }
        }
        
        // Procesar las líneas del mensaje
        const lines = message ? message.split('\n') : ["Log de época"];
        
        // MEJORA: Primera línea con título más destacado y claro
        const epochTitleLine = document.createElement('p');
        epochTitleLine.className = 'log-line epoch-title';
        epochTitleLine.style.fontWeight = 'bold';
        epochTitleLine.style.color = '#00ff00'; // Verde brillante para todos los logs de época
        epochTitleLine.style.borderBottom = '1px dashed #00ff00';
        epochTitleLine.style.paddingBottom = '4px';
        epochTitleLine.style.marginBottom = '4px';
        epochTitleLine.style.fontSize = '1.1em';
        epochTitleLine.style.textShadow = '0 0 2px rgba(0,0,0,0.8)';
        
        // MEJORA: Agregar identificador de origen si viene de caché especializada
        if (source === "caché especializada") {
            epochTitleLine.innerHTML = `${lines[0]} <span style="font-size:0.8em;color:#00aaff;float:right">[recuperado]</span>`;
        } else {
            epochTitleLine.textContent = lines[0];
        }
        
        epochLogContainer.appendChild(epochTitleLine);
        
        // Resto de líneas: métricas con indentación
        if (lines.length > 1) {
            for (let i = 1; i < lines.length; i++) {
                if (!lines[i] || lines[i].trim() === '') continue;
                
                const metricsLine = document.createElement('p');
                metricsLine.className = 'log-line';
                metricsLine.style.color = '#00ff00';
                metricsLine.style.paddingLeft = '1em';
                metricsLine.style.fontSize = '0.95em';
                
                // MEJORA: Resaltar métricas importantes con más contraste
                const metricText = lines[i];
                if (metricText.includes('loss:') || metricText.includes('val_loss:')) {
                    metricsLine.innerHTML = metricText.replace(/(loss: \d+\.\d+|val_loss: \d+\.\d+|mae: \d+\.\d+|val_mae: \d+\.\d+)/g, 
                        '<span style="font-weight:bold; text-decoration:underline;">$1</span>');
                } else {
                    metricsLine.textContent = metricText;
                }
                
                epochLogContainer.appendChild(metricsLine);
            }
        }
        
        // Añadir con efecto de aparición mejorado
        epochLogContainer.style.animation = 'fadeIn 0.5s ease-out';
        epochLogContainer.style.borderRadius = '4px';
        epochLogContainer.style.padding = '6px 10px';
        epochLogContainer.style.margin = '10px 0';
        
        // Añadir al contenedor principal
        this.elements.trainingLog.appendChild(epochLogContainer);
        
        // Auto-scroll al final del log
        this.elements.trainingLog.scrollTop = this.elements.trainingLog.scrollHeight;
        
        // Confirmación
        console.log("%cLog de época insertado en el DOM ✓", "background:green; color:white; padding:2px 5px;");
    }
    
    /**
     * Añade una nueva entrada al log de entrenamiento
     * @param {string} message - Mensaje a mostrar
     * @param {string} level - Nivel del mensaje (info, success, warning, error)
     */
    addLogEntry(message, level = 'info') {
        if (!this.elements.trainingLog) {
            console.warn("No se encontró el elemento trainingLog");
            return;
        }
        
        // Skip debug logs
        if (message.startsWith('[DEBUG]')) {
            return;
        }
        
        // Depuración adicional
        console.log(`Añadiendo log al DOM: "${message.substring(0, 50)}${message.length > 50 ? '...' : ''}" (${level})`);
        
        const logLine = document.createElement('p');
        logLine.className = 'log-line';
        
        // Aplicar color según nivel
        switch (level) {
            case 'error':
                logLine.style.color = '#ff6b6b';
                break;
            case 'warning':
                logLine.style.color = '#ffd166';
                break;
            case 'success':
                logLine.style.color = '#06d6a0';
                break;
            default: // info
                logLine.style.color = '#00ff00';
        }
        
        // Verificar si es un mensaje con saltos de línea
        if (message.includes('\n')) {
            const lines = message.split('\n');
            logLine.textContent = lines[0];
            this.elements.trainingLog.appendChild(logLine);
            
            // Añadir líneas adicionales con indentación
            for (let i = 1; i < lines.length; i++) {
                const subLine = document.createElement('p');
                subLine.className = 'log-line';
                subLine.style.color = logLine.style.color;
                subLine.style.paddingLeft = '1em';
                subLine.textContent = lines[i];
                this.elements.trainingLog.appendChild(subLine);
            }
        } else {
            // Mensajes simples
            logLine.textContent = message;
            this.elements.trainingLog.appendChild(logLine);
        }
        
        // Auto-scroll al final del log
        this.elements.trainingLog.scrollTop = this.elements.trainingLog.scrollHeight;
    }
    
    /**
     * Actualiza la interfaz con información de progreso por época
     * @param {Object} data - Datos de progreso
     * @private
     */
    _updateProgress(data) {
        // Actualizar barra de progreso
        if (data.epoch !== undefined && data.total_epochs !== undefined) {
            const progress = (data.epoch / data.total_epochs) * 100;
            this.updateTrainingStatus(`Entrenando [Época ${data.epoch}/${data.total_epochs}]`, progress);
            
            if (this.elements.currentEpoch) {
                this.elements.currentEpoch.textContent = `${data.epoch}/${data.total_epochs}`;
                this._animateElement(this.elements.currentEpoch);
            }
        }
        
        // Actualizar métricas
        if (data.train_loss !== undefined && this.elements.trainLoss) {
            this.elements.trainLoss.textContent = data.train_loss.toFixed(4);
            this._animateElement(this.elements.trainLoss);
        }
        
        if (data.val_loss !== undefined && this.elements.valLoss) {
            this.elements.valLoss.textContent = data.val_loss.toFixed(4);
            this._animateElement(this.elements.valLoss);
        }
        
        // Actualizar tiempo restante
        if (data.remaining_time && this.elements.remainingTime) {
            this.elements.remainingTime.textContent = data.remaining_time;
            this._animateElement(this.elements.remainingTime);
        }
    }
    
    /**
     * Actualiza la interfaz con información de progreso por batch
     * @param {Object} data - Datos de progreso por batch
     * @private
     */
    _updateBatchProgress(data) {
        // En actualizaciones por batch, solo cambiamos el loss actual sin modificar el estado general
        if (data.loss !== undefined && this.elements.trainLoss) {
            this.elements.trainLoss.textContent = data.loss.toFixed(4);
        }
        
        // Si incluye información de época, actualizar
        if (data.epoch !== undefined && data.total_epochs !== undefined && this.elements.currentEpoch) {
            this.elements.currentEpoch.textContent = `${data.epoch}/${data.total_epochs}`;
            
            // También actualizar la barra de progreso
            const progress = (data.epoch / data.total_epochs) * 100;
            if (this.elements.trainingProgress) {
                this.elements.trainingProgress.style.width = `${progress}%`;
            }
        }
    }
    
    /**
     * Actualiza el estado del entrenamiento y la barra de progreso
     * @param {string} status - Texto de estado
     * @param {number} progress - Porcentaje de progreso (0-100)
     */
    updateTrainingStatus(status, progress) {
        // Actualizar elementos de la interfaz correctamente usando this.elements
        if (this.elements.trainingStatus) {
            this.elements.trainingStatus.textContent = status;
        }
        
        if (this.elements.trainingProgress) {
            this.elements.trainingProgress.style.width = `${progress}%`;
        }
        
        // Si el estado es "Completado", mostrar check
        if (status === "Completado" || status === "Finalizado") {
            this._replaceSpinnerWithCheck();
        }
    }
    
    /**
     * Añade una animación de actualización a un elemento
     * @param {HTMLElement} element - Elemento a animar
     * @private
     */
    _animateElement(element) {
        element.classList.add('text-update');
        setTimeout(() => element.classList.remove('text-update'), 300);
    }
    
    /**
     * Reemplaza el spinner de carga con un icono de verificación
     * @private
     */
    _replaceSpinnerWithCheck() {
        const spinnerElement = document.getElementById('trainingSpinner');
        if (spinnerElement) {
            // Reemplazar spinner con icono de check de verificación
            spinnerElement.classList.remove('spinner');
            spinnerElement.innerHTML = `
                <svg class="h-8 w-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                </svg>
            `;
            console.log("Spinner reemplazado por icono de verificación");
        }
    }
}

// Añadir CSS dinámicamente para la animación
const style = document.createElement('style');
style.textContent = `
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}
.epoch-log-container {
    margin: 8px 0;
    padding: 5px;
    border-left: 3px solid #00ff00;
    background-color: rgba(0, 255, 0, 0.05);
}
.text-update {
    animation: pulse 0.3s ease-in-out;
}
@keyframes pulse {
    0% { background-color: transparent; }
    50% { background-color: rgba(0, 255, 0, 0.3); }
    100% { background-color: transparent; }
}
`;
document.head.appendChild(style);