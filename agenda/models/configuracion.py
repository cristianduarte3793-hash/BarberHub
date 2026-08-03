"""
Modelos de Configuración del Sistema - BarberHub.

Contiene:
- ConfiguracionBarberia: Datos de la barbería (nombre, logo, contactos, etc.)
"""

from django.db import models


class ConfiguracionBarberia(models.Model):
    """
    Configuración general de la barbería.
    
    Solo debe existir un registro (singleton).
    Contiene información de contacto, redes sociales y branding.
    """
    
    nombre = models.CharField(max_length=100)
    logo = models.ImageField(upload_to='barberia/', blank=True, null=True)
    descripcion = models.TextField(blank=True, null=True)
    direccion = models.TextField(blank=True, null=True)
    telefono = models.CharField(max_length=20, blank=True, null=True)
    correo = models.EmailField(blank=True, null=True)
    facebook = models.URLField(blank=True, null=True)
    instagram = models.URLField(blank=True, null=True)
    tiktok = models.URLField(blank=True, null=True)
    whatsapp = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'Configuración de la Barbería'
        verbose_name_plural = 'Configuración de la Barbería'
