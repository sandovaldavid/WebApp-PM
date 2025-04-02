/**
 * Componentes para la integración con Jira
 * Este archivo contiene funciones para crear y manipular los elementos de la UI
 * sin usar innerHTML, mejorando la seguridad y rendimiento
 */

/**
 * Componente para proyectos
 */
const ProjectComponent = {
    /**
     * Actualiza la tabla de mapeo de proyectos
     * @param {Array} jiraProjects - Proyectos de Jira
     * @param {Array} localProjects - Proyectos locales
     */
    updateProjectMapping(jiraProjects, localProjects) {
        // Actualizar contador de proyectos
        const projectCountElement = document.getElementById('project-count');
        if (projectCountElement) {
            projectCountElement.textContent = localProjects.length;
        }
        
        // Obtener la tabla donde se mostrarán los proyectos
        const tbody = document.getElementById('project-mapping-tbody');
        if (!tbody) return;
        
        // Limpiar la tabla
        tbody.innerHTML = '';
        
        // Si no hay proyectos, mostrar mensaje
        if (localProjects.length === 0) {
            const row = document.createElement('tr');
            
            const cell = document.createElement('td');
            cell.colSpan = 3;
            cell.className = 'py-8 text-center text-gray-500';
            
            const messageContainer = document.createElement('div');
            messageContainer.className = 'flex flex-col items-center';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'w-10 h-10 text-gray-300 mb-3');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4');
            
            svg.appendChild(path);
            messageContainer.appendChild(svg);
            
            const text = document.createElement('p');
            text.textContent = 'No hay proyectos disponibles';
            messageContainer.appendChild(text);
            
            cell.appendChild(messageContainer);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        // Crear filas para cada proyecto
        localProjects.forEach(localProject => {
            const mappedTo = localProject.mapped_to;
            
            const row = document.createElement('tr');
            row.className = 'border-b hover:bg-gray-50';
            
            // Celda para nombre de proyecto local
            const nameCell = document.createElement('td');
            nameCell.className = 'py-3 px-4';
            nameCell.textContent = localProject.name;
            row.appendChild(nameCell);
            
            // Celda para selector de proyecto Jira
            const selectCell = document.createElement('td');
            selectCell.className = 'py-3 px-4';
            
            const select = document.createElement('select');
            select.id = `jira-project-${localProject.id}`;
            select.className = 'form-select rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 w-full';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Seleccionar proyecto Jira';
            select.appendChild(defaultOption);
            
            // Opciones para proyectos de Jira
            jiraProjects.forEach(jiraProject => {
                const option = document.createElement('option');
                option.value = jiraProject.key;
                option.dataset.jiraId = jiraProject.id;
                option.textContent = `${jiraProject.name} (${jiraProject.key})`;
                
                if (mappedTo === jiraProject.key) {
                    option.selected = true;
                }
                
                select.appendChild(option);
            });
            
            selectCell.appendChild(select);
            row.appendChild(selectCell);
            
            // Celda para botón de acción
            const actionCell = document.createElement('td');
            actionCell.className = 'py-3 px-4';
            
            const button = document.createElement('button');
            button.className = 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1 rounded text-sm shadow hover:shadow-md transition-all duration-300';
            button.textContent = mappedTo ? 'Actualizar' : 'Mapear';
            button.onclick = () => mapProject(localProject.id);
            
            actionCell.appendChild(button);
            row.appendChild(actionCell);
            
            tbody.appendChild(row);
        });
        
        // Configurar botón de sincronización
        const syncButton = document.getElementById('sync-projects-btn');
        if (syncButton) {
            syncButton.onclick = (event) => sincronizarJira(event);
        }
    },

    /**
     * Actualiza la tabla de proyectos sincronizados
     * @param {Array} projects - Proyectos sincronizados
     */
    updateProjectsTable(projects) {
        const tbody = document.getElementById('sync-projects-tbody');
        if (!tbody) return;
        
        // Limpiar tabla
        tbody.innerHTML = '';
        
        if (projects.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.className = 'py-8 text-center text-gray-500';
            
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'flex flex-col items-center';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'w-10 h-10 text-gray-300 mb-3');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z');
            
            svg.appendChild(path);
            emptyMessage.appendChild(svg);
            
            const text = document.createElement('p');
            text.textContent = 'No hay proyectos sincronizados en este período';
            emptyMessage.appendChild(text);
            
            cell.appendChild(emptyMessage);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        // Añadir filas para cada proyecto
        projects.forEach(proyecto => {
            const row = document.createElement('tr');
            row.className = 'border-b hover:bg-gray-50';
            
            // Nombre del proyecto local
            const localNameCell = document.createElement('td');
            localNameCell.className = 'py-3 px-4';
            localNameCell.textContent = proyecto.proyecto_local.nombre;
            row.appendChild(localNameCell);
            
            // Clave del proyecto en Jira
            const jiraKeyCell = document.createElement('td');
            jiraKeyCell.className = 'py-3 px-4';
            jiraKeyCell.textContent = proyecto.proyecto_jira.key;
            row.appendChild(jiraKeyCell);
            
            // Tareas exportadas
            const exportedCell = document.createElement('td');
            exportedCell.className = 'py-3 px-4';
            exportedCell.textContent = proyecto.sincronizacion.tareas_exportadas;
            row.appendChild(exportedCell);
            
            // Issues importados
            const importedCell = document.createElement('td');
            importedCell.className = 'py-3 px-4';
            importedCell.textContent = proyecto.sincronizacion.issues_importados;
            row.appendChild(importedCell);
            
            // Porcentaje sincronizado
            const percentCell = document.createElement('td');
            percentCell.className = 'py-3 px-4';
            
            const progressContainer = document.createElement('div');
            progressContainer.className = 'w-full bg-gray-200 rounded-full h-2.5';
            
            const progressBar = document.createElement('div');
            progressBar.className = 'bg-blue-600 h-2.5 rounded-full';
            progressBar.style.width = `${proyecto.sincronizacion.porcentaje}%`;
            
            progressContainer.appendChild(progressBar);
            percentCell.appendChild(progressContainer);
            
            const percentText = document.createElement('span');
            percentText.className = 'text-xs text-gray-600';
            percentText.textContent = `${proyecto.sincronizacion.porcentaje}%`;
            percentCell.appendChild(percentText);
            
            row.appendChild(percentCell);
            tbody.appendChild(row);
        });
    },

    /**
     * Muestra un indicador de carga en la sección de proyectos
     */
    showLoader() {
        const section = document.getElementById('projectMappingSection');
        if (!section) return;

        section.classList.remove('hidden', 'unloaded');
        
        // Crear loader
        const loaderContainer = document.createElement('div');
        loaderContainer.className = 'flex justify-center my-8';
        
        const loader = document.createElement('div');
        loader.className = 'animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500';
        
        loaderContainer.appendChild(loader);
        
        // Limpiar y añadir el loader
        section.innerHTML = '';
        section.appendChild(loaderContainer);
    },

    /**
     * Muestra un mensaje de error en la sección de proyectos
     * @param {String} message - Mensaje de error
     */
    showError(message) {
        const section = document.getElementById('projectMappingSection');
        if (!section) return;
        
        // Crear contenedor de error
        const errorContainer = document.createElement('div');
        errorContainer.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4 rounded shadow-md animate-fade-in';
        
        // Mensaje de error
        const errorMessage = document.createElement('p');
        errorMessage.textContent = message || 'Error al cargar proyectos';
        errorContainer.appendChild(errorMessage);
        
        // Botón de reintentar
        const retryButton = document.createElement('button');
        retryButton.className = 'mt-2 text-sm text-blue-600 hover:underline focus:outline-none';
        retryButton.textContent = 'Reintentar';
        retryButton.onclick = () => loadJiraProjects();
        errorContainer.appendChild(retryButton);
        
        // Limpiar y añadir el mensaje de error
        section.innerHTML = '';
        section.appendChild(errorContainer);
    }
};

