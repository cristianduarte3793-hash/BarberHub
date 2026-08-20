"""
Modelo de Notificaciones internas - BarberHub.
"""

from django.db import models
from .usuarios import PerfilUsuario
from .citas import Cita


class Notificacion(models.Model):
    """
    Notificaciones internas del sistema para los usuarios.

    Se usan principalmente para informar al cliente cuando
    su cita fue cancelada por el barbero.
    """

    TIPO_CHOICES = [
        ('CITA_CANCELADA_BARBERO', 'Cita cancelada por barbero'),
        ('INFO',                   'Información general'),
    ]

    destinatario = models.ForeignKey(
        PerfilUsuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
    )
    # Cita relacionada (opcional — puede eliminarse)
    cita = models.ForeignKey(
        Cita,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='notificaciones',
    )
    tipo    = models.CharField(max_length=30, choices=TIPO_CHOICES, default='INFO')
    titulo  = models.CharField(max_length=120)
    mensaje = models.TextField()
    leida   = models.BooleanField(default=False)
    creada_en = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'[{self.tipo}] → {self.destinatario} — {self.titulo}'

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-creada_en']
