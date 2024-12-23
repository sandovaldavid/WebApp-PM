document.addEventListener("DOMContentLoaded", function () {
    // Gráfico de Comparación
    var ctx = document.getElementById('comparison-chart').getContext('2d');
    var comparisonChart = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Tarea 1', 'Tarea 2', 'Tarea 3'],
            datasets: [{
                label: 'Estimación de Tiempo (RNN)',
                data: [20, 15, 30], // Estimaciones de tiempo por RNN
                backgroundColor: 'rgba(75, 192, 192, 0.2)',
                borderColor: 'rgba(75, 192, 192, 1)',
                borderWidth: 1
            }, {
                label: 'Tiempo Real',
                data: [22, 17, 29], // Tiempos reales
                backgroundColor: 'rgba(255, 99, 132, 0.2)',
                borderColor: 'rgba(255, 99, 132, 1)',
                borderWidth: 1
            }]
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });

    // Gráfico de Desempeño de Recursos
    var ctx2 = document.getElementById('resource-performance').getContext('2d');
    var resourcePerformanceChart = new Chart(ctx2, {
        type: 'line',
        data: {
            labels: ['Semana 1', 'Semana 2', 'Semana 3', 'Semana 4'],
            datasets: [{
                label: 'Horas Asignadas',
                data: [30, 40, 50, 60], // Horas asignadas
                borderColor: 'rgba(75, 192, 192, 1)',
                fill: false
            }]
        }
    });

    // Funciones de Exportación
    document.getElementById("export-pdf-button").addEventListener("click", function () {
        alert('Exportando a PDF');
    });

    document.getElementById("export-csv-button").addEventListener("click", function () {
        alert('Exportando a CSV');
    });
});
