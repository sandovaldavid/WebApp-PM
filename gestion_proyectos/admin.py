from django.contrib import admin
from dashboard.models import Proyecto, Requerimiento, Tarea

class RequerimientoInline(admin.TabularInline):
    model = Requerimiento
    extra = 1  # Número de formularios vacíos a mostrar por defecto

class TareaInline(admin.TabularInline):
    model = Tarea
    extra = 1  # Número de formularios vacíos a mostrar por defecto

class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('idproyecto', 'nombreproyecto', 'idequipo', 'fechainicio', 'fechafin', 'presupuesto', 'estado', 'fechacreacion', 'fechamodificacion')
    list_filter = ('estado', 'fechainicio', 'idequipo')  # Filtro por estado, fecha de inicio y equipo
    search_fields = ('nombreproyecto', 'idequipo__nombreequipo')  # Búsqueda por nombre de proyecto y equipo
    inlines = [RequerimientoInline]  # Incluir los requerimientos directamente en el formulario de proyecto

class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('idrequerimiento', 'descripcion', 'idproyecto', 'fechacreacion', 'fechamodificacion')
    list_filter = ('idproyecto',)  # Filtro por proyecto
    search_fields = ('descripcion', 'idproyecto__nombreproyecto')  # Búsqueda por descripción y nombre del proyecto
    inlines = [TareaInline]  # Incluir las tareas directamente en el formulario de requerimiento

class TareaAdmin(admin.ModelAdmin):
    list_display = ('idtarea', 'nombretarea', 'idrequerimiento', 'estado', 'prioridad', 'duracionestimada', 'fechacreacion', 'fechamodificacion')
    list_filter = ('estado', 'prioridad', 'idrequerimiento')  # Filtro por estado, prioridad y requerimiento
    search_fields = ('nombretarea', 'idrequerimiento__descripcion')  # Búsqueda por nombre de tarea y descripción del requerimiento

# Registrar los modelos en el panel de administración
admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Requerimiento, RequerimientoAdmin)
