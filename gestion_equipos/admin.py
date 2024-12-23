from django.contrib import admin
from .models import Equipo, Miembro

class MiembroInline(admin.TabularInline):
    model = Miembro
    extra = 1  # Número de formularios vacíos a mostrar por defecto

class EquipoAdmin(admin.ModelAdmin):
    list_display = ('idEquipo', 'nombreEquipo', 'descripcion', 'fechaCreacion', 'fechaModificacion')
    list_filter = ('fechaCreacion',)  # Filtro por fecha de creación
    search_fields = ('nombreEquipo',)  # Búsqueda por nombre de equipo
    inlines = [MiembroInline]  # Incluir los miembros directamente en el formulario de equipo

class MiembroAdmin(admin.ModelAdmin):
    list_display = ('idMiembro', 'recurso', 'equipo')
    list_filter = ('equipo',)  # Filtro por equipo
    search_fields = ('recurso__nombreRecurso', 'equipo__nombreEquipo')  # Búsqueda por recurso o equipo

# Registrar los modelos en el panel de administración
admin.site.register(Equipo, EquipoAdmin)
admin.site.register(Miembro, MiembroAdmin)
