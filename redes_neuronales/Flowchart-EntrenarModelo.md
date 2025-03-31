```mermaid
flowchart TB
    %% Definición de estilos
    classDef default color:#000;
    classDef userInterface fill:#e1f5fe,stroke:#01579b,stroke-width:2px
    classDef serverEndpoint fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    classDef processingModule fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    classDef dataFlow fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef modelComponent fill:#ffebee,stroke:#c62828,stroke-width:2px
    classDef utilityFunction fill:#ede7f6,stroke:#4527a0,stroke-width:2px
    classDef storageComponent fill:#e0f7fa,stroke:#006064,stroke-width:2px
    classDef dataOperation fill:#fff3e0,stroke:#e65100,stroke-width:2px

    %% Inicio del proceso - Interfaz de usuario
    startUI([Usuario accede a la interfaz de entrenamiento]):::userInterface --> loadWebUI

    subgraph UI [Interfaz de Usuario - entrenar_modelo.html]
        loadWebUI[Carga entrenar_modelo.html]:::userInterface --> checkTraining
        checkTraining{¿Entrenamiento activo?}:::userInterface
        checkTraining -->|No| showConfigForm[Mostrar formulario de configuración]:::userInterface 
        checkTraining -->|Sí| loadActiveTraining[Cargar entrenamiento activo]:::userInterface

        showConfigForm --> configDataSource{{Selección fuente de datos}}:::userInterface
        configDataSource -->|CSV| configUpload[Cargar archivo CSV]:::userInterface
        configDataSource -->|Base de datos| configSynthetic[Configurar datos sintéticos]:::userInterface
        configDataSource -->|Sintético| configGenerate[Configurar generación de datos]:::userInterface
        
        configUpload & configSynthetic & configGenerate --> configNN[Configurar arquitectura de red]:::userInterface
        configNN --> configParams[Configurar hiperparámetros]:::userInterface
        configParams --> validateForm{Formulario válido?}:::userInterface
        validateForm -->|No| showErrors[Mostrar errores]:::userInterface --> configParams
        validateForm -->|Sí| submitForm[Enviar formulario]:::userInterface
        
        loadActiveTraining --> monitoringInit[Inicializar TrainingMonitor.js]:::userInterface
    end

    submitForm --> callBackend>POST iniciar_entrenamiento]:::serverEndpoint

    %% Backend: Iniciar entrenamiento
    callBackend --> serverValidation

    subgraph Backend [Procesamiento en Servidor - views.py]
        serverValidation{Validar datos en servidor}:::serverEndpoint
        serverValidation -->|Error| returnError[Retornar error JSON]:::serverEndpoint
        serverValidation -->|Válido| setupTrainingConfig[Crear configuración de entrenamiento]:::serverEndpoint
        
        setupTrainingConfig --> cacheConfig[(Guardar en caché Redis)]:::storageComponent
        cacheConfig --> createTrainingID[Generar ID único de entrenamiento]:::serverEndpoint
        createTrainingID --> dispatchTask{{Despachar tarea asíncrona}}:::serverEndpoint
    end

    %% Tasks - Gestión de procesos
    dispatchTask --> createProcess

    subgraph TasksProcessing [Gestión de Procesos - tasks.py]
        createProcess[tasks.py: start_training_process.delay]:::utilityFunction 
        createProcess --> newProcess[(Crear proceso separado)]:::utilityFunction
        newProcess --> processWrapper{{Ejecutar entrenamiento en proceso aislado}}:::utilityFunction
    end

    %% Entrenamiento principal
    processWrapper --> trainingMain

    subgraph MainTraining [Entrenamiento - entrenamiento_utils.py]
        trainingMain[ejecutar_entrenamiento]:::processingModule
        trainingMain --> backendConfig[Configurar backend no-interactivo]:::utilityFunction
        backendConfig --> retrieveConfig[(Obtener configuración de caché)]:::processingModule
        
        retrieveConfig --> dataSourceDecision{Fuente\nde datos?}:::processingModule
        dataSourceDecision -->|CSV| loadCSV[(data_processor.py: load_data)]:::dataFlow
        dataSourceDecision -->|DB| loadDB[(load_data_from_db)]:::dataFlow
        dataSourceDecision -->|Sintético| generateData>data_processor.py: generate_synthetic_data]:::dataFlow
        
        loadDB --> useSyntheticData{¿Aumentar\ndatos?}:::processingModule
        loadCSV--> preprocessData
        useSyntheticData -->|Sí| generateData
        useSyntheticData -->|No| preprocessData
        generateData --> preprocessData
        
        preprocessData[[data_processor.py: preprocess_data]]:::dataFlow
        preprocessData --> dataValidation{{Validación de datos}}:::dataFlow
        dataValidation -->|Falta feature| handleMissingFeatures[Rellenar datos faltantes]:::dataFlow
        handleMissingFeatures --> splitData
        dataValidation -->|Datos OK| splitData>Dividir: train/val/test]:::dataFlow
        
        splitData --> storePreprocessors[(save_preprocessors)]:::storageComponent
    end

    %% Construcción y entrenamiento del modelo
    storePreprocessors --> buildModelProcess

    subgraph ModelTraining [Construcción del Modelo - rnn_model.py]
        buildModelProcess[rnn_model.py: build_model]:::modelComponent
        buildModelProcess --> architectureSetup{{Configurar arquitectura GRU/LSTM}}:::modelComponent
        architectureSetup --> optimizerSetup>Configurar optimizador]:::modelComponent
        optimizerSetup --> callbacksSetup[Configurar callbacks]:::utilityFunction
        
        callbacksSetup --> fitProcess{{model.fit - Entrenamiento}}:::modelComponent
        
        fitProcess --> iterateEpochs{{Iteración por épocas}}:::modelComponent
        iterateEpochs --> calculateBatch[Procesar batch]:::modelComponent
        calculateBatch --> updateWeights[Actualizar pesos]:::modelComponent
        updateWeights --> checkEpochEnd{¿Fin de\nla época?}:::modelComponent
        checkEpochEnd -->|No| calculateBatch
        checkEpochEnd -->|Sí| progressCallback[Enviar progreso]:::utilityFunction
        
        progressCallback --> evaluateModel[Evaluar con datos validación]:::modelComponent
        evaluateModel --> checkConvergence{¿Convergencia o\nmáx épocas?}:::modelComponent
        checkConvergence -->|No| iterateEpochs
        checkConvergence -->|Sí| finalizeModel[Finalizar modelo]:::modelComponent
    end

    %% Comunicación en tiempo real
    progressCallback ---> communicationLayer

    subgraph IPCComm [Comunicación Real-time - ipc_utils.py]
        communicationLayer[ipc_utils.py: send_update]:::utilityFunction
        communicationLayer --> queueUpdate[(Almacenar actualización en cola)]:::storageComponent
        queueUpdate --> eventCreation[Crear SSE]:::serverEndpoint
        
        eventCreation --> clientReceive{{Recibir en cliente}}:::userInterface
    end

    clientReceive --> clientUI

    subgraph ClientUI [Actualización UI - training-monitor.js]
        clientUI[Recibir actualización]:::userInterface
        clientUI --> parseProgress[Procesar datos de progreso]:::userInterface
        parseProgress --> updateProgressBar[Actualizar barra y métricas]:::userInterface
        updateProgressBar --> addLogEntry[Añadir entrada a log]:::userInterface
        addLogEntry --> chartUpdate{{Actualizar gráficos en tiempo real}}:::userInterface
    end

    %% Finalización del entrenamiento
    finalizeModel --> trainingComplete

    subgraph PostProcessing [Post-procesamiento - post_training_tasks.py]
        trainingComplete{{Entrenamiento completado}}:::processingModule
        trainingComplete --> modelPersistence[(Guardar modelo .keras)]:::storageComponent
        modelPersistence --> historyPersistence[(Guardar historial)]:::storageComponent
        historyPersistence --> metricsCalculation[Calcular métricas finales]:::processingModule
        
        metricsCalculation --> notifyCompletion[Notificar finalización]:::serverEndpoint
        notifyCompletion --> runEvaluation[[evaluator.py: evaluate_model]]:::processingModule
        
        runEvaluation --> generatePlots>Generar gráficos]:::dataFlow
        generatePlots --> featureImportance{{Calcular importancia de características}}:::processingModule
        featureImportance --> segmentedAnalysis[Análisis segmentado por tamaño]:::processingModule
    end

    notifyCompletion --> showResults

    subgraph ResultsUI [Visualización de Resultados]
        showResults[Mostrar panel de resultados]:::userInterface
        showResults --> hideProgress[Ocultar indicadores progreso]:::userInterface
        hideProgress --> displaySummary>Mostrar resumen de métricas]:::userInterface
        displaySummary --> showCharts{{Renderizar gráficos de resultados}}:::userInterface
        showCharts --> enableDownload[Habilitar descarga de gráficos]:::userInterface
    end

    segmentedAnalysis --> resultsReady{{Resultados listos}}:::processingModule

    resultsReady --> userOptions

    subgraph UserActions [Acciones Post-entrenamiento]
        userOptions{Acción del usuario}:::userInterface
        
        userOptions -->|Evaluar Modelo| evaluateDetailBtn[[Ejecutar evaluación detallada]]:::processingModule
        userOptions -->|Generar Informe| reportGeneration[(Generar PDF)]:::processingModule
        userOptions -->|TensorBoard| openTBBtn>Abrir TensorBoard]:::serverEndpoint
        userOptions -->|Recargar Modelo| reloadModelBtn[Recargar en memoria]:::serverEndpoint
        
        evaluateDetailBtn --> displayEvaluationDetail[Ver métricas detalladas]:::userInterface
    end

    reloadModelBtn --> integrationStart

    subgraph Integration [Integración con Aplicación]
        integrationStart[[model_service.py: initialize]]:::processingModule
        integrationStart --> loadModel[(Cargar modelo en servicio)]:::modelComponent
        loadModel --> configureService>Configurar servicio de predicción]:::processingModule
        configureService --> registerEstimator[Registrar en sistema]:::processingModule
        registerEstimator --> readyProduction{{Modelo listo para producción}}:::processingModule
    end

    readyProduction --> productionUse[Uso en vista estimación_avanzada.html]:::userInterface

    subgraph EstimationProcess [Proceso de Estimación]
        productionUse --> extractFeatures[Extraer características de tarea]:::processingModule
        extractFeatures --> processFeatures[[data_processor.py: process_single_task]]:::dataFlow
        processFeatures --> runPrediction>rnn_model.py: predict]:::modelComponent
        runPrediction --> displayEstimation[Mostrar tiempo estimado]:::userInterface
    end

    %% Estilo para nodos clave
    style startUI font-weight:bold,font-size:16px
    style trainingMain font-weight:bold
    style fitProcess font-weight:bold,stroke-width:3px
    style finalizeModel font-weight:bold
    style showResults font-weight:bold
    style readyProduction font-weight:bold,font-size:16px
    style clientUI font-weight:bold