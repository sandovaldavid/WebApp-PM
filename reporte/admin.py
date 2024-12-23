from django.contrib import admin
from .models import Reporte, ReporteUsuario, HistorialReporte, HistorialReporteUsuario

class ReporteAdmin(admin.ModelAdmin):
    list_display = ('tipoReporte', 'fechaGeneracion', 'proyecto')
    list_filter = ('tipoReporte', 'fechaGeneracion', 'proyecto')  # Filtro por tipo de reporte, fecha de generación y proyecto
    search_fields = ('tipoReporte', 'proyecto__nombreProyecto')  # Búsqueda por tipo de reporte y nombre del proyecto

class ReporteUsuarioAdmin(admin.ModelAdmin):
    list_display = ('reporte', 'usuario', 'descripcion', 'fechaCreacion')
    list_filter = ('reporte', 'usuario')  # Filtro por reporte y usuario
    search_fields = ('usuario__nombreUsuario', 'reporte__tipoReporte')  # Búsqueda por nombre de usuario y tipo de reporte

class HistorialReporteAdmin(admin.ModelAdmin):
    list_display = ('reporte', 'fechaModificacion', 'descripcionCambio')
    search_fields = ('reporte__tipoReporte', 'descripcionCambio')  # Búsqueda por tipo de reporte y descripción del cambio

class HistorialReporteUsuarioAdmin(admin.ModelAdmin):
    list_display = ('reporteUsuario', 'cambio', 'fechaModificacion')
    search_fields = ('reporteUsuario__reporte__tipoReporte', 'cambio')  # Búsqueda por tipo de reporte y cambio

# Registrar los modelos en el panel de administración
admin.site.register(Reporte, ReporteAdmin)
admin.site.register(ReporteUsuario, ReporteUsuarioAdmin)
admin.site.register(HistorialReporte, HistorialReporteAdmin)
admin.site.register(HistorialReporteUsuario, HistorialReporteUsuarioAdmin)
