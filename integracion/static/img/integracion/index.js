/**
 * Gestión de la integración con Jira
 */

// Token CSRF para peticiones POST
const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;

// URLs de endpoints
const URLS = {
    configurar: '/integracion/jira/configurar/',
    listarProyectos: '/integracion/jira/proyectos/',
    mapearProyecto: '/integracion/jira/mapear-proyecto/',
    sincronizar: '/integracion/jira/sincronizar/'
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
 * Muestra una notificación en pantalla
 */
function showNotification(type, message) {
    const notificationArea = document.getElementById('notificationArea');
    
    if (!notificationArea) {
        // Crear área de notificaciones si no existe
        const notifDiv = document.createElement('div');
        notifDiv.id = 'notificationArea';
        notifDiv.className = 'fixed top-10 right-4 z-50 space-y-2';
        document.body.appendChild(notifDiv);
    }
    
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
    
    document.getElementById('notificationArea').appendChild(toast);
    
    // Eliminar después de 5 segundos
    setTimeout(() => {
        toast.classList.add('animate-fade-out');
        setTimeout(() => toast.remove(), 500);
    }, 5000);
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
    
    // Si hay configuración, cargar proyectos
    if (document.getElementById('jiraConfigStatus') && 
        document.getElementById('jiraConfigStatus').dataset.configured === 'true') {
        loadJiraProjects();
    }
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