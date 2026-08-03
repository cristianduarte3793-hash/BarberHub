"""
Configuración del panel de administración de Django para BarberHub.
Este panel es útil para debugging y gestión rápida de datos.
"""

from django.contrib import admin
from .models import (
    PerfilUsuario, ConfiguracionBarberia, Servicio, Barbero,
    Horario, Cita, Calificacion
)


# ===========================================================================
# PERFIL DE USUARIO
# ===========================================================================

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'rol', 'telefono', 'activo', 'creado_en')
    list_filter = ('rol', 'activo', 'creado_en')
    search_fields = ('usuario__username', 'usuario__first_name', 'usuario__last_name', 'telefono')
    readonly_fields = ('creado_en', 'actualizado_en')
    
    fieldsets = (
        ('Usuario', {
            'fields': ('usuario', 'rol', 'activo')
        }),
        ('Información de Contacto', {
            'fields': ('telefono', 'foto_perfil')
        }),
        ('Fechas', {
            'fields': ('creado_en', 'actualizado_en'),
            'classes': ('collapse',)
        }),
    )


# ===========================================================================
# CONFIGURACIÓN BARBERÍA
# ===========================================================================

@admin.register(ConfiguracionBarberia)
class ConfiguracionBarberiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'telefono', 'correo')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'logo', 'descripcion')
        }),
        ('Contacto', {
            'fields': ('direccion', 'telefono', 'correo')
        }),
        ('Redes Sociales', {
            'fields': ('facebook', 'instagram', 'tiktok', 'whatsapp')
        }),
    )


# ===========================================================================
# SERVICIOS
# ===========================================================================

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion', 'activo', 'creado_en')
    list_filter = ('activo', 'creado_en')
    search_fields = ('nombre', 'descripcion')
    readonly_fields = ('creado_en',)
    
    fieldsets = (
        ('Información del Servicio', {
            'fields': ('nombre', 'descripcion', 'activo')
        }),
        ('Detalles', {
            'fields': ('precio', 'duracion')
        }),
        ('Fechas', {
            'fields': ('creado_en',),
            'classes': ('collapse',)
        }),
    )


# ===========================================================================
# BARBEROS
# ===========================================================================

@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'especialidad', 'estado', 'disponibilidad')
    list_filter = ('estado', 'disponibilidad')
    search_fields = ('perfil__usuario__first_name', 'perfil__usuario__last_name', 'especialidad')
    filter_horizontal = ('servicios',)
    
    fieldsets = (
        ('Perfil', {
            'fields': ('perfil',)
        }),
        ('Información Profesional', {
            'fields': ('especialidad', 'descripcion', 'servicios')
        }),
        ('Estado', {
            'fields': ('estado', 'disponibilidad')
        }),
    )
    
    def get_nombre_completo(self, obj):
        return obj.perfil.usuario.get_full_name() or obj.perfil.usuario.username
    get_nombre_completo.short_description = 'Nombre'


# ===========================================================================
# HORARIOS
# ===========================================================================

@admin.register(Horario)
class HorarioAdmin(admin.ModelAdmin):
    list_display = ('get_tipo', 'get_dia_o_fecha', 'hora_inicio', 'hora_fin', 'abierto')
    list_filter = ('abierto', 'dia_semana')
    
    fieldsets = (
        ('Tipo de Horario', {
            'fields': ('dia_semana', 'fecha_especifica'),
            'description': 'Elige DÍA DE LA SEMANA para horario regular, o FECHA ESPECÍFICA para días especiales.'
        }),
        ('Horario', {
            'fields': ('hora_inicio', 'hora_fin', 'abierto')
        }),
        ('Bloqueo', {
            'fields': ('motivo_bloqueo',),
            'classes': ('collapse',)
        }),
    )
    
    def get_tipo(self, obj):
        return 'Semanal' if obj.dia_semana is not None else 'Especial'
    get_tipo.short_description = 'Tipo'
    
    def get_dia_o_fecha(self, obj):
        if obj.dia_semana is not None:
            return obj.get_dia_semana_display()
        return obj.fecha_especifica
    get_dia_o_fecha.short_description = 'Día/Fecha'


# ===========================================================================
# CITAS
# ===========================================================================

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_cliente', 'get_barbero', 'servicio', 'fecha', 'hora_inicio', 'estado', 'precio')
    list_filter = ('estado', 'fecha', 'barbero', 'servicio')
    search_fields = (
        'cliente__usuario__first_name', 'cliente__usuario__last_name',
        'barbero__perfil__usuario__first_name', 'barbero__perfil__usuario__last_name'
    )
    readonly_fields = ('creado_en',)
    date_hierarchy = 'fecha'
    
    fieldsets = (
        ('Información de la Cita', {
            'fields': ('cliente', 'barbero', 'servicio')
        }),
        ('Fecha y Hora', {
            'fields': ('fecha', 'hora_inicio', 'hora_fin')
        }),
        ('Detalles', {
            'fields': ('precio', 'estado', 'observaciones')
        }),
        ('Metadata', {
            'fields': ('creado_en',),
            'classes': ('collapse',)
        }),
    )
    
    def get_cliente(self, obj):
        return obj.cliente.usuario.get_full_name() or obj.cliente.usuario.username
    get_cliente.short_description = 'Cliente'
    
    def get_barbero(self, obj):
        return obj.barbero.perfil.usuario.get_full_name() or obj.barbero.perfil.usuario.username
    get_barbero.short_description = 'Barbero'


# ===========================================================================
# CALIFICACIONES
# ===========================================================================

@admin.register(Calificacion)
class CalificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'get_cita_id', 'get_cliente', 'get_barbero', 'puntuacion', 'creado_en')
    list_filter = ('puntuacion', 'creado_en')
    search_fields = (
        'cliente__usuario__first_name', 'cliente__usuario__last_name',
        'barbero__perfil__usuario__first_name', 'barbero__perfil__usuario__last_name',
        'comentario'
    )
    readonly_fields = ('creado_en',)
    date_hierarchy = 'creado_en'
    
    fieldsets = (
        ('Cita Relacionada', {
            'fields': ('cita',)
        }),
        ('Calificación', {
            'fields': ('cliente', 'barbero', 'puntuacion', 'comentario')
        }),
        ('Metadata', {
            'fields': ('creado_en',),
            'classes': ('collapse',)
        }),
    )
    
    def get_cita_id(self, obj):
        return f'Cita #{obj.cita.id}'
    get_cita_id.short_description = 'Cita'
    
    def get_cliente(self, obj):
        return obj.cliente.usuario.get_full_name() or obj.cliente.usuario.username
    get_cliente.short_description = 'Cliente'
    
    def get_barbero(self, obj):
        return obj.barbero.perfil.usuario.get_full_name() or obj.barbero.perfil.usuario.username
    get_barbero.short_description = 'Barbero'
