"""
Modelos relacionados con Citas y Horarios - BarberHub.

Contiene:
- Horario: Define horarios de atención (semanales y especiales)
- Cita: Agendamiento de servicios
- Calificacion: Calificaciones de citas finalizadas
"""

from django.db import models
from .usuarios import PerfilUsuario
from .barberos import Barbero, Servicio


class Horario(models.Model):
    """
    Horarios de atención de la barbería.
    
    Dos tipos de registro:
    1. Horario semanal: dia_semana = 0 (lunes) ... 6 (domingo), fecha_especifica = null
    2. Día especial: fecha_especifica = una fecha concreta, dia_semana = null
       Si abierto=False, ese día está bloqueado (festivo, vacaciones, etc.)
    """
    
    DIA_CHOICES = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]

    dia_semana = models.IntegerField(choices=DIA_CHOICES, blank=True, null=True)
    fecha_especifica = models.DateField(blank=True, null=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    abierto = models.BooleanField(default=True)
    # Motivo de bloqueo: festivo, mantenimiento, vacaciones, etc.
    motivo_bloqueo = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        if self.fecha_especifica:
            estado = 'Abierto' if self.abierto else f'Bloqueado ({self.motivo_bloqueo})'
            return f'{self.fecha_especifica} - {estado}'
        return f'{self.get_dia_semana_display()} {self.hora_inicio}-{self.hora_fin}'

    class Meta:
        verbose_name = 'Horario'
        verbose_name_plural = 'Horarios'


class Cita(models.Model):
    """
    Citas agendadas en la barbería.
    
    Una cita relaciona un cliente con un barbero para un servicio específico
    en una fecha y hora determinadas.
    """
    
    ESTADO_CHOICES = [
        ('PENDIENTE',   'Pendiente'),
        ('CONFIRMADA',  'Confirmada'),
        ('EN_PROCESO',  'En Proceso'),
        ('FINALIZADA',  'Finalizada'),
        ('CANCELADA',   'Cancelada'),
    ]

    # El cliente es el PerfilUsuario con rol CLIENTE
    cliente = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='citas_cliente'
    )
    barbero = models.ForeignKey(
        Barbero,
        on_delete=models.CASCADE,
        related_name='citas_barbero'
    )
    servicio = models.ForeignKey(
        Servicio,
        on_delete=models.CASCADE,
        related_name='citas_servicio'
    )
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    # Precio en pesos colombianos (sin decimales)
    precio = models.DecimalField(max_digits=10, decimal_places=0)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='PENDIENTE')
    observaciones = models.TextField(blank=True, null=True)
    # Código único de reserva — formato BH-000001
    codigo_reserva = models.CharField(max_length=20, unique=True, blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        """Genera el código de reserva automáticamente al crear la cita."""
        # Primera pasada: guardamos sin código para obtener el PK
        if not self.pk:
            super().save(*args, **kwargs)
            self.codigo_reserva = f'BH-{self.pk:06d}'
            # Segunda pasada: actualizamos solo el campo codigo_reserva
            Cita.objects.filter(pk=self.pk).update(codigo_reserva=self.codigo_reserva)
        else:
            super().save(*args, **kwargs)

    def __str__(self):
        return (f'Cita #{self.pk} - {self.cliente} con {self.barbero} '
                f'el {self.fecha} a las {self.hora_inicio}')

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora_inicio']


class Calificacion(models.Model):
    """
    Calificaciones de citas finalizadas.
    
    Solo se puede calificar cuando la cita esté FINALIZADA.
    Una sola calificación por cita (OneToOne).
    """
    
    PUNTUACION_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1 a 5 estrellas

    # OneToOne garantiza que solo exista una calificación por cita
    cita = models.OneToOneField(
        Cita,
        on_delete=models.CASCADE,
        related_name='calificacion'
    )
    # Guardamos cliente y barbero directo para facilitar consultas de reportes
    cliente = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='calificaciones_dadas'
    )
    barbero = models.ForeignKey(
        Barbero,
        on_delete=models.CASCADE,
        related_name='calificaciones_recibidas'
    )
    puntuacion = models.PositiveSmallIntegerField(choices=PUNTUACION_CHOICES)
    comentario = models.TextField(blank=True, null=True)
    creado_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Calificación cita #{self.cita.pk} - {self.puntuacion}★'

    class Meta:
        verbose_name = 'Calificación'
        verbose_name_plural = 'Calificaciones'