/**
 * Componente para usuarios
 */
const UserComponent = {
    /**
     * Actualiza la tabla de mapeo de usuarios
     * @param {Array} jiraUsers - Usuarios de Jira
     * @param {Array} localUsers - Usuarios locales
     */
    updateUserMapping(jiraUsers, localUsers) {
        // Actualizar contador de usuarios
        const userCountElement = document.getElementById('user-count');
        if (userCountElement) {
            userCountElement.textContent = localUsers.length;
        }
        
        // Obtener la tabla donde se mostrarán los usuarios
        const tbody = document.getElementById('user-mapping-tbody');
        if (!tbody) return;
        
        // Limpiar la tabla
        tbody.innerHTML = '';
        
        // Si no hay usuarios, mostrar mensaje
        if (localUsers.length === 0) {
            const row = document.createElement('tr');
            
            const cell = document.createElement('td');
            cell.colSpan = 3;
            cell.className = 'py-8 text-center text-gray-500';
            
            const messageContainer = document.createElement('div');
            messageContainer.className = 'flex flex-col items-center';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'w-10 h-10 text-gray-300 mb-3');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z');
            
            svg.appendChild(path);
            messageContainer.appendChild(svg);
            
            const text = document.createElement('p');
            text.textContent = 'No hay usuarios disponibles';
            messageContainer.appendChild(text);
            
            cell.appendChild(messageContainer);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        // Crear filas para cada usuario
        localUsers.forEach(localUser => {
            const mappedTo = localUser.mapped_to;
            
            const row = document.createElement('tr');
            row.className = 'border-b hover:bg-gray-50';
            
            // Celda para nombre de usuario local
            const nameCell = document.createElement('td');
            nameCell.className = 'py-3 px-4';
            nameCell.textContent = `${localUser.username} (${localUser.email})`;
            row.appendChild(nameCell);
            
            // Celda para selector de usuario Jira
            const selectCell = document.createElement('td');
            selectCell.className = 'py-3 px-4';
            
            const select = document.createElement('select');
            select.id = `jira-user-${localUser.id}`;
            select.className = 'form-select rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 w-full';
            
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Seleccionar usuario Jira';
            select.appendChild(defaultOption);
            
            // Opciones para usuarios de Jira
            jiraUsers.forEach(jiraUser => {
                const option = document.createElement('option');
                option.value = jiraUser.accountId;
                option.dataset.displayName = jiraUser.displayName;
                option.textContent = jiraUser.emailAddress 
                    ? `${jiraUser.displayName} (${jiraUser.emailAddress})`
                    : jiraUser.displayName;
                
                if (mappedTo && mappedTo.jira_user_id === jiraUser.accountId) {
                    option.selected = true;
                }
                
                select.appendChild(option);
            });
            
            selectCell.appendChild(select);
            row.appendChild(selectCell);
            
            // Celda para botón de acción
            const actionCell = document.createElement('td');
            actionCell.className = 'py-3 px-4';
            
            const button = document.createElement('button');
            button.className = 'bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white px-3 py-1 rounded text-sm shadow hover:shadow-md transition-all duration-300';
            button.textContent = mappedTo ? 'Actualizar' : 'Mapear';
            button.onclick = () => mapUser(localUser.id);
            
            actionCell.appendChild(button);
            row.appendChild(actionCell);
            
            tbody.appendChild(row);
        });
        
        // Configurar botones
        const autoMapButton = document.getElementById('auto-map-users-btn');
        if (autoMapButton) {
            autoMapButton.onclick = () => mapAllUsersAuto();
        }
        
        const checkHealthButton = document.getElementById('check-health-btn');
        if (checkHealthButton) {
            checkHealthButton.onclick = () => checkIntegrationHealth();
        }
        
        const cleanMappingsButton = document.getElementById('clean-mappings-btn');
        if (cleanMappingsButton) {
            cleanMappingsButton.onclick = () => cleanOrphanedMappings();
        }
    },

    /**
     * Muestra un indicador de carga en la sección de usuarios
     */
    showLoader() {
        const section = document.getElementById('userMappingSection');
        if (!section) return;

        section.classList.remove('hidden', 'unloaded');
        
        // Crear loader
        const loaderContainer = document.createElement('div');
        loaderContainer.className = 'flex justify-center my-8';
        
        const loader = document.createElement('div');
        loader.className = 'animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-500';
        
        loaderContainer.appendChild(loader);
        
        // Limpiar y añadir el loader
        section.innerHTML = '';
        section.appendChild(loaderContainer);
    },

    /**
     * Muestra un mensaje de error en la sección de usuarios
     * @param {String} message - Mensaje de error
     */
    showError(message) {
        const section = document.getElementById('userMappingSection');
        if (!section) return;
        
        // Crear contenedor de error
        const errorContainer = document.createElement('div');
        errorContainer.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4 rounded shadow-md animate-fade-in';
        
        // Mensaje de error
        const errorMessage = document.createElement('p');
        errorMessage.textContent = message || 'Error al cargar usuarios';
        errorContainer.appendChild(errorMessage);
        
        // Botón de reintentar
        const retryButton = document.createElement('button');
        retryButton.className = 'mt-2 text-sm text-blue-600 hover:underline focus:outline-none';
        retryButton.textContent = 'Reintentar';
        retryButton.onclick = () => loadJiraUsers();
        errorContainer.appendChild(retryButton);
        
        // Limpiar y añadir el mensaje de error
        section.innerHTML = '';
        section.appendChild(errorContainer);
    }
};

