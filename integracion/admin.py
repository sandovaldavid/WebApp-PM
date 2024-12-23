from django.contrib import admin
from .models import IntegracionExterna

# Register your models here.

@admin.register(IntegracionExterna)
class IntegracionExternaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'url', 'token')  # Muestra estas columnas en la lista
    search_fields = ('nombre', 'descripcion')        # Habilita la búsqueda por estos campos
    list_filter = ('nombre',)                        # Agrega filtros por nombre
    ordering = ('id',)                               # Ordena por ID
