from django.contrib import admin
from .models import Notificacion, Alerta, HistorialNotificacion, HistorialAlerta

class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'mensaje', 'leido', 'fechaCreacion')
    list_filter = ('leido', 'fechaCreacion')  # Filtro por leído y fecha de creación
    search_fields = ('usuario__nombreUsuario', 'mensaje')  # Búsqueda por nombre de usuario y mensaje

class AlertaAdmin(admin.ModelAdmin):
    list_display = ('tarea', 'tipoAlerta', 'mensaje', 'activa', 'fechaCreacion')
    list_filter = ('activa', 'fechaCreacion', 'tipoAlerta')  # Filtro por activa, tipo de alerta, fecha de creación
    search_fields = ('tarea__nombreTarea', 'mensaje')  # Búsqueda por nombre de tarea y mensaje

class HistorialNotificacionAdmin(admin.ModelAdmin):
    list_display = ('notificacion', 'fechaLectura')
    search_fields = ('notificacion__mensaje',)  # Búsqueda por mensaje de la notificación

class HistorialAlertaAdmin(admin.ModelAdmin):
    list_display = ('alerta', 'fechaResolucion')
    search_fields = ('alerta__mensaje',)  # Búsqueda por mensaje de la alerta

# Registrar los modelos en el panel de administración
admin.site.register(Notificacion, NotificacionAdmin)
admin.site.register(Alerta, AlertaAdmin)
admin.site.register(HistorialNotificacion, HistorialNotificacionAdmin)
admin.site.register(HistorialAlerta, HistorialAlertaAdmin)