/**
 * Componente para estado de salud
 */
const HealthComponent = {
    /**
     * Actualiza el informe de estado de salud
     * @param {Object} report - Informe de estado
     */
    updateHealthReport(report) {
        // Estado general
        const statusColors = {
            'healthy': { bg: 'bg-green-100', text: 'text-green-800', label: 'Saludable' },
            'warning': { bg: 'bg-yellow-100', text: 'text-yellow-800', label: 'Con advertencias' },
            'error': { bg: 'bg-red-100', text: 'text-red-800', label: 'Con errores' },
            'unknown': { bg: 'bg-gray-100', text: 'text-gray-800', label: 'Desconocido' }
        };
        
        const overallStatus = report.overall_status || 'unknown';
        const statusConfig = statusColors[overallStatus];
        
        // Actualizar badge de estado
        const statusBadge = document.getElementById('health-status-badge');
        if (statusBadge) {
            statusBadge.className = `badge py-1 px-4 rounded-full text-sm font-medium ${statusConfig.bg} ${statusConfig.text}`;
            statusBadge.textContent = statusConfig.label;
        }
        
        // Actualizar secciones de estado
        this.updateStatusSection('connection-status', report.connection);
        this.updateStatusSection('mappings-status', report.mappings);
        this.updateStatusSection('sync-status', report.sync_status);
        
        // Actualizar fecha de última sincronización
        const lastSyncElement = document.getElementById('last-sync-date');
        if (lastSyncElement) {
            const lastSyncDate = report.last_sync ? 
                new Date(report.last_sync).toLocaleString() : 'Nunca';
            lastSyncElement.textContent = lastSyncDate;
        }
        
        // Configurar botones
        const reportButton = document.getElementById('generate-report-btn');
        if (reportButton) {
            reportButton.onclick = () => generateSyncReport();
        }
        
        const configButton = document.getElementById('advanced-config-btn');
        if (configButton) {
            configButton.onclick = () => openAdvancedConfigModal();
        }
    },
    
    /**
     * Actualiza una sección de estado específica
     * @param {String} elementId - ID del elemento a actualizar
     * @param {Object} status - Datos de estado
     */
    updateStatusSection(elementId, status) {
        if (!status) return;
        
        const statusColors = {
            'healthy': 'text-green-600',
            'warning': 'text-yellow-600',
            'error': 'text-red-600',
            'unknown': 'text-gray-600'
        };
        
        const section = document.getElementById(elementId);
        if (section) {
            const statusElement = section.querySelector('p');
            if (statusElement) {
                statusElement.className = `text-sm ${statusColors[status.status] || 'text-gray-600'}`;
                statusElement.textContent = status.message;
            }
            
            // Actualizar fondo según estado
            if (status.status === 'healthy') {
                section.className = 'border border-green-100 rounded-xl p-5 transition-all duration-300 bg-green-50';
            } else if (status.status === 'warning') {
                section.className = 'border border-yellow-100 rounded-xl p-5 transition-all duration-300 bg-yellow-50';
            } else if (status.status === 'error') {
                section.className = 'border border-red-100 rounded-xl p-5 transition-all duration-300 bg-red-50';
            } else {
                section.className = 'border border-gray-100 rounded-xl p-5 transition-all duration-300 bg-gray-50';
            }
        }
    },

    /**
     * Muestra un indicador de carga en la sección de salud
     */
    showLoader() {
        const section = document.getElementById('healthCheckSection');
        if (!section) return;

        section.classList.remove('hidden', 'unloaded');
        
        // Crear loader
        const loaderContainer = document.createElement('div');
        loaderContainer.className = 'flex justify-center my-8';
        
        const loader = document.createElement('div');
        loader.className = 'animate-spin rounded-full h-12 w-12 border-b-2 border-teal-500';
        
        loaderContainer.appendChild(loader);
        
        // Limpiar y añadir el loader
        section.innerHTML = '';
        section.appendChild(loaderContainer);
    },

    /**
     * Muestra un mensaje de error en la sección de salud
     * @param {String} message - Mensaje de error
     */
    showError(message) {
        const section = document.getElementById('healthCheckSection');
        if (!section) return;
        
        // Crear contenedor de error
        const errorContainer = document.createElement('div');
        errorContainer.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4 rounded shadow-md animate-fade-in';
        
        // Mensaje de error
        const errorMessage = document.createElement('p');
        errorMessage.textContent = message || 'Error al verificar estado';
        errorContainer.appendChild(errorMessage);
        
        // Botón de reintentar
        const retryButton = document.createElement('button');
        retryButton.className = 'mt-2 text-sm text-blue-600 hover:underline focus:outline-none';
        retryButton.textContent = 'Reintentar';
        retryButton.onclick = () => checkIntegrationHealth();
        errorContainer.appendChild(retryButton);
        
        // Limpiar y añadir el mensaje de error
        section.innerHTML = '';
        section.appendChild(errorContainer);
    }
};

