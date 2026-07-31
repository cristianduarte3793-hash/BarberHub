"""
Formularios de BarberHub.
"""

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from .models import PerfilUsuario, Servicio, Horario, ConfiguracionBarberia


# ---------------------------------------------------------------------------
# Registro de cliente
# ---------------------------------------------------------------------------
class RegistroForm(forms.Form):
    first_name = forms.CharField(label='Nombre', max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Tu nombre'}))
    last_name = forms.CharField(label='Apellido', max_length=30,
        widget=forms.TextInput(attrs={'placeholder': 'Tu apellido'}))
    username = forms.CharField(label='Usuario', max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Elige un usuario'}))
    email = forms.EmailField(label='Correo electrónico',
        widget=forms.EmailInput(attrs={'placeholder': 'correo@ejemplo.com'}))
    telefono = forms.CharField(label='Teléfono', max_length=20, required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Opcional'}))
    password1 = forms.CharField(label='Contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Mínimo 8 caracteres'}))
    password2 = forms.CharField(label='Confirmar contraseña',
        widget=forms.PasswordInput(attrs={'placeholder': 'Repite la contraseña'}))

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Este nombre de usuario ya está en uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ya existe una cuenta con este correo.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            self.add_error('password2', 'Las contraseñas no coinciden.')
        if p1 and len(p1) < 8:
            self.add_error('password1', 'La contraseña debe tener al menos 8 caracteres.')
        return cleaned_data


# ---------------------------------------------------------------------------
# Editar perfil
# ---------------------------------------------------------------------------
class EditarPerfilForm(forms.ModelForm):
    first_name = forms.CharField(label='Nombre', max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(label='Apellido', max_length=30,
        widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(label='Correo electrónico',
        widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = PerfilUsuario
        fields = ['telefono', 'foto_perfil']
        widgets = {
            'telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'foto_perfil': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {'telefono': 'Teléfono', 'foto_perfil': 'Foto de perfil'}


# ---------------------------------------------------------------------------
# Cambiar contraseña
# ---------------------------------------------------------------------------
class CambiarPasswordForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs['class'] = 'form-control'


# ---------------------------------------------------------------------------
# Servicio (Admin)
# ---------------------------------------------------------------------------
class ServicioForm(forms.ModelForm):
    class Meta:
        model = Servicio
        fields = ['nombre', 'descripcion', 'precio', 'duracion', 'activo']
        widgets = {
            'nombre':      forms.TextInput(attrs={'placeholder': 'Ej: Corte Clásico'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción del servicio...'}),
            'precio':      forms.NumberInput(attrs={'step': '0.01', 'min': '0', 'placeholder': '0.00'}),
            'duracion':    forms.NumberInput(attrs={'min': '5', 'step': '5', 'placeholder': 'Minutos'}),
        }
        labels = {
            'nombre': 'Nombre del servicio',
            'descripcion': 'Descripción',
            'precio': 'Precio ($)',
            'duracion': 'Duración (min)',
            'activo': 'Servicio activo',
        }


# ---------------------------------------------------------------------------
# Horario (Admin)
# ---------------------------------------------------------------------------
class HorarioForm(forms.ModelForm):
    class Meta:
        model = Horario
        fields = ['dia_semana', 'fecha_especifica', 'hora_inicio', 'hora_fin', 'abierto', 'motivo_bloqueo']
        widgets = {
            'dia_semana':        forms.Select(),
            'fecha_especifica':  forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio':       forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin':          forms.TimeInput(attrs={'type': 'time'}),
            'motivo_bloqueo':    forms.TextInput(attrs={'placeholder': 'Ej: Festivo, mantenimiento...'}),
        }
        labels = {
            'dia_semana': 'Día de la semana',
            'fecha_especifica': 'Fecha específica (opcional)',
            'hora_inicio': 'Hora inicio',
            'hora_fin': 'Hora fin',
            'abierto': 'Abierto',
            'motivo_bloqueo': 'Motivo de bloqueo',
        }

    def clean(self):
        cleaned = super().clean()
        dia = cleaned.get('dia_semana')
        fecha = cleaned.get('fecha_especifica')
        inicio = cleaned.get('hora_inicio')
        fin = cleaned.get('hora_fin')
        if not dia and not fecha:
            raise forms.ValidationError('Debes indicar un día de la semana o una fecha específica.')
        if dia and fecha:
            raise forms.ValidationError('Elige solo un día de la semana O una fecha específica, no ambos.')
        if inicio and fin and inicio >= fin:
            raise forms.ValidationError('La hora de inicio debe ser anterior a la hora de fin.')
        return cleaned


# ---------------------------------------------------------------------------
# Configuración Barbería (Admin)
# ---------------------------------------------------------------------------
class ConfiguracionBarberiaForm(forms.ModelForm):
    class Meta:
        model = ConfiguracionBarberia
        fields = ['nombre', 'logo', 'descripcion', 'direccion',
                  'telefono', 'correo', 'facebook', 'instagram', 'tiktok', 'whatsapp']
        widgets = {
            'nombre':      forms.TextInput(attrs={'placeholder': 'Nombre de la barbería'}),
            'descripcion': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Descripción breve...'}),
            'direccion':   forms.Textarea(attrs={'rows': 2, 'placeholder': 'Dirección completa...'}),
            'telefono':    forms.TextInput(attrs={'placeholder': '+57 310 000 0000'}),
            'correo':      forms.EmailInput(attrs={'placeholder': 'hola@barberhub.co'}),
            'facebook':    forms.URLInput(attrs={'placeholder': 'https://facebook.com/...'}),
            'instagram':   forms.URLInput(attrs={'placeholder': 'https://instagram.com/...'}),
            'tiktok':      forms.URLInput(attrs={'placeholder': 'https://tiktok.com/@...'}),
            'whatsapp':    forms.TextInput(attrs={'placeholder': '+573100000000'}),
        }
        labels = {
            'nombre': 'Nombre de la barbería', 'logo': 'Logo',
            'descripcion': 'Descripción', 'direccion': 'Dirección',
            'telefono': 'Teléfono', 'correo': 'Correo electrónico',
            'facebook': 'Facebook', 'instagram': 'Instagram',
            'tiktok': 'TikTok', 'whatsapp': 'WhatsApp',
        }
