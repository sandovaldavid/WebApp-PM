const toggleButton = document.getElementById("toggleSidebar");
const sidebar = document.querySelector(".sidebar");
const content = document.querySelector(".content");

if (toggleButton) { // Verificar que el elemento existe
    toggleButton.addEventListener("click", () => {
        sidebar.classList.toggle("hidden");
        content.classList.toggle("expanded");
    });
}

// Código para manejar notificaciones y otras funcionalidades
document.addEventListener('DOMContentLoaded', function () {
    // Código para manejar notificaciones
    const notifications = document.querySelectorAll('.notification-message');
    
    // Para cada notificación, configurar la animación de desaparición
    notifications.forEach(notification => {
        setTimeout(() => {
            notification.style.opacity = '0';
            notification.style.transform = 'translateX(100%)';
            
            setTimeout(() => {
                if (notification && notification.parentElement) {
                    notification.remove();
                }
            }, 300);
        }, 5000);
    });
    
    // Verificamos si hay notificaciones y registramos en consola para debugging
    if (notifications.length > 0) {
        console.log(`${notifications.length} notificaciones inicializadas`);
    }

    // Iniciar con el estado correcto de la barra lateral al cargar la página
    document.addEventListener('alpine:init', () => {
        // Este evento se dispara cuando Alpine está inicializado
        // Se maneja directamente en el HTML con localStorage
        console.log('Alpine initialized, sidebar state loaded from localStorage');
    });
});

// Agregar función para mejorar el rendimiento de carga
window.addEventListener('load', function() {
    // Aplicar lazy loading a imágenes que no son críticas
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    if ('loading' in HTMLImageElement.prototype) {
        console.log('Browser supports native lazy loading');
    } else {
        // Fallback para navegadores que no soportan lazy loading nativo
        lazyImages.forEach(img => {
            const src = img.getAttribute('data-src');
            if (src) {
                img.src = src;
            }
        });
    }
});