/**
 * Componente para informes de sincronización
 */
const SyncReportComponent = {
    /**
     * Actualiza el reporte de sincronización
     * @param {Object} report - Datos del reporte
     */
    updateSyncReport(report) {
        if (!report) return;
        
        // Formatear fechas
        const formatDate = (dateString) => {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        };
        
        // Actualizar período
        document.getElementById('report-period-start').textContent = formatDate(report.periodo.inicio);
        document.getElementById('report-period-end').textContent = formatDate(report.periodo.fin);
        
        // Actualizar estadísticas
        document.getElementById('report-projects-count').textContent = report.estadisticas.proyectos_sincronizados || 0;
        document.getElementById('report-tasks-count').textContent = report.estadisticas.tareas_exportadas || 0;
        document.getElementById('report-issues-count').textContent = report.estadisticas.issues_importados || 0;
        document.getElementById('report-last-sync').textContent = formatDate(report.estadisticas.ultima_sincronizacion);
        
        // Actualizar tabla de proyectos sincronizados
        this.updateProjectsTable(report.proyectos || []);
        
        // Actualizar historial de sincronización
        this.updateSyncHistoryTable(report.historial_sincronizaciones || []);
        
        // Configurar botones de período
        document.getElementById('report-7-days-btn').onclick = () => generateSyncReport(7);
        document.getElementById('report-30-days-btn').onclick = () => generateSyncReport(30);
        document.getElementById('report-90-days-btn').onclick = () => generateSyncReport(90);
        document.getElementById('export-report-btn').onclick = () => this.exportReport(report);
    },
    
    /**
     * Actualiza la tabla de proyectos sincronizados
     * @param {Array} projects - Proyectos sincronizados
     */
    updateProjectsTable(projects) {
        const tbody = document.getElementById('sync-projects-tbody');
        if (!tbody) return;
        
        // Limpiar tabla
        tbody.innerHTML = '';
        
        if (projects.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 5;
            cell.className = 'py-8 text-center text-gray-500';
            
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'flex flex-col items-center';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'w-10 h-10 text-gray-300 mb-3');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M8 16l2.879-2.879m0 0a3 3 0 104.243-4.242 3 3 0 00-4.243 4.242zM21 12a9 9 0 11-18 0 9 9 0 0118 0z');
            
            svg.appendChild(path);
            emptyMessage.appendChild(svg);
            
            const text = document.createElement('p');
            text.textContent = 'No hay proyectos sincronizados en este período';
            emptyMessage.appendChild(text);
            
            cell.appendChild(emptyMessage);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        // Añadir filas para cada proyecto
        projects.forEach(proyecto => {
            const row = document.createElement('tr');
            row.className = 'border-b hover:bg-gray-50';
            
            // Nombre del proyecto local
            const localNameCell = document.createElement('td');
            localNameCell.className = 'py-3 px-4';
            localNameCell.textContent = proyecto.proyecto_local.nombre;
            row.appendChild(localNameCell);
            
            // Clave del proyecto en Jira
            const jiraKeyCell = document.createElement('td');
            jiraKeyCell.className = 'py-3 px-4';
            jiraKeyCell.textContent = proyecto.proyecto_jira.key;
            row.appendChild(jiraKeyCell);
            
            // Tareas exportadas
            const exportedCell = document.createElement('td');
            exportedCell.className = 'py-3 px-4';
            exportedCell.textContent = proyecto.sincronizacion.tareas_exportadas;
            row.appendChild(exportedCell);
            
            // Issues importados
            const importedCell = document.createElement('td');
            importedCell.className = 'py-3 px-4';
            importedCell.textContent = proyecto.sincronizacion.issues_importados;
            row.appendChild(importedCell);
            
            // Porcentaje sincronizado
            const percentCell = document.createElement('td');
            percentCell.className = 'py-3 px-4';
            
            const progressContainer = document.createElement('div');
            progressContainer.className = 'w-full bg-gray-200 rounded-full h-2.5';
            
            const progressBar = document.createElement('div');
            progressBar.className = 'bg-blue-600 h-2.5 rounded-full';
            progressBar.style.width = `${proyecto.sincronizacion.porcentaje}%`;
            
            progressContainer.appendChild(progressBar);
            percentCell.appendChild(progressContainer);
            
            const percentText = document.createElement('span');
            percentText.className = 'text-xs text-gray-600';
            percentText.textContent = `${proyecto.sincronizacion.porcentaje}%`;
            percentCell.appendChild(percentText);
            
            row.appendChild(percentCell);
            tbody.appendChild(row);
        });
    },

    /**
     * Actualiza la tabla de historial de sincronización
     * @param {Array} historyItems - Elementos del historial
     */
    updateSyncHistoryTable(historyItems) {
        const tbody = document.getElementById('sync-history-tbody');
        if (!tbody) return;
        
        // Limpiar tabla
        tbody.innerHTML = '';
        
        if (historyItems.length === 0) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 3;
            cell.className = 'py-8 text-center text-gray-500';
            
            const emptyMessage = document.createElement('div');
            emptyMessage.className = 'flex flex-col items-center';
            
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('class', 'w-10 h-10 text-gray-300 mb-3');
            svg.setAttribute('fill', 'none');
            svg.setAttribute('stroke', 'currentColor');
            svg.setAttribute('viewBox', '0 0 24 24');
            
            const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            path.setAttribute('stroke-width', '2');
            path.setAttribute('d', 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z');
            
            svg.appendChild(path);
            emptyMessage.appendChild(svg);
            
            const text = document.createElement('p');
            text.textContent = 'No hay registros de sincronización en este período';
            emptyMessage.appendChild(text);
            
            cell.appendChild(emptyMessage);
            row.appendChild(cell);
            tbody.appendChild(row);
            return;
        }
        
        // Formatear fechas
        const formatDate = (dateString) => {
            if (!dateString) return 'N/A';
            return new Date(dateString).toLocaleString();
        };
        
        // Añadir filas para cada elemento del historial
        historyItems.forEach(item => {
            const row = document.createElement('tr');
            row.className = 'border-b hover:bg-gray-50';
            
            // Fecha
            const dateCell = document.createElement('td');
            dateCell.className = 'py-2 px-4 text-sm';
            dateCell.textContent = formatDate(item.fecha);
            row.appendChild(dateCell);
            
            // Tipo
            const typeCell = document.createElement('td');
            typeCell.className = 'py-2 px-4 text-sm';
            typeCell.textContent = item.tipo;
            row.appendChild(typeCell);
            
            // Descripción
            const descCell = document.createElement('td');
            descCell.className = 'py-2 px-4 text-sm';
            descCell.textContent = item.descripcion;
            row.appendChild(descCell);
            
            tbody.appendChild(row);
        });
    },

    /**
     * Exporta el reporte de sincronización como CSV o PDF
     * @param {Object} report - Datos del reporte
     */
    exportReport(report) {
        if (!report) return;
        
        // Generar datos CSV
        let csvContent = "data:text/csv;charset=utf-8,";
        
        // Encabezados
        csvContent += "Reporte de Sincronización Jira\r\n";
        csvContent += `Período: ${report.periodo.inicio} - ${report.periodo.fin}\r\n\r\n`;
        csvContent += "Estadísticas Globales:\r\n";
        csvContent += `Proyectos Sincronizados,${report.estadisticas.proyectos_sincronizados}\r\n`;
        csvContent += `Tareas Exportadas,${report.estadisticas.tareas_exportadas}\r\n`;
        csvContent += `Issues Importados,${report.estadisticas.issues_importados}\r\n`;
        csvContent += `Última Sincronización,${report.estadisticas.ultima_sincronizacion}\r\n\r\n`;
        
        // Proyectos
        csvContent += "Proyectos:\r\n";
        csvContent += "Proyecto Local,Proyecto Jira,Tareas Exportadas,Issues Importados,Porcentaje\r\n";
        
        if (report.proyectos && report.proyectos.length > 0) {
            report.proyectos.forEach(p => {
                csvContent += `${p.proyecto_local.nombre},${p.proyecto_jira.key},${p.sincronizacion.tareas_exportadas},${p.sincronizacion.issues_importados},${p.sincronizacion.porcentaje}%\r\n`;
            });
        }
        
        csvContent += "\r\nHistorial:\r\n";
        csvContent += "Fecha,Tipo,Descripción\r\n";
        
        if (report.historial_sincronizaciones && report.historial_sincronizaciones.length > 0) {
            report.historial_sincronizaciones.forEach(h => {
                csvContent += `${h.fecha},${h.tipo},${h.descripcion}\r\n`;
            });
        }
        
        // Crear enlace de descarga
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", `reporte_jira_${new Date().toISOString().slice(0,10)}.csv`);
        document.body.appendChild(link);
        
        // Descargar y limpiar
        link.click();
        document.body.removeChild(link);
        
        NotificationComponent.show('success', 'Reporte exportado exitosamente');
    },
    
    /**
     * Muestra un indicador de carga en la sección de reportes
     */
    showLoader() {
        const section = document.getElementById('syncReportSection');
        if (!section) return;

        section.classList.remove('hidden', 'unloaded');
        
        // Crear loader
        const loaderContainer = document.createElement('div');
        loaderContainer.className = 'flex justify-center my-8';
        
        const loader = document.createElement('div');
        loader.className = 'animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500';
        
        loaderContainer.appendChild(loader);
        
        // Limpiar y añadir el loader
        section.innerHTML = '';
        section.appendChild(loaderContainer);
    },

    /**
     * Muestra un mensaje de error en la sección de reportes
     * @param {String} message - Mensaje de error
     */
    showError(message) {
        const section = document.getElementById('syncReportSection');
        if (!section) return;
        
        // Crear contenedor de error
        const errorContainer = document.createElement('div');
        errorContainer.className = 'bg-red-100 border-l-4 border-red-500 text-red-700 p-4 my-4 rounded shadow-md animate-fade-in';
        
        // Mensaje de error
        const errorMessage = document.createElement('p');
        errorMessage.textContent = message || 'Error al generar reporte';
        errorContainer.appendChild(errorMessage);
        
        // Botón de reintentar
        const retryButton = document.createElement('button');
        retryButton.className = 'mt-2 text-sm text-blue-600 hover:underline focus:outline-none';
        retryButton.textContent = 'Reintentar';
        retryButton.onclick = () => generateSyncReport();
        errorContainer.appendChild(retryButton);
        
        // Limpiar y añadir el mensaje de error
        section.innerHTML = '';
        section.appendChild(errorContainer);
    }
};

