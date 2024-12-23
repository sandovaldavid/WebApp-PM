from django.contrib import admin
from .models import Tarea, Tarearecurso, Monitoreotarea

# Register your models here.

@admin.register(Tarea)
class TareaAdmin(admin.ModelAdmin):
    list_display = ('idtarea', 'nombretarea', 'fechainicio', 'fechafin', 'estado', 'prioridad', 'costoestimado', 'costoactual')
    search_fields = ('nombretarea',)
    list_filter = ('estado', 'prioridad', 'fechainicio', 'fechafin')
    ordering = ('fechainicio',)

@admin.register(Tarearecurso)
class TarearecursoAdmin(admin.ModelAdmin):
    list_display = ('id', 'idtarea', 'idrecurso', 'cantidad')
    search_fields = ('idtarea__nombretarea', 'idrecurso__nombrerecurso')
    list_filter = ('idtarea',)

@admin.register(Monitoreotarea)
class MonitoreotareaAdmin(admin.ModelAdmin):
    list_display = ('idtarea', 'fechainicioreal', 'fechafinreal', 'porcentajecompletado', 'alertagenerada', 'fechamodificacion')
    search_fields = ('idtarea__nombretarea',)
    list_filter = ('alertagenerada', 'porcentajecompletado', 'fechainicioreal', 'fechafinreal')

