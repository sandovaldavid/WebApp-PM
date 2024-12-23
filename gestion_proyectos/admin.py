from django.contrib import admin
from .models import Proyecto, Requerimiento

# Register your models here.

@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('idproyecto', 'nombreproyecto', 'idequipo', 'fechainicio', 'fechafin', 'presupuesto', 'estado')
    search_fields = ('nombreproyecto', 'estado')
    list_filter = ('estado', 'fechainicio', 'fechafin')

@admin.register(Requerimiento)
class RequerimientoAdmin(admin.ModelAdmin):
    list_display = ('idrequerimiento', 'descripcion', 'idproyecto', 'fechacreacion', 'fechamodificacion')
    search_fields = ('descripcion',)
    list_filter = ('fechacreacion', 'fechamodificacion')
