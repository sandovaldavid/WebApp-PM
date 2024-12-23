from django.contrib import admin
from .models import Tarea, TareaRecurso, MonitoreoTarea, HistorialTarea

class TareaAdmin(admin.ModelAdmin):
    list_display = ('idTarea', 'nombreTarea', 'fechaInicio', 'fechaFin', 'duracionEstimada', 'estado', 'prioridad', 'costoEstimado', 'costoActual', 'fechaCreacion', 'fechaModificacion')
    list_filter = ('estado', 'prioridad', 'fechaInicio', 'fechaFin')  # Filtro por estado, prioridad, fechas
    search_fields = ('nombreTarea', 'requerimiento__proyecto__nombreProyecto')  # Búsqueda por nombre de tarea y nombre de proyecto

class TareaRecursoAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'recurso', 'cantidad')
    search_fields = ('tarea__nombreTarea', 'recurso__nombreRecurso')  # Búsqueda por tarea y recurso

class MonitoreoTareaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'fechaInicioReal', 'fechaFinReal', 'porcentajeCompletado', 'alertaGenerada', 'fechaModificacion')
    search_fields = ('tarea__nombreTarea',)  # Búsqueda por tarea

class HistorialTareaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'fechaCambio', 'descripcionCambio')
    search_fields = ('tarea__nombreTarea', 'descripcionCambio')  # Búsqueda por tarea y descripción del cambio

# Registrar los modelos en el panel de administración
admin.site.register(Tarea, TareaAdmin)
admin.site.register(TareaRecurso, TareaRecursoAdmin)
admin.site.register(MonitoreoTarea, MonitoreoTareaAdmin)
admin.site.register(HistorialTarea, HistorialTareaAdmin)
