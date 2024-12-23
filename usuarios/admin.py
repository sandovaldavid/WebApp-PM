from django.contrib import admin
from .models import Usuario, RolModuloAcceso, UsuarioRolModulo, Administrador, Desarrollador, JefeProyecto, Cliente, Tester

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'fecha_creacion', 'fecha_modificacion')
    list_filter = ('rol', 'fecha_creacion')  # Filtro por rol y fecha de creación
    search_fields = ('username', 'email')  # Búsqueda por nombre de usuario y correo electrónico

class RolModuloAccesoAdmin(admin.ModelAdmin):
    list_display = ('nombreRol', 'modulo', 'permisos')
    list_filter = ('nombreRol', 'permisos')  # Filtro por nombre del rol y permisos
    search_fields = ('nombreRol', 'modulo')  # Búsqueda por nombre del rol y módulo

class UsuarioRolModuloAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol_modulo')
    search_fields = ('usuario__username', 'rol_modulo__nombreRol')  # Búsqueda por usuario y nombre del rol

class AdministradorAdmin(admin.ModelAdmin):
    list_display = ('usuario',)
    search_fields = ('usuario__username',)  # Búsqueda por nombre de usuario

class DesarrolladorAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tareasCompletadas', 'tiempoTotalEmpleado')
    search_fields = ('usuario__username',)  # Búsqueda por nombre de usuario

class JefeProyectoAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'proyectosGestionados')
    search_fields = ('usuario__username',)  # Búsqueda por nombre de usuario

class ClienteAdmin(admin.ModelAdmin):
    list_display = ('usuario',)
    search_fields = ('usuario__username',)  # Búsqueda por nombre de usuario

class TesterAdmin(admin.ModelAdmin):
    list_display = ('usuario',)
    search_fields = ('usuario__username',)  # Búsqueda por nombre de usuario

# Registrar los modelos en el panel de administración
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(RolModuloAcceso, RolModuloAccesoAdmin)
admin.site.register(UsuarioRolModulo, UsuarioRolModuloAdmin)
admin.site.register(Administrador, AdministradorAdmin)
admin.site.register(Desarrollador, DesarrolladorAdmin)
admin.site.register(JefeProyecto, JefeProyectoAdmin)
admin.site.register(Cliente, ClienteAdmin)
admin.site.register(Tester, TesterAdmin)
