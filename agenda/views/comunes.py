"""
Vistas comunes - BarberHub.
Dashboard general, perfil y cambio de contraseña.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Avg

from ..forms import EditarPerfilForm, CambiarPasswordForm
from ..models import PerfilUsuario, Barbero, Cita, Calificacion
from ..utils import es_admin, es_barbero, es_cliente


# ===========================================================================
# DASHBOARD GENERAL
# ===========================================================================

@login_required
def dashboard_view(request):
    """Dashboard principal con datos reales según el rol.
    Los barberos son redirigidos a su panel dedicado."""
    if es_barbero(request.user):
        return redirect('barbero_dashboard')

    hoy = timezone.localdate()

    # Datos comunes
    proximas_citas = []

    if es_admin(request.user):
        # Citas de hoy
        citas_hoy = Cita.objects.filter(fecha=hoy).exclude(estado='CANCELADA').count()
        # Clientes registrados
        total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
        # Barberos activos
        barberos_activos = Barbero.objects.filter(estado='ACTIVO').count()
        # Próximas citas (hoy y futuras, pendientes o confirmadas)
        proximas_citas = Cita.objects.filter(
            fecha__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_PROCESO']
        ).select_related(
            'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
        ).order_by('fecha', 'hora_inicio')[:10]

        # Servicios más solicitados (top 5 por conteo de citas finalizadas)
        servicios_top_qs = Cita.objects.filter(
            estado='FINALIZADA'
        ).values('servicio__nombre').annotate(
            total=Count('id')
        ).order_by('-total')[:5]

        total_servicios = sum(s['total'] for s in servicios_top_qs) or 1
        servicios_top = [
            {
                'nombre': s['servicio__nombre'],
                'porcentaje': round(s['total'] / total_servicios * 100),
            }
            for s in servicios_top_qs
        ]

        contexto = {
            'citas_hoy': citas_hoy,
            'total_clientes': total_clientes,
            'barberos_activos': barberos_activos,
            'proximas_citas': proximas_citas,
            'servicios_top': servicios_top,
        }

    elif es_barbero(request.user):
        try:
            barbero = request.user.perfil.barbero
            citas_hoy = Cita.objects.filter(
                barbero=barbero, fecha=hoy
            ).exclude(estado='CANCELADA').count()
            proximas_citas = Cita.objects.filter(
                barbero=barbero,
                fecha__gte=hoy,
                estado__in=['PENDIENTE', 'CONFIRMADA', 'EN_PROCESO']
            ).select_related('cliente__usuario', 'servicio').order_by('fecha', 'hora_inicio')[:10]
        except Exception:
            citas_hoy = 0

        contexto = {
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'servicios_top': [],
        }

    else:  # CLIENTE
        citas_hoy = Cita.objects.filter(
            cliente=request.user.perfil,
            fecha=hoy
        ).exclude(estado='CANCELADA').count()
        proximas_citas = Cita.objects.filter(
            cliente=request.user.perfil,
            fecha__gte=hoy,
            estado__in=['PENDIENTE', 'CONFIRMADA']
        ).select_related('barbero__perfil__usuario', 'servicio').order_by('fecha', 'hora_inicio')[:5]

        contexto = {
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'servicios_top': [],
        }

    return render(request, 'agenda/dashboard.html', contexto)


# ===========================================================================
# PERFIL
# ===========================================================================

@login_required
def perfil_view(request):
    """Ver y editar perfil del usuario."""
    perfil = get_object_or_404(PerfilUsuario, usuario=request.user)

    if request.method == 'POST':
        form = EditarPerfilForm(request.POST, request.FILES, instance=perfil)
        if form.is_valid():
            form.save()
            request.user.first_name = form.cleaned_data['first_name']
            request.user.last_name = form.cleaned_data['last_name']
            request.user.email = form.cleaned_data['email']
            request.user.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil')
    else:
        initial = {
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
        }
        form = EditarPerfilForm(instance=perfil, initial=initial)

    contexto = {'form': form, 'perfil': perfil}

    # Datos extra para barberos
    if perfil.rol == 'BARBERO':
        try:
            barbero = perfil.barbero
            calificacion_resultado = Calificacion.objects.filter(
                barbero=barbero
            ).aggregate(prom=Avg('puntuacion'))
            contexto['calificacion_promedio'] = (
                round(calificacion_resultado['prom'], 1)
                if calificacion_resultado['prom'] else None
            )
            contexto['total_citas_realizadas'] = Cita.objects.filter(
                barbero=barbero, estado='FINALIZADA'
            ).count()
        except Exception:
            contexto['calificacion_promedio'] = None
            contexto['total_citas_realizadas'] = 0

    return render(request, 'agenda/perfil.html', contexto)


# ===========================================================================
# CAMBIAR CONTRASEÑA
# ===========================================================================

@login_required
def cambiar_password_view(request):
    """Cambiar contraseña del usuario autenticado."""
    if request.method == 'POST':
        form = CambiarPasswordForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Contraseña cambiada correctamente.')
            return redirect('perfil')
    else:
        form = CambiarPasswordForm(request.user)

    return render(request, 'agenda/cambiar_password.html', {'form': form})
