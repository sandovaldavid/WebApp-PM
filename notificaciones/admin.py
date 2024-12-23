from django.contrib import admin
from .models import Notificacion

# Register your models here.

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'mensaje_resumido', 'fecha_creacion', 'leido')
    list_filter = ('leido', 'fecha_creacion')
    search_fields = ('usuario__username', 'mensaje')
    ordering = ('-fecha_creacion',)
    list_editable = ('leido',)

    def mensaje_resumido(self, obj):
        return obj.mensaje[:50] + ('...' if len(obj.mensaje) > 50 else '')
    mensaje_resumido.short_description = 'Mensaje'
