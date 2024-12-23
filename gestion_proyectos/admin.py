from django.contrib import admin
from .models import Proyecto, Requerimiento

class RequerimientoInline(admin.TabularInline):
    model = Requerimiento
    extra = 1  # Número de formularios vacíos a mostrar por defecto

class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('idProyecto', 'nombreProyecto', 'equipo', 'fechaInicio', 'fechaFin', 'presupuesto', 'estado', 'fechaCreacion', 'fechaModificacion')
    list_filter = ('estado', 'fechaInicio', 'equipo')  # Filtro por estado, fecha de inicio y equipo
    search_fields = ('nombreProyecto', 'equipo__nombreEquipo')  # Búsqueda por nombre de proyecto y equipo
    inlines = [RequerimientoInline]  # Incluir los requerimientos directamente en el formulario de proyecto

class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('idRequerimiento', 'descripcion', 'proyecto', 'fechaCreacion', 'fechaModificacion')
    list_filter = ('proyecto',)  # Filtro por proyecto
    search_fields = ('descripcion', 'proyecto__nombreProyecto')  # Búsqueda por descripción y nombre del proyecto

# Registrar los modelos en el panel de administración
admin.site.register(Proyecto, ProyectoAdmin)
admin.site.register(Requerimiento, RequerimientoAdmin)
