const toggleButton = document.getElementById("toggleSidebar");
const sidebar = document.querySelector(".sidebar");
const content = document.querySelector(".content");

toggleButton.addEventListener("click", () => {
    sidebar.classList.toggle("hidden");
    content.classList.toggle("expanded");
});

// Agregar al final del archivo o en un archivo JS separado
document.addEventListener('DOMContentLoaded', function () {
    // Obtener todas las notificaciones
    const notifications = document.querySelectorAll('.notification-message');

    // Para cada notificación
    notifications.forEach(notification => {
        // Agregar clase para fade out después de 5 segundos
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';

            // Remover el elemento después de la animación
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 5000);
    });
});