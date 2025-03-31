/**
 * Gestión de la integración con Jira
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
    reporteSincronizacion: '/integracion/jira/reporte-sincronizacion/'
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
        showNotification('success', 'Configuración guardada correctamente');
        
        // Cerrar modal y actualizar interfaz
        closeModal();
        
        // Mostrar panel de mapeo de proyectos
        loadJiraProjects();
        
        return data;
    } catch (error) {
        showNotification('error', error.message);
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
        
        showNotification('success', 'Configuración avanzada actualizada correctamente');
        closeModal();
        
        return data;
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Carga los proyectos de Jira y locales para mapeo
 */
async function loadJiraProjects() {
    try {
        // Mostrar indicador de carga
        document.getElementById('projectMappingSection').innerHTML = '<div class="flex justify-center my-8"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>';
        
        const response = await fetch(URLS.listarProyectos);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al obtener proyectos');
        }
        
        // Mostrar panel de mapeo
        document.getElementById('projectMappingSection').classList.remove('hidden');
        renderProjectMapping(data.jira_projects, data.local_projects);
        
    } catch (error) {
        document.getElementById('projectMappingSection').innerHTML = `
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4">
                <p>${error.message || 'Error al cargar proyectos'}</p>
                <button onclick="loadJiraProjects()" class="mt-2 text-sm text-blue-600 hover:underline">Reintentar</button>
            </div>
        `;
        console.error('Error:', error);
    }
}

/**
 * Renderiza la interfaz de mapeo de proyectos
 */
