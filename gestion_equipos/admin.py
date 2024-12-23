from django.contrib import admin
from .models import Equipo, Miembro

# Register your models here.

@admin.register(Equipo)
class EquipoAdmin(admin.ModelAdmin):
    list_display = ('idequipo', 'nombreequipo', 'descripcion', 'fechacreacion', 'fechamodificacion')
    search_fields = ('nombreequipo',)
    list_filter = ('fechacreacion', 'fechamodificacion')

@admin.register(Miembro)
class MiembroAdmin(admin.ModelAdmin):
    list_display = ('idmiembro', 'idrecurso', 'idequipo')
    search_fields = ('idmiembro',)
    list_filter = ('idequipo',)
