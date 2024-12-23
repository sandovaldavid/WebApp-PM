from django.contrib import admin
from .models import Usuario, RolModuloAcceso, UsuarioRolModulo

# Register your models here.

@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'rol', 'fecha_creacion', 'fecha_modificacion')
    list_filter = ('rol', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'rol')
    ordering = ('-fecha_creacion',)

@admin.register(RolModuloAcceso)
class RolModuloAccesoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre_rol', 'modulo', 'permisos')
    list_filter = ('nombre_rol', 'permisos')
    search_fields = ('nombre_rol', 'modulo')
    ordering = ('id',)

@admin.register(UsuarioRolModulo)
class UsuarioRolModuloAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'rol_modulo')
    search_fields = ('usuario__username', 'rol_modulo__nombre_rol')
    ordering = ('id',)
