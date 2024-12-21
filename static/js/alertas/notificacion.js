        // Simulación de notificación emergente
        function showNotification() {
          const notification = document.getElementById('notification');
          notification.classList.add('show');
          setTimeout(() => {
              notification.classList.remove('show');
          }, 5000);
      }

      // Llamar a la función para mostrar la notificación
      showNotification();