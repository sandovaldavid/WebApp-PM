/**
 * Gestión de la integración con Jira - Versión Refactorizada
 * Esta versión utiliza componentes para manipular el DOM sin innerHTML
 */

// Token CSRF para peticiones POST
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// URLs de endpoints
const URLS = {
    configurar: '/integracion/jira/configurar/',
    configuracionAvanzada: '/integracion/jira/configuracion-avanzada/',
    listarProyectos: '/integracion/jira/proyectos/',
    mapearProyecto: '/integracion/jira/mapear-proyecto/',
    sincronizar: '/integracion/jira/sincronizar/',
    listarUsuarios: '/integracion/jira/usuarios/',
    mapearUsuarios: '/integracion/jira/mapear-usuarios/',
    limpiarMapeos: '/integracion/jira/limpiar-mapeos/',
    estadoSalud: '/integracion/jira/estado-salud/',
    reporteSincronizacion: '/integracion/jira/reporte-sincronizacion/',
};

/**
 * Configura la integración con Jira
 */
async function configurarJira(formData) {
    try {
        const response = await fetch(URLS.configurar, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al configurar Jira');
        }
        
        // Mostrar notificación de éxito
        NotificationComponent.show('success', 'Configuración guardada correctamente');
        
        // Cerrar modal y actualizar interfaz
        ModalComponent.close();
        
        // Mostrar panel de mapeo de proyectos
        loadJiraProjects();
        
        return data;
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Actualiza la configuración avanzada de Jira
 */
async function updateAdvancedConfig(formData) {
    try {
        const response = await fetch(URLS.configuracionAvanzada, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al actualizar configuración avanzada');
        }
        
        NotificationComponent.show('success', 'Configuración avanzada actualizada correctamente');
        ModalComponent.close();
        
        return data;
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Carga los proyectos de Jira y locales para mapeo
 */
async function loadJiraProjects() {
    try {
        // Verificar si estamos en la pestaña correcta, si no, cambiar a ella
        const projectsTab = document.getElementById('projectsTab');
        if (projectsTab && projectsTab.classList.contains('hidden')) {
            switchTab('projectsTab');
        }
        
        // Mostrar indicador de carga
        ProjectComponent.showLoader();
        
        const response = await fetch(URLS.listarProyectos);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al obtener proyectos');
        }
        
        // Cargar template si es necesario
        await TemplateLoader.loadTemplate('projectMappingSection', 'components/project_mapping.html');
        
        // Actualizar UI con los componentes
        ProjectComponent.updateProjectMapping(data.jira_projects, data.local_projects);
        
    } catch (error) {
        ProjectComponent.showError(error.message || 'Error al cargar proyectos');
        console.error('Error:', error);
    }
}

/**
 * Cambia entre las pestañas de la interfaz
 */
function switchTab(tabId) {
    // Ocultar todos los contenidos de pestañas
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.add('hidden');
    });
    
    // Mostrar la pestaña seleccionada
    const selectedTab = document.getElementById(tabId);
    if (selectedTab) {
        selectedTab.classList.remove('hidden');
    }
    
    // Actualizar estado de los botones de pestañas
    document.querySelectorAll('#integrationTabs a').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600', 'integration-tab-active');
        btn.classList.add('border-transparent', 'text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
    });
    
    // Marcar el botón activo con clases más modernas
    const activeButton = document.getElementById(tabId + 'Btn');
    if (activeButton) {
        activeButton.classList.remove('border-transparent', 'text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
        activeButton.classList.add('border-blue-500', 'text-blue-600', 'integration-tab-active');
    }
    
    // Gestionar visibilidad de secciones específicas según la pestaña
    const projectMappingSection = document.getElementById('projectMappingSection');
    const userMappingSection = document.getElementById('userMappingSection');
    const healthCheckSection = document.getElementById('healthCheckSection');
    const syncReportSection = document.getElementById('syncReportSection');
    
    // Por defecto, ocultar todos los paneles específicos
    if (projectMappingSection) projectMappingSection.classList.add('hidden');
    if (userMappingSection) userMappingSection.classList.add('hidden');
    if (healthCheckSection) healthCheckSection.classList.add('hidden');
    if (syncReportSection) syncReportSection.classList.add('hidden');
    
    // Mostrar solo los paneles correspondientes a la pestaña activa
    // pero solo si ya han sido cargados (no tienen clase 'unloaded')
    switch(tabId) {
        case 'projectsTab':
            if (projectMappingSection && !projectMappingSection.classList.contains('unloaded')) {
                projectMappingSection.classList.remove('hidden');
            }
            break;
            
        case 'usersTab':
            if (userMappingSection && !userMappingSection.classList.contains('unloaded')) {
                userMappingSection.classList.remove('hidden');
            }
            break;
            
        case 'reportsTab':
            if (healthCheckSection && !healthCheckSection.classList.contains('unloaded')) {
                healthCheckSection.classList.remove('hidden');
            }
            if (syncReportSection && !syncReportSection.classList.contains('unloaded')) {
                syncReportSection.classList.remove('hidden');
            }
            break;
    }
}

/**
 * Mapea un proyecto local con uno de Jira
 */
async function mapProject(localProjectId) {
    const selectElement = document.getElementById(`jira-project-${localProjectId}`);
    if (!selectElement) return;
    
    const jiraProjectKey = selectElement.value;
    
    if (!jiraProjectKey) {
        NotificationComponent.show('warning', 'Selecciona un proyecto de Jira');
        return;
    }
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const jiraProjectId = selectedOption.getAttribute('data-jira-id');
    
    try {
        const response = await fetch(URLS.mapearProyecto, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                proyecto_local_id: localProjectId,
                jira_project_key: jiraProjectKey,
                jira_project_id: jiraProjectId
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al mapear proyecto');
        }
        
        NotificationComponent.show('success', 'Proyecto mapeado correctamente');
        
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Inicia la sincronización con Jira
 */
async function sincronizarJira(event) {
    const syncButton = event ? 
        (event.target.tagName === 'BUTTON' ? event.target : event.target.closest('button')) :
        document.getElementById('sync-projects-btn');
        
    if (!syncButton) return;
        
    try {
        // Cambiar estado del botón
        const originalContent = syncButton.innerHTML;
        syncButton.disabled = true;
        
        // Crear y agregar el icono de carga
        const loadingIcon = document.createElement('i');
        loadingIcon.className = 'fas fa-spinner fa-spin mr-2';
        
        const loadingText = document.createTextNode(' Sincronizando...');
        
        syncButton.innerHTML = '';
        syncButton.appendChild(loadingIcon);
        syncButton.appendChild(loadingText);
        
        const response = await fetch(URLS.sincronizar, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error en la sincronización');
        }
        
        NotificationComponent.show('success', 'Sincronización completada correctamente');
        
        // Actualizar estado de salud después de la sincronización
        checkIntegrationHealth();
        
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    } finally {
        // Restaurar botón
        syncButton.disabled = false;
        
        // Recrear el SVG para el botón
        const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svgIcon.setAttribute('class', 'w-5 h-5 mr-2');
        svgIcon.setAttribute('fill', 'none');
        svgIcon.setAttribute('stroke', 'currentColor');
        svgIcon.setAttribute('viewBox', '0 0 24 24');
        
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('stroke-linejoin', 'round');
        path.setAttribute('stroke-width', '2');
        path.setAttribute('d', 'M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15');
        
        svgIcon.appendChild(path);
        
        syncButton.innerHTML = '';
        syncButton.appendChild(svgIcon);
        syncButton.appendChild(document.createTextNode(' Sincronizar Ahora'));
    }
}

/**
 * Carga usuarios de Jira y usuarios locales para mapeo
 */
async function loadJiraUsers() {
    try {
        // Verificar si estamos en la pestaña correcta
        const usersTab = document.getElementById('usersTab');
        if (usersTab && usersTab.classList.contains('hidden')) {
            switchTab('usersTab');
        }
        
        // Mostrar indicador de carga
        UserComponent.showLoader();
        
        const response = await fetch(URLS.listarUsuarios);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al obtener usuarios');
        }
        
        // Cargar template si es necesario
        await TemplateLoader.loadTemplate('userMappingSection', 'components/user_mapping.html');
        
        // Actualizar UI con los componentes
        UserComponent.updateUserMapping(data.jira_users, data.local_users);
        
    } catch (error) {
        UserComponent.showError(error.message || 'Error al cargar usuarios');
        console.error('Error:', error);
    }
}

/**
 * Mapea un usuario local con uno de Jira
 */
async function mapUser(localUserId) {
    const selectElement = document.getElementById(`jira-user-${localUserId}`);
    if (!selectElement) return;
    
    const jiraUserId = selectElement.value;
    
    if (!jiraUserId) {
        NotificationComponent.show('warning', 'Selecciona un usuario de Jira');
        return;
    }
    
    const selectedOption = selectElement.options[selectElement.selectedIndex];
    const jiraUserName = selectedOption.getAttribute('data-display-name');
    
    try {
        const response = await fetch(URLS.mapearUsuarios, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                mappings: [{
                    local_user_id: localUserId,
                    jira_user_id: jiraUserId,
                    jira_user_name: jiraUserName
                }]
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al mapear usuario');
        }
        
        NotificationComponent.show('success', 'Usuario mapeado correctamente');
        
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Inicia el mapeo automático de usuarios por correo electrónico
 */
async function mapAllUsersAuto() {
    try {
        const autoMapBtn = document.getElementById('auto-map-users-btn');
        if (autoMapBtn) {
            // Desactivar botón durante el mapeo
            const originalContent = autoMapBtn.innerHTML;
            autoMapBtn.disabled = true;
            autoMapBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Mapeando...';
        }
        
        const response = await fetch(URLS.mapearUsuarios, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                mappings: [] // Enviar array vacío para mapeo automático
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error en el mapeo automático');
        }
        
        NotificationComponent.show('success', data.message || 'Mapeo automático completado');
        
        // Recargar la lista de usuarios para mostrar los nuevos mapeos
        loadJiraUsers();
        
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    } finally {
        // Restaurar botón
        const autoMapBtn = document.getElementById('auto-map-users-btn');
        if (autoMapBtn) {
            autoMapBtn.disabled = false;
            
            // Recrear el SVG para el botón
            const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svgIcon.setAttribute('class', 'w-5 h-5 mr-2');
            svgIcon.setAttribute('fill', 'none');
            svgIcon.setAttribute('stroke', 'currentColor');
            svgIcon.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M12 6v6m0 0v6m0-6h6m-6 0H6');
            
            svgIcon.appendChild(path);
            
            autoMapBtn.innerHTML = '';
            autoMapBtn.appendChild(svgIcon);
            autoMapBtn.appendChild(document.createTextNode(' Mapeo Automático'));
        }
    }
}

/**
 * Limpia mapeos huérfanos (sin tarea o issue correspondiente)
 */
async function cleanOrphanedMappings() {
    if (!confirm('¿Estás seguro de que deseas limpiar los mapeos huérfanos? Esta acción no se puede deshacer.')) {
        return;
    }
    
    try {
        const cleanBtn = document.getElementById('clean-mappings-btn');
        if (cleanBtn) {
            // Desactivar botón durante la limpieza
            cleanBtn.disabled = true;
            cleanBtn.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Limpiando...';
        }
        
        const response = await fetch(URLS.limpiarMapeos, {
            method: 'POST',
            headers: {
                'X-CSRFToken': csrfToken
            }
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al limpiar mapeos');
        }
        
        NotificationComponent.show('success', `Limpieza completada. Se eliminaron ${data.total_cleaned} mapeos huérfanos.`);
        
        // Recargar usuarios para reflejar los cambios
        loadJiraUsers();
        
    } catch (error) {
        NotificationComponent.show('error', error.message);
        console.error('Error:', error);
    } finally {
        // Restaurar botón
        const cleanBtn = document.getElementById('clean-mappings-btn');
        if (cleanBtn) {
            cleanBtn.disabled = false;
            
            // Recrear el SVG para el botón
            const svgIcon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svgIcon.setAttribute('class', 'w-5 h-5 mr-2');
            svgIcon.setAttribute('fill', 'none');
            svgIcon.setAttribute('stroke', 'currentColor');
            svgIcon.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16');
            
            svgIcon.appendChild(path);
            
            cleanBtn.innerHTML = '';
            cleanBtn.appendChild(svgIcon);
            cleanBtn.appendChild(document.createTextNode(' Limpiar Mapeos'));
        }
    }
}

/**
 * Comprueba el estado de salud de la integración con Jira
 */
async function checkIntegrationHealth() {
    try {
        // Verificar si estamos en la pestaña correcta
        const reportsTab = document.getElementById('reportsTab');
        if (reportsTab && reportsTab.classList.contains('hidden')) {
            switchTab('reportsTab');
        }
        
        // Mostrar indicador de carga
        HealthComponent.showLoader();
        
        const response = await fetch(URLS.estadoSalud);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al verificar estado');
        }
        
        // Cargar template si es necesario
        await TemplateLoader.loadTemplate('healthCheckSection', 'components/health_check.html');
        
        // Actualizar UI con los componentes
        HealthComponent.updateHealthReport(data.health_report);
        
    } catch (error) {
        HealthComponent.showError(error.message || 'Error al verificar estado');
        console.error('Error:', error);
    }
}

/**
 * Genera y muestra un reporte completo de sincronización
 * @param {Number} days - Días a incluir en el reporte (por defecto 30)
 */
async function generateSyncReport(days = 30) {
    try {
        // Verificar si estamos en la pestaña correcta
        const reportsTab = document.getElementById('reportsTab');
        if (reportsTab && reportsTab.classList.contains('hidden')) {
            switchTab('reportsTab');
        }
        
        // Mostrar indicador de carga
        SyncReportComponent.showLoader();
        
        const response = await fetch(`${URLS.reporteSincronizacion}?days=${days}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al generar reporte');
        }
        
        // Cargar template si es necesario
        await TemplateLoader.loadTemplate('syncReportSection', 'components/sync_report.html');
        
        // Actualizar UI con los componentes
        SyncReportComponent.updateSyncReport(data.report);
        
    } catch (error) {
        SyncReportComponent.showError(error.message || 'Error al generar reporte');
        console.error('Error:', error);
    }
}

/**
 * Abre el modal de configuración avanzada
 */
function openAdvancedConfigModal() {
    // Crear modal si no existe
    if (!document.getElementById('advancedConfigModal')) {
        const modal = document.createElement('div');
        modal.id = 'advancedConfigModal';
        modal.className = 'hidden fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50 modal';
        
        const modalContent = document.createElement('div');
        modalContent.className = 'relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white';
        
        modalContent.innerHTML = `
            <div class="mt-3">
                <div class="flex justify-between items-center pb-3 border-b">
                    <h3 class="text-lg font-medium text-gray-900 flex items-center">
                        <i class="fas fa-cogs mr-2 text-blue-500"></i>
                        Configuración Avanzada de Jira
                    </h3>
                    <button type="button" id="closeAdvancedConfigBtn" class="text-gray-400 hover:text-gray-500">
                        <i class="fas fa-times"></i>
                    </button>
                </div>

                <form id="jiraAdvancedConfigForm" class="mt-4">
                    <div class="space-y-4">
                        <div class="flex items-center">
                            <input type="checkbox" id="importarIssues" name="importarIssues" class="rounded text-blue-500 focus:ring-blue-500">
                            <label for="importarIssues" class="ml-2 block text-sm text-gray-700">
                                Importar issues desde Jira
                            </label>
                        </div>
                        
                        <div class="flex items-center">
                            <input type="checkbox" id="exportarTareas" name="exportarTareas" class="rounded text-blue-500 focus:ring-blue-500">
                            <label for="exportarTareas" class="ml-2 block text-sm text-gray-700">
                                Exportar tareas locales a Jira
                            </label>
                        </div>
                        
                        <div class="flex items-center">
                            <input type="checkbox" id="syncComentarios" name="syncComentarios" class="rounded text-blue-500 focus:ring-blue-500">
                            <label for="syncComentarios" class="ml-2 block text-sm text-gray-700">
                                Sincronizar comentarios
                            </label>
                        </div>
                        
                        <div class="flex items-center">
                            <input type="checkbox" id="sincronizarAdjuntos" name="sincronizarAdjuntos" class="rounded text-blue-500 focus:ring-blue-500">
                            <label for="sincronizarAdjuntos" class="ml-2 block text-sm text-gray-700">
                                Sincronizar archivos adjuntos
                            </label>
                        </div>
                    </div>

                    <div class="flex justify-between pt-4 mt-4 border-t">
                        <button type="button" id="cancelAdvancedConfigBtn" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors">
                            Cancelar
                        </button>
                        <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
                            <i class="fas fa-save mr-1"></i> Guardar Configuración
                        </button>
                    </div>
                </form>
            </div>
        `;
        
        modal.appendChild(modalContent);
        document.body.appendChild(modal);
        
        // Configurar eventos del modal
        document.getElementById('closeAdvancedConfigBtn').onclick = () => ModalComponent.close('advancedConfigModal');
        document.getElementById('cancelAdvancedConfigBtn').onclick = () => ModalComponent.close('advancedConfigModal');
        
        // Configurar el formulario
        document.getElementById('jiraAdvancedConfigForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                importar_issues: document.getElementById('importarIssues').checked,
                exportar_tareas: document.getElementById('exportarTareas').checked,
                sync_comentarios: document.getElementById('syncComentarios').checked,
                sincronizar_adjuntos: document.getElementById('sincronizarAdjuntos').checked
            };
            
            updateAdvancedConfig(formData);
        });
    }
    
    // Cargar configuración actual
    fetchCurrentAdvancedConfig();
    
    // Mostrar modal
    ModalComponent.open('advancedConfigModal');
}

/**
 * Obtiene la configuración avanzada actual
 */
async function fetchCurrentAdvancedConfig() {
    try {
        // Obtener valores actuales de configuración desde el elemento de estado
        const configStatus = document.getElementById('jiraConfigStatus');
        
        if (configStatus && configStatus.dataset.importarIssues !== undefined) {
            document.getElementById('importarIssues').checked = configStatus.dataset.importarIssues === 'true';
            document.getElementById('exportarTareas').checked = configStatus.dataset.exportarTareas === 'true';
            document.getElementById('syncComentarios').checked = configStatus.dataset.syncComentarios === 'true';
            document.getElementById('sincronizarAdjuntos').checked = configStatus.dataset.sincronizarAdjuntos === 'true';
        } else {
            // Valores predeterminados
            document.getElementById('importarIssues').checked = true;
            document.getElementById('exportarTareas').checked = true;
            document.getElementById('syncComentarios').checked = true;
            document.getElementById('sincronizarAdjuntos').checked = false;
        }
        
    } catch (error) {
        console.error('Error al cargar configuración avanzada:', error);
        NotificationComponent.show('error', 'Error al cargar la configuración avanzada');
    }
}

/**
 * Añade pestañas de navegación para la interfaz de integración
 */
function setupIntegrationTabs() {
    const container = document.querySelector('.p-8.space-y-8');
    if (!container) return;
    
    // Crear contenedor de pestañas si no existe
    if (!document.getElementById('integrationTabs')) {
        const tabsContainer = document.createElement('div');
        tabsContainer.id = 'integrationTabs';
        tabsContainer.className = 'border-b border-gray-200 mb-6';
        
        // Crear el contenido de las pestañas usando DOM API en lugar de innerHTML
        const tabsList = document.createElement('ul');
        tabsList.className = 'flex flex-wrap -mb-px text-sm font-medium text-center';
        
        // Añadir pestaña de configuración
        const configTab = createTabElement('configTab', 'Configuración', 'cog');
        tabsList.appendChild(configTab);
        
        // Añadir pestaña de proyectos
        const projectsTab = createTabElement('projectsTab', 'Proyectos', 'project-diagram');
        tabsList.appendChild(projectsTab);
        
        // Añadir pestaña de usuarios
        const usersTab = createTabElement('usersTab', 'Usuarios', 'users');
        tabsList.appendChild(usersTab);
        
        // Añadir pestaña de reportes
        const reportsTab = createTabElement('reportsTab', 'Reportes', 'chart-bar');
        tabsList.appendChild(reportsTab);
        
        tabsContainer.appendChild(tabsList);
        
        // Insertar al principio del contenedor principal
        container.insertBefore(tabsContainer, container.firstChild);
        
        // Crear contenedores de contenido para cada pestaña
        const contentContainers = createTabContentContainers();
        container.appendChild(contentContainers);
        
        // Mover contenido existente a la pestaña de configuración
        const configTabContent = document.getElementById('configTab');
        const tools = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-3.gap-6');
        
        if (tools && configTabContent) {
            configTabContent.appendChild(tools);
        }
        
        // Configurar pestaña activa por defecto
        switchTab('configTab');
    }
}

/**
 * Crea un elemento de pestaña
 * @param {String} id - ID de la pestaña
 * @param {String} label - Etiqueta de la pestaña
 * @param {String} iconName - Nombre del icono de FontAwesome
 * @returns {HTMLLIElement} - Elemento de pestaña
 */
function createTabElement(id, label, iconName) {
    const tabItem = document.createElement('li');
    tabItem.className = 'mr-2';
    
    const tabLink = document.createElement('a');
    tabLink.href = '#';
    tabLink.id = id + 'Btn';
    tabLink.className = 'inline-block p-4 rounded-t-lg border-b-2 border-transparent hover:border-gray-300 text-gray-500 hover:text-gray-600';
    tabLink.onclick = function(e) {
        e.preventDefault();
        switchTab(id);
    };
    
    const icon = document.createElement('i');
    icon.className = `fas fa-${iconName} mr-2`;
    
    tabLink.appendChild(icon);
    tabLink.appendChild(document.createTextNode(label));
    
    tabItem.appendChild(tabLink);
    
    return tabItem;
}

/**
 * Crea los contenedores para el contenido de las pestañas
 * @returns {HTMLDivElement} - Contenedor de contenido de pestañas
 */
function createTabContentContainers() {
    const tabContents = document.createElement('div');
    tabContents.id = 'tabContents';
    
    // Pestaña de configuración
    const configTab = document.createElement('div');
    configTab.id = 'configTab';
    configTab.className = 'tab-content';
    tabContents.appendChild(configTab);
    
    // Pestaña de proyectos
    const projectsTab = document.createElement('div');
    projectsTab.id = 'projectsTab';
    projectsTab.className = 'tab-content hidden';
    
    const projectTabContent = document.createElement('div');
    projectTabContent.id = 'projectTabContent';
    
    const loadProjectsBtn = document.createElement('button');
    loadProjectsBtn.className = 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-md flex items-center mb-6';
    loadProjectsBtn.onclick = loadJiraProjects;
    
    const projectBtnIcon = document.createElement('i');
    projectBtnIcon.className = 'fas fa-sync-alt mr-2';
    
    loadProjectsBtn.appendChild(projectBtnIcon);
    loadProjectsBtn.appendChild(document.createTextNode('Cargar Proyectos'));
    projectTabContent.appendChild(loadProjectsBtn);
    
    const projectMappingSection = document.createElement('div');
    projectMappingSection.id = 'projectMappingSection';
    projectMappingSection.className = 'mt-4 hidden unloaded';
    projectTabContent.appendChild(projectMappingSection);
    
    projectsTab.appendChild(projectTabContent);
    tabContents.appendChild(projectsTab);
    
    // Pestaña de usuarios
    const usersTab = document.createElement('div');
    usersTab.id = 'usersTab';
    usersTab.className = 'tab-content hidden';
    
    const userTabContent = document.createElement('div');
    userTabContent.id = 'userTabContent';
    
    const loadUsersBtn = document.createElement('button');
    loadUsersBtn.className = 'bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white px-4 py-2 rounded-md flex items-center mb-6';
    loadUsersBtn.onclick = loadJiraUsers;
    
    const userBtnIcon = document.createElement('i');
    userBtnIcon.className = 'fas fa-sync-alt mr-2';
    
    loadUsersBtn.appendChild(userBtnIcon);
    loadUsersBtn.appendChild(document.createTextNode('Cargar Usuarios'));
    userTabContent.appendChild(loadUsersBtn);
    
    const userMappingSection = document.createElement('div');
    userMappingSection.id = 'userMappingSection';
    userMappingSection.className = 'mt-4 hidden unloaded';
    userTabContent.appendChild(userMappingSection);
    
    usersTab.appendChild(userTabContent);
    tabContents.appendChild(usersTab);
    
    // Pestaña de reportes
    const reportsTab = document.createElement('div');
    reportsTab.id = 'reportsTab';
    reportsTab.className = 'tab-content hidden';
    
    const reportsTabContent = document.createElement('div');
    reportsTabContent.id = 'reportsTabContent';
    
    const buttonsContainer = document.createElement('div');
    buttonsContainer.className = 'flex space-x-4 mb-6';
    
    const checkHealthBtn = document.createElement('button');
    checkHealthBtn.className = 'btn-gradient bg-gradient-to-r from-amber-500 to-amber-600 hover:from-amber-600 hover:to-amber-700 text-white px-4 py-2 rounded-md flex items-center';
    checkHealthBtn.id = 'check-health-btn';
    checkHealthBtn.style.backgroundImage = 'linear-gradient(to right, rgb(245, 158, 11), rgb(217, 119, 6))';
    checkHealthBtn.onclick = checkIntegrationHealth;
    
    const healthBtnIcon = document.createElement('i');
    healthBtnIcon.className = 'fas fa-heartbeat mr-2';
    
    checkHealthBtn.appendChild(healthBtnIcon);
    checkHealthBtn.appendChild(document.createTextNode('Verificar Estado'));
    buttonsContainer.appendChild(checkHealthBtn);
    
    const genReportBtn = document.createElement('button');
    genReportBtn.className = 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-4 py-2 rounded-md flex items-center';
    genReportBtn.onclick = () => generateSyncReport();
    
    const reportBtnIcon = document.createElement('i');
    reportBtnIcon.className = 'fas fa-file-alt mr-2';
    
    genReportBtn.appendChild(reportBtnIcon);
    genReportBtn.appendChild(document.createTextNode('Generar Reporte'));
    buttonsContainer.appendChild(genReportBtn);
    
    reportsTabContent.appendChild(buttonsContainer);
    
    const healthCheckSection = document.createElement('div');
    healthCheckSection.id = 'healthCheckSection';
    healthCheckSection.className = 'hidden unloaded';
    reportsTabContent.appendChild(healthCheckSection);
    
    const syncReportSection = document.createElement('div');
    syncReportSection.id = 'syncReportSection';
    syncReportSection.className = 'hidden unloaded';
    reportsTabContent.appendChild(syncReportSection);
    
    reportsTab.appendChild(reportsTabContent);
    tabContents.appendChild(reportsTab);
    
    return tabContents;
}

/**
 * Carga una plantilla HTML desde el servidor
 * @param {String} containerId - ID del contenedor donde cargar la plantilla
 * @param {String} templateName - Nombre del archivo de plantilla
 * @returns {Promise<Boolean>} - True si se cargó correctamente
 */
async function loadTemplate(containerId, templateName) {
    return TemplateLoader.loadTemplate(containerId, templateName);
}

/**
 * Configura el formulario de integración con Jira
 */
function setupJiraForm() {
    const form = document.getElementById('jiraConfigForm');
    
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                url_servidor: document.getElementById('serverUrl').value,
                api_key: document.getElementById('apiKey').value,
                usuario_jira: document.getElementById('jiraUser').value,
                frecuencia_sync: document.getElementById('syncFrequency').value
            };
            
            configurarJira(formData);
        });
    }
}

/**
 * Abre el modal de configuración Jira
 */
function openJiraModal() {
    ModalComponent.open('jiraConfigModal');
}

/**
 * Inicializa la interfaz de integración
 */
function initIntegration() {
    // Configurar pestañas de navegación
    setupIntegrationTabs();
    
    // Configurar formulario de Jira
    setupJiraForm();
    
    // Inicializar eventos para modales
    ModalComponent.initEvents();
    
    // Verificar si Jira está configurado y mostrar el panel correspondiente
    const configStatus = document.getElementById('jiraConfigStatus');
    //if (configStatus && configStatus.dataset.configured === 'true') {
    //    checkIntegrationHealth(); // Si ya está configurado, mostrar el estado de salud
    //}
    // Siempre iniciar en la pestaña de configuración
    switchTab('configTab');
}

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    initIntegration();
    
    // Conectar eventos para los botones de herramientas
    document.querySelectorAll('[data-tool]').forEach(button => {
        button.addEventListener('click', function() {
            const tool = this.getAttribute('data-tool');
            if (tool === 'jira') {
                openJiraModal();
            }
        });
    });
});