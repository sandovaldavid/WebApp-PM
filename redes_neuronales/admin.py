from django.contrib import admin
from .models import ModeloRedNeuronal

# Register your models here.

@admin.register(ModeloRedNeuronal)
class ModeloRedNeuronalAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'proyecto', 'fecha_entrenamiento', 'accuracy')
    list_filter = ('proyecto', 'fecha_entrenamiento')
    search_fields = ('nombre', 'descripcion', 'proyecto__nombreproyecto')
    ordering = ('-fecha_entrenamiento',)
    readonly_fields = ('accuracy',)
