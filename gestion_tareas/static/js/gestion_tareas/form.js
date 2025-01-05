function openTaskForm() {
    document.getElementById('taskForm').style.display = 'flex';
}

function closeTaskForm() {
    document.getElementById('taskForm').style.display = 'none';
}

function confirmDelete() {
    if (confirm('¿Estás seguro de que deseas eliminar esta tarea?')) {
        // Lógica para eliminar la tarea
    }
}