/**
 * Componente para notificaciones
 */
const NotificationComponent = {
    /**
     * Muestra una notificación 
     * @param {String} type - Tipo de notificación (success, error, warning)
     * @param {String} message - Mensaje a mostrar
     */
    show(type, message) {
        const notificationArea = this.getNotificationArea();
        
        // Crear notificación
        const toast = document.createElement('div');
        toast.className = `notification animate-fade-in-right ${
            type === 'success' ? 'notification-success' : 
            type === 'error' ? 'notification-error' : 
            'notification-warning'
        } px-4 py-3 rounded-md shadow-lg flex items-center max-w-xs`;
        
        // Icono según tipo
        const icon = document.createElement('i');
        icon.className = `fas fa-${
            type === 'success' ? 'check-circle' : 
            type === 'error' ? 'exclamation-circle' : 
            'exclamation-triangle'
        } mr-2`;
        toast.appendChild(icon);
        
        // Mensaje
        const text = document.createElement('span');
        text.textContent = message;
        toast.appendChild(text);
        
        // Botón para cerrar
        const closeBtn = document.createElement('button');
        closeBtn.className = 'ml-auto text-white opacity-75 hover:opacity-100';
        closeBtn.onclick = () => toast.remove();
        
        const closeIcon = document.createElement('i');
        closeIcon.className = 'fas fa-times';
        closeBtn.appendChild(closeIcon);
        
        toast.appendChild(closeBtn);
        notificationArea.appendChild(toast);
        
        // Eliminar después de 5 segundos
        setTimeout(() => {
            toast.classList.add('animate-fade-out');
            setTimeout(() => toast.remove(), 500);
        }, 5000);
    },
    
    /**
     * Obtiene o crea el área de notificaciones
     * @returns {HTMLElement} - El área de notificaciones
     */
    getNotificationArea() {
        let notifArea = document.getElementById('notificationArea');
        
        if (!notifArea) {
            notifArea = document.createElement('div');
            notifArea.id = 'notificationArea';
            notifArea.className = 'fixed top-10 right-4 z-50 space-y-2';
            document.body.appendChild(notifArea);
        }
        
        return notifArea;
    }
};

