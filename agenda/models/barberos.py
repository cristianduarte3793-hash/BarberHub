"""
Modelos relacionados con Barberos y Servicios - BarberHub.

Contiene:
- Servicio: Servicios ofrecidos en la barbería
- Barbero: Profesionales que atienden las citas
"""

from django.db import models
from .usuarios import PerfilUsuario


class Servicio(models.Model):
    """
    Servicios ofrecidos por la barbería.
    
    Cada servicio tiene un precio y duración definidos.
    Los barberos pueden ofrecer múltiples servicios.
    """
    
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    # Precio en pesos colombianos (sin decimales)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    # Duración en minutos (ej: 30, 45, 60)
    duracion = models.PositiveIntegerField(help_text='Duración en minutos')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.nombre} - $ {int(self.precio):,} COP ({self.duracion} min)'.replace(',', '.')

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['nombre']


class Barbero(models.Model):
    """
    Barberos del sistema.
    
    Cada barbero está vinculado a un PerfilUsuario con rol BARBERO.
    Puede ofrecer múltiples servicios (ManyToMany).
    """
    
    ESTADO_CHOICES = [
        ('ACTIVO',     'Activo'),
        ('INACTIVO',   'Inactivo'),
        ('VACACIONES', 'En Vacaciones'),
    ]

    DISPONIBILIDAD_CHOICES = [
        ('DISPONIBLE',     'Disponible'),
        ('OCUPADO',        'Ocupado'),
        ('NO_DISPONIBLE',  'No disponible'),
    ]

    # Relación con el perfil del usuario (que tiene rol BARBERO)
    perfil = models.OneToOneField(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='barbero'
    )
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # Servicios que este barbero puede realizar
    servicios = models.ManyToManyField(Servicio, blank=True, related_name='barberos')
    
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='ACTIVO')
    disponibilidad = models.CharField(
        max_length=20,
        choices=DISPONIBILIDAD_CHOICES,
        default='DISPONIBLE',
        help_text='Estado de disponibilidad visible para los clientes',
    )

    def __str__(self):
        return self.perfil.usuario.get_full_name() or self.perfil.usuario.username

    class Meta:
        verbose_name = 'Barbero'
        verbose_name_plural = 'Barberos'
