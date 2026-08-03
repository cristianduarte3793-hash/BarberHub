"""
Modelos relacionados con Usuarios - BarberHub.

Contiene:
- PerfilUsuario: Extiende el User de Django con rol, teléfono y foto
"""

from django.db import models
from django.contrib.auth.models import User


class PerfilUsuario(models.Model):
    """
    Perfil de Usuario.
    Extiende el User de Django con información extra mediante OneToOne.
    
    Roles disponibles:
    - ADMIN: Administrador del sistema
    - BARBERO: Profesional que atiende citas
    - CLIENTE: Usuario que agenda citas
    """
    
    ROL_CHOICES = [
        ('ADMIN',    'Administrador'),
        ('BARBERO',  'Barbero'),
        ('CLIENTE',  'Cliente'),
    ]

    # Relación OneToOne: un perfil por usuario
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='perfil'
    )
    telefono = models.CharField(max_length=20, blank=True, null=True)
    foto_perfil = models.ImageField(upload_to='perfiles/', blank=True, null=True)
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='CLIENTE')
    activo = models.BooleanField(default=True)
    creado_en = models.DateTimeField(auto_now_add=True)
    actualizado_en = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.usuario.get_full_name()} ({self.rol})'

    class Meta:
        verbose_name = 'Perfil de Usuario'
        verbose_name_plural = 'Perfiles de Usuario'
