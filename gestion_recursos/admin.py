from django.contrib import admin
from .models import Recurso, TipoRecurso, RecursoHumano, RecursoMaterial

class RecursoAdmin(admin.ModelAdmin):
    list_display = ('idRecurso', 'nombreRecurso', 'idTipoRecurso', 'disponibilidad', 'fechaCreacion', 'fechaModificacion')
    list_filter = ('idTipoRecurso', 'disponibilidad')  # Filtro por tipo de recurso y disponibilidad
    search_fields = ('nombreRecurso', 'idTipoRecurso__nameTipoRecurso')  # Búsqueda por nombre de recurso y tipo de recurso

class TipoRecursoAdmin(admin.ModelAdmin):
    list_display = ('idTipoRecurso', 'nameTipoRecurso', 'descripcion')
    search_fields = ('nameTipoRecurso',)  # Búsqueda por nombre del tipo de recurso

class RecursoHumanoAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'cargo', 'habilidades', 'tarifaHora', 'usuario')
    list_filter = ('cargo',)  # Filtro por cargo
    search_fields = ('recurso__nombreRecurso', 'cargo', 'usuario__username')  # Búsqueda por nombre del recurso y cargo

class RecursoMaterialAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'costoUnidad', 'fechaCompra')
    search_fields = ('recurso__nombreRecurso',)  # Búsqueda por nombre del recurso
    list_filter = ('fechaCompra',)  # Filtro por fecha de compra

# Registrar los modelos en el panel de administración
admin.site.register(Recurso, RecursoAdmin)
admin.site.register(TipoRecurso, TipoRecursoAdmin)
admin.site.register(RecursoHumano, RecursoHumanoAdmin)
admin.site.register(RecursoMaterial, RecursoMaterialAdmin)