/**
 * Componente para modales
 */
const ModalComponent = {
    /**
     * Abre un modal
     * @param {String} modalId - ID del modal a abrir
     */
    open(modalId) {
        const modal = document.getElementById(modalId);
        if (modal) {
            modal.classList.remove('hidden');
            
            // Efecto de entrada
            const modalContent = modal.querySelector('div > div');
            if (modalContent) {
                modalContent.classList.add('animate-fade-in-up');
                setTimeout(() => {
                    modalContent.classList.remove('animate-fade-in-up');
                }, 500);
            }
        }
    },
    
    /**
     * Cierra todos los modales o uno específico
     * @param {String} modalId - ID del modal a cerrar (opcional)
     */
    close(modalId = null) {
        const modals = modalId ? 
            [document.getElementById(modalId)] : 
            document.querySelectorAll('.modal');
            
        modals.forEach(modal => {
            if (modal) {
                const modalContent = modal.querySelector('div > div');
                if (modalContent) {
                    modalContent.classList.add('animate-fade-out');
                    setTimeout(() => {
                        modal.classList.add('hidden');
                        modalContent.classList.remove('animate-fade-out');
                    }, 300);
                } else {
                    modal.classList.add('hidden');
                }
            }
        });
    },
    
    /**
     * Inicializa eventos para modales (cerrar con Escape o clic fuera)
     */
    initEvents() {
        // Cerrar con Escape
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.close();
            }
        });
        
        // Cerrar al hacer clic fuera
        document.querySelectorAll('.modal').forEach(modal => {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close(modal.id);
                }
            });
        });
    }
};

