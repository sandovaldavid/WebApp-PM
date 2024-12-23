from django.contrib import admin
from .models import Recurso, TipoRecurso, RecursoHumano, RecursoMaterial

# Register your models here.

@admin.register(Recurso)
class RecursoAdmin(admin.ModelAdmin):
    list_display = ('idrecurso', 'nombrerecurso', 'idtiporecurso', 'disponibilidad', 'fechacreacion', 'fechamodificacion')
    search_fields = ('nombrerecurso',)
    list_filter = ('disponibilidad', 'fechacreacion')

@admin.register(TipoRecurso)
class TipoRecursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_tipo_recurso', 'descripcion')
    search_fields = ('nombre_tipo_recurso',)

@admin.register(RecursoHumano)
class RecursoHumanoAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'cargo', 'usuario', 'tarifa_hora')
    search_fields = ('cargo', 'usuario__username')
    list_filter = ('cargo',)

@admin.register(RecursoMaterial)
class RecursoMaterialAdmin(admin.ModelAdmin):
    list_display = ('recurso', 'costo_unidad', 'fecha_compra')
    search_fields = ('recurso__nombrerecurso',)
    list_filter = ('fecha_compra',)