function renderProjectMapping(jiraProjects, localProjects) {
    const container = document.getElementById('projectMappingSection');
    
    // Construir HTML para la tabla de mapeos
    let html = `
        <div class="bg-white shadow-md rounded-lg p-6 my-6">
            <h2 class="text-xl font-semibold mb-4">Mapeo de Proyectos</h2>
            <p class="text-gray-600 mb-4">Selecciona qué proyectos de Jira corresponden a tus proyectos locales.</p>
            
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="py-3 px-4 text-left">Proyecto Local</th>
                            <th class="py-3 px-4 text-left">Proyecto Jira</th>
                            <th class="py-3 px-4 text-left">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Generar filas para cada proyecto local
    localProjects.forEach(localProject => {
        const mappedTo = localProject.mapped_to;
        const mappedProject = mappedTo ? 
            jiraProjects.find(p => p.key === mappedTo) : null;
        
        html += `
            <tr class="border-b hover:bg-gray-50">
                <td class="py-3 px-4">${localProject.name}</td>
                <td class="py-3 px-4">
                    <select id="jira-project-${localProject.id}" class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option value="">Seleccionar proyecto Jira</option>
                        ${jiraProjects.map(jiraProject => `
                            <option value="${jiraProject.key}" 
                                data-jira-id="${jiraProject.id}"
                                ${mappedTo === jiraProject.key ? 'selected' : ''}>
                                ${jiraProject.name} (${jiraProject.key})
                            </option>
                        `).join('')}
                    </select>
                </td>
                <td class="py-3 px-4">
                    <button onclick="mapProject(${localProject.id})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                        ${mappedTo ? 'Actualizar' : 'Mapear'}
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
            
            <div class="mt-6 flex justify-end">
                <button onclick="sincronizarJira(event)" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-md flex items-center">
                    <i class="fas fa-sync-alt mr-2"></i> Sincronizar Ahora
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Mapea un proyecto local con uno de Jira
 */
async function mapProject(localProjectId) {
    const selectElement = document.getElementById(`jira-project-${localProjectId}`);
    const jiraProjectKey = selectElement.value;
    
    if (!jiraProjectKey) {
        showNotification('warning', 'Selecciona un proyecto de Jira');
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
        
        showNotification('success', 'Proyecto mapeado correctamente');
        
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Inicia la sincronización con Jira
 */
async function sincronizarJira(event) {
    try {
        // Obtener el botón de forma más segura
        const sincButton = event ? 
            (event.target.tagName === 'BUTTON' ? event.target : event.target.closest('button')) :
            document.querySelector('button[onclick="sincronizarJira()"]');
            
        sincButton.disabled = true;
        sincButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Sincronizando...';
        
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
        
        showNotification('success', 'Sincronización completada correctamente');
        
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
    } finally {
        // Restaurar botón
        sincButton.disabled = false;
        sincButton.innerHTML = '<i class="fas fa-sync-alt mr-2"></i> Sincronizar Ahora';
    }
}


/**
 * Carga usuarios de Jira y usuarios locales para mapeo
 */
async function loadJiraUsers() {
    try {
        // Mostrar indicador de carga
        document.getElementById('userMappingSection').innerHTML = '<div class="flex justify-center my-8"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>';
        
        const response = await fetch(URLS.listarUsuarios);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al obtener usuarios');
        }
        
        // Mostrar panel de mapeo de usuarios
        document.getElementById('userMappingSection').classList.remove('hidden');
        renderUserMapping(data.jira_users, data.local_users);
        
    } catch (error) {
        document.getElementById('userMappingSection').innerHTML = `
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4">
                <p>${error.message || 'Error al cargar usuarios'}</p>
                <button onclick="loadJiraUsers()" class="mt-2 text-sm text-blue-600 hover:underline">Reintentar</button>
            </div>
        `;
        console.error('Error:', error);
    }
}

/**
 * Renderiza la interfaz de mapeo de usuarios
 */
function renderUserMapping(jiraUsers, localUsers) {
    const container = document.getElementById('userMappingSection');
    
    // Construir HTML para la tabla de mapeos
    let html = `
        <div class="bg-white shadow-md rounded-lg p-6 my-6">
            <h2 class="text-xl font-semibold mb-4">Mapeo de Usuarios</h2>
            <p class="text-gray-600 mb-4">Selecciona qué usuarios de Jira corresponden a tus usuarios locales.</p>
            
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="py-3 px-4 text-left">Usuario Local</th>
                            <th class="py-3 px-4 text-left">Usuario Jira</th>
                            <th class="py-3 px-4 text-left">Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Generar filas para cada usuario local
    localUsers.forEach(localUser => {
        const mappedTo = localUser.mapped_to;
        
        html += `
            <tr class="border-b hover:bg-gray-50">
                <td class="py-3 px-4">${localUser.username} (${localUser.email})</td>
                <td class="py-3 px-4">
                    <select id="jira-user-${localUser.id}" class="form-select rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500">
                        <option value="">Seleccionar usuario Jira</option>
                        ${jiraUsers.map(jiraUser => `
                            <option value="${jiraUser.accountId}" 
                                data-display-name="${jiraUser.displayName}"
                                ${mappedTo && mappedTo.jira_user_id === jiraUser.accountId ? 'selected' : ''}>
                                ${jiraUser.displayName} ${jiraUser.emailAddress ? `(${jiraUser.emailAddress})` : ''}
                            </option>
                        `).join('')}
                    </select>
                </td>
                <td class="py-3 px-4">
                    <button onclick="mapUser(${localUser.id})" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">
                        ${mappedTo ? 'Actualizar' : 'Mapear'}
                    </button>
                </td>
            </tr>
        `;
    });
    
    html += `
                    </tbody>
                </table>
            </div>
            
            <div class="mt-6 flex justify-between">
                <button onclick="mapAllUsersAuto()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center">
                    <i class="fas fa-user-plus mr-2"></i> Mapeo Automático
                </button>
                <div class="flex space-x-3">
                    <button onclick="checkIntegrationHealth()" class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-md flex items-center">
                        <i class="fas fa-heartbeat mr-2"></i> Verificar Estado
                    </button>
                    <button onclick="cleanOrphanedMappings()" class="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-md flex items-center">
                        <i class="fas fa-broom mr-2"></i> Limpiar Mapeos
                    </button>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Mapea un usuario local con uno de Jira
 */
async function mapUser(localUserId) {
    const selectElement = document.getElementById(`jira-user-${localUserId}`);
    const jiraUserId = selectElement.value;
    
    if (!jiraUserId) {
        showNotification('warning', 'Selecciona un usuario de Jira');
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
        
        showNotification('success', 'Usuario mapeado correctamente');
        
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Inicia el mapeo automático de usuarios por correo electrónico
 */
async function mapAllUsersAuto() {
    try {
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
        
        showNotification('success', data.message || 'Mapeo automático completado');
        
        // Recargar la lista de usuarios para mostrar los nuevos mapeos
        loadJiraUsers();
        
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
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
        
        showNotification('success', `Limpieza completada. Se eliminaron ${data.total_cleaned} mapeos huérfanos.`);
        
    } catch (error) {
        showNotification('error', error.message);
        console.error('Error:', error);
    }
}

/**
 * Comprueba el estado de salud de la integración con Jira
 */
async function checkIntegrationHealth() {
    try {
        // Mostrar indicador de carga
        const healthSection = document.getElementById('healthCheckSection') || 
            createSection('healthCheckSection', 'Estado de la Integración');
            
        healthSection.innerHTML = '<div class="flex justify-center my-8"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>';
        healthSection.classList.remove('hidden');
        
        const response = await fetch(URLS.estadoSalud);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al verificar estado');
        }
        
        renderHealthReport(data.health_report);
        
    } catch (error) {
        document.getElementById('healthCheckSection').innerHTML = `
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4">
                <p>${error.message || 'Error al verificar estado'}</p>
                <button onclick="checkIntegrationHealth()" class="mt-2 text-sm text-blue-600 hover:underline">Reintentar</button>
            </div>
        `;
        console.error('Error:', error);
    }
}

/**
 * Renderiza el informe de estado de salud
 */
function renderHealthReport(report) {
    const container = document.getElementById('healthCheckSection');
    
    // Determinar color para el estado general
    const statusColors = {
        'healthy': 'green',
        'warning': 'yellow',
        'error': 'red',
        'unknown': 'gray'
    };
    
    const overallColor = statusColors[report.overall_status] || 'gray';
    
    // Formatear fecha de última sincronización
    const lastSyncDate = report.last_sync ? 
        new Date(report.last_sync).toLocaleString() : 
        'Nunca';
    
    // Construir HTML para el informe
    let html = `
        <div class="bg-white shadow-md rounded-lg p-6 my-6">
            <div class="flex justify-between items-center mb-6">
                <h2 class="text-xl font-semibold">Estado de la Integración</h2>
                <span class="px-3 py-1 rounded-full text-white bg-${overallColor}-500">
                    ${report.overall_status === 'healthy' ? 'Saludable' : 
                      report.overall_status === 'warning' ? 'Con advertencias' : 
                      report.overall_status === 'error' ? 'Con errores' : 'Desconocido'}
                </span>
            </div>
            
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div class="border rounded-lg p-4">
                    <h3 class="font-medium mb-2 text-gray-700">Conexión</h3>
                    <p class="text-${statusColors[report.connection.status]}-600">
                        ${report.connection.message}
                    </p>
                </div>
                
                <div class="border rounded-lg p-4">
                    <h3 class="font-medium mb-2 text-gray-700">Mapeos</h3>
                    <p class="text-${statusColors[report.mappings.status]}-600">
                        ${report.mappings.message}
                    </p>
                </div>
                
                <div class="border rounded-lg p-4">
                    <h3 class="font-medium mb-2 text-gray-700">Estado Sincronización</h3>
                    <p class="text-${statusColors[report.sync_status.status]}-600">
                        ${report.sync_status.message}
                    </p>
                </div>
            </div>
            
            <div class="border-t pt-4">
                <p><strong>Última sincronización:</strong> ${lastSyncDate}</p>
                <div class="mt-4 flex justify-between">
                    <button onclick="generateSyncReport()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md">
                        <i class="fas fa-file-alt mr-2"></i> Generar Reporte Completo
                    </button>
                    <button onclick="openAdvancedConfigModal()" class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded-md">
                        <i class="fas fa-cog mr-2"></i> Configuración Avanzada
                    </button>
                </div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Genera y muestra un reporte completo de sincronización
 */
async function generateSyncReport(days = 30) {
    try {
        // Mostrar indicador de carga
        const reportSection = document.getElementById('syncReportSection') ||
            createSection('syncReportSection', 'Reporte de Sincronización');
            
        reportSection.innerHTML = '<div class="flex justify-center my-8"><div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div></div>';
        reportSection.classList.remove('hidden');
        
        const response = await fetch(`${URLS.reporteSincronizacion}?days=${days}`);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.message || 'Error al generar reporte');
        }
        
        renderSyncReport(data.report);
        
    } catch (error) {
        document.getElementById('syncReportSection').innerHTML = `
            <div class="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4">
                <p>${error.message || 'Error al generar reporte'}</p>
                <button onclick="generateSyncReport()" class="mt-2 text-sm text-blue-600 hover:underline">Reintentar</button>
            </div>
        `;
        console.error('Error:', error);
    }
}

/**
 * Renderiza el reporte de sincronización
 */
function renderSyncReport(report) {
    const container = document.getElementById('syncReportSection');
    
    // Formatear fechas
    const formatDate = (dateString) => {
        if (!dateString) return 'N/A';
        return new Date(dateString).toLocaleString();
    };
    
    // Construir HTML del reporte
    let html = `
        <div class="bg-white shadow-md rounded-lg p-6 my-6">
            <h2 class="text-xl font-semibold mb-2">Reporte de Sincronización</h2>
            <p class="text-gray-600 mb-4">Período: ${formatDate(report.periodo.inicio)} - ${formatDate(report.periodo.fin)}</p>
            
            <div class="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
                <div class="bg-blue-50 border border-blue-200 rounded-lg p-4 text-center">
                    <h3 class="text-lg font-medium text-blue-800">Proyectos</h3>
                    <p class="text-2xl font-bold">${report.estadisticas.proyectos_sincronizados}</p>
                </div>
                
                <div class="bg-green-50 border border-green-200 rounded-lg p-4 text-center">
                    <h3 class="text-lg font-medium text-green-800">Tareas Exportadas</h3>
                    <p class="text-2xl font-bold">${report.estadisticas.tareas_exportadas}</p>
                </div>
                
                <div class="bg-purple-50 border border-purple-200 rounded-lg p-4 text-center">
                    <h3 class="text-lg font-medium text-purple-800">Issues Importados</h3>
                    <p class="text-2xl font-bold">${report.estadisticas.issues_importados}</p>
                </div>
                
                <div class="bg-gray-50 border border-gray-200 rounded-lg p-4 text-center">
                    <h3 class="text-lg font-medium text-gray-800">Última Sincronización</h3>
                    <p class="text-gray-600">${formatDate(report.estadisticas.ultima_sincronizacion)}</p>
                </div>
            </div>
            
            <h3 class="text-lg font-semibold mt-6 mb-3 border-b pb-2">Proyectos Sincronizados</h3>
            
            <div class="overflow-x-auto">
                <table class="min-w-full bg-white">
                    <thead>
                        <tr class="bg-gray-100">
                            <th class="py-3 px-4 text-left">Proyecto Local</th>
                            <th class="py-3 px-4 text-left">Proyecto Jira</th>
                            <th class="py-3 px-4 text-left">Tareas Exportadas</th>
                            <th class="py-3 px-4 text-left">Issues Importados</th>
                            <th class="py-3 px-4 text-left">% Sincronizado</th>
                        </tr>
                    </thead>
                    <tbody>
    `;
    
    // Añadir filas para cada proyecto
    if (report.proyectos && report.proyectos.length > 0) {
        report.proyectos.forEach(proyecto => {
            html += `
                <tr class="border-b hover:bg-gray-50">
                    <td class="py-3 px-4">${proyecto.proyecto_local.nombre}</td>
                    <td class="py-3 px-4">${proyecto.proyecto_jira.key}</td>
                    <td class="py-3 px-4">${proyecto.sincronizacion.tareas_exportadas}</td>
                    <td class="py-3 px-4">${proyecto.sincronizacion.issues_importados}</td>
                    <td class="py-3 px-4">
                        <div class="w-full bg-gray-200 rounded-full h-2.5">
                            <div class="bg-blue-600 h-2.5 rounded-full" style="width: ${proyecto.sincronizacion.porcentaje}%"></div>
                        </div>
                        <span class="text-xs text-gray-600">${proyecto.sincronizacion.porcentaje}%</span>
                    </td>
                </tr>
            `;
        });
    } else {
        html += `
            <tr>
                <td colspan="5" class="py-4 px-4 text-center text-gray-500">No hay proyectos sincronizados en este período</td>
            </tr>
        `;
    }
    
    html += `
                    </tbody>
                </table>
            </div>
            
            <h3 class="text-lg font-semibold mt-6 mb-3 border-b pb-2">Historial de Sincronizaciones</h3>
    `;
    
    // Añadir historial de sincronizaciones si existe
    if (report.historial_sincronizaciones && report.historial_sincronizaciones.length > 0) {
        html += `
            <div class="overflow-y-auto max-h-64 border rounded-lg">
                <table class="min-w-full bg-white">
                    <thead class="sticky top-0 bg-white shadow-sm">
                        <tr class="bg-gray-50">
                            <th class="py-2 px-4 text-left">Fecha</th>
                            <th class="py-2 px-4 text-left">Tipo</th>
                            <th class="py-2 px-4 text-left">Descripción</th>
                        </tr>
                    </thead>
                    <tbody>
        `;
        
        report.historial_sincronizaciones.forEach(item => {
            html += `
                <tr class="border-b hover:bg-gray-50">
                    <td class="py-2 px-4 text-sm">${formatDate(item.fecha)}</td>
                    <td class="py-2 px-4 text-sm">${item.tipo}</td>
                    <td class="py-2 px-4 text-sm">${item.descripcion}</td>
                </tr>
            `;
        });
        
        html += `
                    </tbody>
                </table>
            </div>
        `;
    } else {
        html += `
            <div class="text-center py-8 text-gray-500">
                No hay registros de sincronización en este período
            </div>
        `;
    }
    
    html += `
            <div class="mt-6 flex justify-between">
                <button onclick="generateSyncReport(7)" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm">
                    Últimos 7 días
                </button>
                <button onclick="generateSyncReport(30)" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm">
                    Últimos 30 días
                </button>
                <button onclick="generateSyncReport(90)" class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded-md text-sm">
                    Últimos 90 días
                </button>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

/**
 * Crea una nueva sección en la interfaz
 */
function createSection(id, title) {
    const mainContainer = document.querySelector('.p-8.space-y-8');
    
    const section = document.createElement('div');
    section.id = id;
    section.className = 'mt-8';
    section.innerHTML = `<h2 class="text-xl font-semibold mb-4">${title}</h2>`;
    
    mainContainer.appendChild(section);
    
    return section;
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
        
        modal.innerHTML = `
            <div class="relative top-20 mx-auto p-5 border w-full max-w-md shadow-lg rounded-md bg-white">
                <div class="mt-3">
                    <div class="flex justify-between items-center pb-3 border-b">
                        <h3 class="text-lg font-medium text-gray-900 flex items-center">
                            <i class="fas fa-cogs mr-2 text-blue-500"></i>
                            Configuración Avanzada de Jira
                        </h3>
                        <button type="button" onclick="closeModal()" class="text-gray-400 hover:text-gray-500">
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
                            <button type="button" onclick="closeModal()" class="px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors">
                                Cancelar
                            </button>
                            <button type="submit" class="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 transition-colors">
                                <i class="fas fa-save mr-1"></i> Guardar Configuración
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        `;
        
        document.body.appendChild(modal);
        
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
    document.getElementById('advancedConfigModal').classList.remove('hidden');
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
        
        tabsContainer.innerHTML = `
            <ul class="flex flex-wrap -mb-px text-sm font-medium text-center">
                <li class="mr-2">
                    <a href="#" onclick="switchTab('configTab')" id="configTabBtn" class="inline-block p-4 rounded-t-lg border-b-2 border-blue-500 text-blue-600 active">
                        <i class="fas fa-cog mr-2"></i>Configuración
                    </a>
                </li>
                <li class="mr-2">
                    <a href="#" onclick="switchTab('projectsTab')" id="projectsTabBtn" class="inline-block p-4 rounded-t-lg border-b-2 border-transparent hover:border-gray-300 text-gray-500 hover:text-gray-600">
                        <i class="fas fa-project-diagram mr-2"></i>Proyectos
                    </a>
                </li>
                <li class="mr-2">
                    <a href="#" onclick="switchTab('usersTab')" id="usersTabBtn" class="inline-block p-4 rounded-t-lg border-b-2 border-transparent hover:border-gray-300 text-gray-500 hover:text-gray-600">
                        <i class="fas fa-users mr-2"></i>Usuarios
                    </a>
                </li>
                <li class="mr-2">
                    <a href="#" onclick="switchTab('reportsTab')" id="reportsTabBtn" class="inline-block p-4 rounded-t-lg border-b-2 border-transparent hover:border-gray-300 text-gray-500 hover:text-gray-600">
                        <i class="fas fa-chart-bar mr-2"></i>Reportes
                    </a>
                </li>
            </ul>
        `;
        
        // Insertar al principio del contenedor principal
        container.insertBefore(tabsContainer, container.firstChild);
        
        // Crear contenedores de contenido para cada pestaña
        const contentContainers = document.createElement('div');
        contentContainers.id = 'tabContents';
        
        contentContainers.innerHTML = `
            <div id="configTab" class="tab-content">
                <!-- El contenido de configuración (tarjetas de herramientas) se mostrará aquí -->
            </div>
            <div id="projectsTab" class="tab-content hidden">
                <div id="projectTabContent">
                    <button onclick="loadJiraProjects()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center mb-6">
                        <i class="fas fa-sync-alt mr-2"></i> Cargar Proyectos
                    </button>
                    <div id="projectMappingSection" class="mt-4">
                        <!-- El contenido de mapeo de proyectos se mostrará aquí -->
                    </div>
                </div>
            </div>
            <div id="usersTab" class="tab-content hidden">
                <div id="userTabContent">
                    <button onclick="loadJiraUsers()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center mb-6">
                        <i class="fas fa-sync-alt mr-2"></i> Cargar Usuarios
                    </button>
                    <div id="userMappingSection" class="mt-4">
                        <!-- El contenido de mapeo de usuarios se mostrará aquí -->
                    </div>
                </div>
            </div>
            <div id="reportsTab" class="tab-content hidden">
                <div id="reportsTabContent">
                    <div class="flex space-x-4 mb-6">
                        <button onclick="checkIntegrationHealth()" class="bg-yellow-500 hover:bg-yellow-600 text-white px-4 py-2 rounded-md flex items-center">
                            <i class="fas fa-heartbeat mr-2"></i> Verificar Estado
                        </button>
                        <button onclick="generateSyncReport()" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-md flex items-center">
                            <i class="fas fa-file-alt mr-2"></i> Generar Reporte
                        </button>
                    </div>
                    <div id="healthCheckSection" class="hidden"></div>
                    <div id="syncReportSection" class="hidden"></div>
                </div>
            </div>
        `;
        
        container.appendChild(contentContainers);
        
        // Mover contenido existente a la pestaña de configuración
        const configTab = document.getElementById('configTab');
        const tools = document.querySelector('.grid.grid-cols-1.md\\:grid-cols-3.gap-6');
        
        if (tools && configTab) {
            configTab.appendChild(tools);
        }
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
    document.getElementById(tabId).classList.remove('hidden');
    
    // Actualizar estado de los botones de pestañas
    document.querySelectorAll('#integrationTabs a').forEach(btn => {
        btn.classList.remove('border-blue-500', 'text-blue-600');
        btn.classList.add('border-transparent', 'text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
    });
    
    // Marcar el botón activo
    document.getElementById(tabId + 'Btn').classList.remove('border-transparent', 'text-gray-500', 'hover:text-gray-600', 'hover:border-gray-300');
    document.getElementById(tabId + 'Btn').classList.add('border-blue-500', 'text-blue-600');
}

/**
 * Muestra una notificación en pantalla
 */
function showNotification(type, message) {
    const notificationArea = document.getElementById('notificationArea') || createNotificationArea();
    
    // Crear notificación
    const toast = document.createElement('div');
    toast.className = `px-4 py-3 rounded-md shadow-lg flex items-center max-w-xs animate-fade-in-right ${
        type === 'success' ? 'bg-green-500 text-white' : 
        type === 'error' ? 'bg-red-500 text-white' : 
        'bg-yellow-500 text-white'
    }`;
    
    const icon = type === 'success' ? 'check-circle' : 
               type === 'error' ? 'exclamation-circle' : 'exclamation-triangle';
    
    toast.innerHTML = `
        <i class="fas fa-${icon} mr-2"></i>
        <span>${message}</span>
        <button class="ml-auto text-white opacity-75 hover:opacity-100" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    notificationArea.appendChild(toast);
    
    // Eliminar después de 5 segundos
    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
}

/**
 * Crea el área de notificaciones si no existe
 */
function createNotificationArea() {
    const notifDiv = document.createElement('div');
    notifDiv.id = 'notificationArea';
    notifDiv.className = 'fixed top-10 right-4 z-50 space-y-2';
    document.body.appendChild(notifDiv);
    return notifDiv;
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

// Inicializar cuando se carga la página
document.addEventListener('DOMContentLoaded', function() {
    setupJiraForm();
    setupIntegrationTabs();
    
    // Si hay configuración, cargar proyectos
    if (document.getElementById('jiraConfigStatus') && 
        document.getElementById('jiraConfigStatus').dataset.configured === 'true') {
        loadJiraProjects();
    }
    
    // Cerrar modales con Escape
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
    
    // Cerrar modales al hacer clic fuera
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                closeModal();
            }
        });
    });
});

// Funciones para manejar modales
function openJiraModal() {
    document.getElementById('jiraConfigModal').classList.remove('hidden');
}

function closeModal() {
    document.querySelectorAll('.modal').forEach(modal => {
        modal.classList.add('hidden');
    });
}
