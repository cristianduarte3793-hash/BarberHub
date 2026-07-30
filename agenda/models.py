"""
Modelos de BarberHub.

Todas las tablas del sistema se definen aquí.
Django genera las migraciones automáticamente a partir de estos modelos.

Tablas que Django crea solas (NO las tocamos):
  - auth_user          → el usuario base (username, email, password, etc.)
  - auth_group         → grupos de permisos
  - auth_permission    → permisos
  - django_session     → sesiones
  - django_content_type

Tablas que creamos nosotros:
  - agenda_perfilusuario      (extiende auth_user con rol, teléfono, foto)
  - agenda_configuracionbarberia
  - agenda_servicio
  - agenda_barbero
  - agenda_barbero_servicios  (tabla pivot ManyToMany, la genera Django)
  - agenda_horario
  - agenda_cita
  - agenda_calificacion
"""

from django.db import models
from django.contrib.auth.models import User


# ---------------------------------------------------------------------------
# Perfil de Usuario
# Extiende el User de Django con información extra mediante OneToOne.
# ---------------------------------------------------------------------------
class PerfilUsuario(models.Model):
    ROL_CHOICES = [
        ('ADMIN',    'Administrador'),
        ('BARBERO',  'Barbero'),
        ('CLIENTE',  'Cliente'),
    ]

    # Relación OneToOne: un perfil por usuario
    usuario    = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefono   = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    rol        = models.CharField(max_length=10, choices=ROL_CHOICES, default='CLIENTE')
    activo     = models.BooleanField(default=True)
    creado_en  = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.usuario.get_full_name()} ({self.rol})'

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'


# ---------------------------------------------------------------------------
# Configuración de la Barbería
# Solo debe existir un registro (singleton).
# ---------------------------------------------------------------------------
class ConfiguracionBarberia(models.Model):
    nombre      = models.CharField(max_length=100)
    logo        = models.ImageField(upload_to='barberia/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    direccion   = models.TextField(blank=True, null=True)
    telefono    = models.CharField(max_length=20, blank=True, null=True)
    correo      = models.EmailField(blank=True, null=True)
    facebook    = models.URLField(blank=True, null=True)
    instagram   = models.URLField(blank=True, null=True)
    tiktok      = models.URLField(blank=True, null=True)
    whatsapp    = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Configuración de la Barbería'
        verbose_name_plural = 'Configuración de la Barbería'


# ---------------------------------------------------------------------------
# Servicios
# ---------------------------------------------------------------------------
class Servicio(models.Model):
    nombre      = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    precio      = models.DecimalField(max_digits=10, decimal_places=2)
    # Duración en minutos (ej: 30, 45, 60)
    duracion    = models.PositiveIntegerField(help_text='Duración en minutos')
    activo      = models.BooleanField(default=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} - ${self.precio} ({self.duracion} min)'

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']


# ---------------------------------------------------------------------------
# Barberos
# Cada barbero está vinculado a un PerfilUsuario con rol BARBERO.
# Puede ofrecer múltiples servicios (ManyToMany).
# ---------------------------------------------------------------------------
class Barbero(models.Model):
    ESTADO_CHOICES = [
        ('ACTIVO',     'Activo'),
        ('INACTIVO',   'Inactivo'),
        ('VACACIONES', 'En Vacaciones'),
    ]

    # Relación con el perfil del usuario (que tiene rol BARBERO)
    perfil      = models.OneToOneField(PerfilUsuario, on_delete=models.CASCADE, related_name='barbero')
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    descripcion  = models.TextField(blank=True, null=True)
    # Servicios que este barbero puede realizar
    servicios    = models.ManyToManyField(Servicio, blank=True, related_name='barberos')
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='ACTIVO')

    def __str__(self):
        return self.perfil.usuario.get_full_name() or self.perfil.usuario.username

    class Meta:
        verbose_name = 'Barbero'
        verbose_name_plural = 'Barberos'


# ---------------------------------------------------------------------------
# Horarios
# Dos tipos de registro:
#   1. Horario semanal: dia_semana = 0 (lunes) ... 6 (domingo), fecha_especifica = null
#   2. Día especial: fecha_especifica = una fecha concreta, dia_semana = null
#      Si abierto=False, ese día está bloqueado (festivo, vacaciones, etc.)
# ---------------------------------------------------------------------------
class Horario(models.Model):
    DIA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dia_semana       = models.IntegerField(choices=DIA_CHOICES, blank=True, null=True)
    fecha_especifica = models.DateField(blank=True, null=True)
    hora_inicio      = models.TimeField()
    hora_fin         = models.TimeField()
    abierto          = models.BooleanField(default=True)
    # Motivo de bloqueo: festivo, mantenimiento, vacaciones, etc.
    motivo_bloqueo   = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.fecha_especifica:
            estado = 'Abierto' if self.abierto else f'Bloqueado ({self.motivo_bloqueo})'
            return f'{self.fecha_especifica} - {estado}'
        return f'{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}'

    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'


# ---------------------------------------------------------------------------
# Citas
# ---------------------------------------------------------------------------
class Cita(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE',   'Pendiente'),
        ('CONFIRMADA',  'Confirmada'),
        ('EN_PROCESO',  'En Proceso'),
        ('FINALIZADA',  'Finalizada'),
        ('CANCELADA',   'Cancelada'),
    ]

    # El cliente es el PerfilUsuario con rol CLIENTE
    cliente      = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE,
                                     related_name='citas_cliente')
    barbero      = models.ForeignKey(Barbero, on_delete=models.CASCADE,
                                     related_name='citas_barbero')
    servicio     = models.ForeignKey(Servicio, on_delete=models.CASCADE,
                                     related_name='citas_servicio')
    fecha        = models.DateField()
    hora_inicio  = models.TimeField()
    hora_fin     = models.TimeField()
    # Precio guardado en el momento de crear la cita (puede cambiar después)
    precio       = models.DecimalField(max_digits=10, decimal_places=2)
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)
    creado_en    = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (f'Cita #{self.pk} - {self.cliente} con {self.barbero} '
                f'el {self.fecha} a las {self.hora_inicio}')

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora_inicio']


# ---------------------------------------------------------------------------
# Calificaciones
# Solo se puede calificar cuando la cita esté FINALIZADA.
# Una sola calificación por cita (OneToOne).
# ---------------------------------------------------------------------------
class Calificacion(models.Model):
    PUNTUACION_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1 a 5 estrellas

    # OneToOne garantiza que solo exista una calificación por cita
    cita        = models.OneToOneField(Cita, on_delete=models.CASCADE,
                                       related_name='calificacion')
    # Guardamos cliente y barbero directo para facilitar consultas de reportes
    cliente     = models.ForeignKey(PerfilUsuario, on_delete=models.CASCADE,
                                    related_name='calificaciones_dadas')
    barbero     = models.ForeignKey(Barbero, on_delete=models.CASCADE,
                                    related_name='calificaciones_recibidas')
    puntuacion  = models.PositiveSmallIntegerField(choices=PUNTUACION_CHOICES)
    comentario  = models.TextField(blank=True, null=True)
    creado_en   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Calificación cita #{self.cita.pk} - {self.puntuacion}★'

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