/**
 * Componente para carga de plantillas
 */
const TemplateLoader = {
    /**
     * Carga una plantilla HTML en un contenedor
     * @param {String} containerId - ID del contenedor donde cargar la plantilla
     * @param {String} templateName - Nombre del archivo de plantilla
     * @returns {Promise<Boolean>} - True si se cargó correctamente
     */
    async loadTemplate(containerId, templateName) {
        const container = document.getElementById(containerId);
        if (!container) return false;
        
        try {
            // Verificar si la plantilla ya está cargada
            if (container.dataset.templateLoaded === templateName) {
                return true;
            }
            
            // Mapeo de nombres de plantilla a URLs específicas
            const templateUrls = {
                'components/project_mapping.html': '/integracion/templates/project-mapping/',
                'components/user_mapping.html': '/integracion/templates/user-mapping/',
                'components/health_check.html': '/integracion/templates/health-check/',
                'components/sync_report.html': '/integracion/templates/sync-report/'
            };
            
            // Obtener la URL específica para esta plantilla
            const templateUrl = templateUrls[templateName];
            if (!templateUrl) {
                throw new Error(`No hay URL definida para la plantilla: ${templateName}`);
            }
            
            // Cargar plantilla desde la URL específica
            const response = await fetch(templateUrl);
            if (!response.ok) {
                throw new Error(`Error al cargar la plantilla ${templateName}`);
            }
            
            const html = await response.text();
            container.innerHTML = html;
            container.dataset.templateLoaded = templateName;
            container.classList.remove('unloaded');
            
            return true;
        } catch (error) {
            console.error('Error cargando plantilla:', error);
            return false;
        }
    }
};

// Exportar componentes
window.ProjectComponent = ProjectComponent;
window.UserComponent = UserComponent;
window.HealthComponent = HealthComponent;
window.SyncReportComponent = SyncReportComponent;
window.NotificationComponent = NotificationComponent;
window.ModalComponent = ModalComponent;
window.TemplateLoader = TemplateLoader;