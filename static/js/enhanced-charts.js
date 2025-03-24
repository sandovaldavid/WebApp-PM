/**
 * Mejoras para las gráficas de resultados del entrenamiento
 */

document.addEventListener('DOMContentLoaded', function() {
    // Configurar botones de escala
    document.querySelectorAll('.chart-scale-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const scale = this.dataset.scale;
            const chartId = this.dataset.chart;
            
            // Actualizar botones activos
            document.querySelectorAll(`.chart-scale-btn[data-chart="${chartId}"]`).forEach(b => {
                b.classList.remove('active', 'bg-indigo-100', 'text-indigo-700');
                b.classList.add('bg-white', 'text-gray-600');
            });
            
            this.classList.add('active', 'bg-indigo-100', 'text-indigo-700');
            this.classList.remove('bg-white', 'text-gray-600');
            
            // Cambiar escala del gráfico
            changeChartScale(chartId, scale);
        });
    });
    
    // Configurar botones de descarga
    document.querySelectorAll('.chart-download-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chartId = this.dataset.chart;
            downloadChart(chartId);
        });
    });
    
    // Configurar botones de pantalla completa
    document.querySelectorAll('.chart-fullscreen-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chartId = this.dataset.chart;
            showChartFullscreen(chartId);
        });
    });
    
    // Cerrar modal
    document.getElementById('closeChartModal').addEventListener('click', function() {
        document.getElementById('chartFullscreenModal').classList.add('hidden');
    });
});

/**
 * Cambia la escala del eje Y en el gráfico
 */
function changeChartScale(chartId, scale) {
    const chart = Chart.getChart(chartId);
    if (!chart) return;
    
    chart.options.scales.y.type = scale;
    chart.update();
}

/**
 * Descarga el gráfico como imagen PNG
 */
function downloadChart(chartId) {
    const chart = Chart.getChart(chartId);
    if (!chart) return;
    
    // Crear un enlace para descargar
    const link = document.createElement('a');
    link.download = `${chartId}-${new Date().toISOString().split('T')[0]}.png`;
    link.href = chart.toBase64Image();
    link.click();
}

/**
 * Muestra el gráfico en pantalla completa
 */
function showChartFullscreen(chartId) {
    const chart = Chart.getChart(chartId);
    if (!chart) return;
    
    const modal = document.getElementById('chartFullscreenModal');
    const modalCanvas = document.getElementById('modalChart');
    const modalTitle = document.getElementById('modalChartTitle');
    
    // Establecer título según el gráfico
    if (chartId === 'lossChart') {
        modalTitle.textContent = 'Historial de Pérdida - Vista Detallada';
    } else if (chartId === 'predictionsChart') {
        modalTitle.textContent = 'Predicciones vs. Valores Reales - Vista Detallada';
    }
    
    // Mostrar modal
    modal.classList.remove('hidden');
    
    // Clonar configuración y datos
    const newChart = new Chart(modalCanvas, {
        type: chart.config.type,
        data: JSON.parse(JSON.stringify(chart.data)),
        options: JSON.parse(JSON.stringify(chart.options))
    });
    
    // Ajustar opciones para mejor visualización
    newChart.options.responsive = true;
    newChart.options.maintainAspectRatio = false;
    newChart.options.plugins.legend.position = 'top';
    
    // Si es gráfico de línea (pérdida), ajustar grosor
    if (chartId === 'lossChart') {
        newChart.data.datasets.forEach(dataset => {
            dataset.borderWidth = 3;
        });
    }
    
    newChart.update();
    
    // Guardar referencia para limpieza posterior
    modal._chartInstance = newChart;
    
    // Añadir evento para destruir el gráfico al cerrar
    const closeBtn = document.getElementById('closeChartModal');
    const closeHandler = function() {
        if (modal._chartInstance) {
            modal._chartInstance.destroy();
            modal._chartInstance = null;
        }
        closeBtn.removeEventListener('click', closeHandler);
    };
    
    closeBtn.addEventListener('click', closeHandler);
}