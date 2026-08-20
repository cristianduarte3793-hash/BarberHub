"""
Vistas del módulo ADMINISTRADOR - BarberHub.
Gestión de servicios, horarios, citas, reportes y configuración.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone

from ..forms import ServicioForm, HorarioForm, ConfiguracionBarberiaForm, BarberoForm
from ..models import (
    Barbero, Servicio, Cita, Horario, ConfiguracionBarberia,
    PerfilUsuario, Calificacion,
)
from ..utils import admin_required


# ===========================================================================
# GESTIÓN DE BARBEROS
# ===========================================================================

@login_required
@admin_required
def barberos_view(request):
    """Lista y gestión de barberos. Solo accesible para ADMIN."""
    barberos = Barbero.objects.select_related(
        'perfil__usuario'
    ).prefetch_related('servicios').all()

    contexto = {
        'barberos': barberos,
        'total_barberos': barberos.count(),
        'barberos_activos': barberos.filter(estado='ACTIVO').count(),
        # Barbero con más citas finalizadas
        'top_barbero': Cita.objects.filter(estado='FINALIZADA').values(
            'barbero__perfil__usuario__first_name',
            'barbero__perfil__usuario__last_name',
        ).annotate(total=Count('id')).order_by('-total').first(),
        # Citas pendientes totales
        'citas_pendientes': Cita.objects.filter(estado='PENDIENTE').count(),
    }
    return render(request, 'agenda/barberos.html', contexto)


@login_required
@admin_required
def barbero_crear_view(request):
    """Crear un nuevo barbero (User + PerfilUsuario + Barbero)."""
    form = BarberoForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        # 1. Crear User de Django
        user = User.objects.create_user(
            username   = d['username'],
            password   = d['password'],
            first_name = d['first_name'],
            last_name  = d['last_name'],
            email      = d.get('email', ''),
        )
        # 2. Crear / actualizar PerfilUsuario con rol BARBERO
        perfil = PerfilUsuario.objects.create(
            usuario    = user,
            rol        = 'BARBERO',
            telefono   = d.get('telefono', ''),
            foto_perfil= d.get('foto_perfil') or None,
        )
        # 3. Crear Barbero
        barbero = Barbero.objects.create(
            perfil      = perfil,
            especialidad= d.get('especialidad', ''),
            descripcion = d.get('descripcion', ''),
            estado      = d['estado'],
        )
        barbero.servicios.set(d.get('servicios') or [])
        messages.success(request, f'Barbero "{user.get_full_name()}" creado correctamente.')
        return redirect('barberos')

    return render(request, 'agenda/admin/barbero_form.html', {
        'form':   form,
        'accion': 'Crear',
        'servicios_seleccionados': [int(pk) for pk in request.POST.getlist('servicios')] if request.method == 'POST' else [],
    })


@login_required
@admin_required
def barbero_editar_view(request, pk):
    """Editar datos de un barbero existente."""
    barbero = get_object_or_404(Barbero, pk=pk)
    form = BarberoForm(
        request.POST or None,
        request.FILES or None,
        barbero_instance=barbero,
    )
    if request.method == 'POST' and form.is_valid():
        d = form.cleaned_data
        # Actualizar User
        user = barbero.perfil.usuario
        user.first_name = d['first_name']
        user.last_name  = d['last_name']
        user.email      = d.get('email', '')
        user.username   = d['username']
        if d.get('password'):
            user.set_password(d['password'])
        user.save()
        # Actualizar Perfil
        perfil = barbero.perfil
        perfil.telefono = d.get('telefono', '')
        if d.get('foto_perfil'):
            perfil.foto_perfil = d['foto_perfil']
        perfil.save()
        # Actualizar Barbero
        barbero.especialidad = d.get('especialidad', '')
        barbero.descripcion  = d.get('descripcion', '')
        barbero.estado       = d['estado']
        barbero.save()
        barbero.servicios.set(d.get('servicios') or [])
        messages.success(request, f'Barbero "{user.get_full_name()}" actualizado correctamente.')
        return redirect('barberos')

    return render(request, 'agenda/admin/barbero_form.html', {
        'form':    form,
        'accion':  'Editar',
        'barbero': barbero,
        'servicios_seleccionados': list(barbero.servicios.values_list('pk', flat=True)),
    })


@login_required
@admin_required
def barbero_eliminar_view(request, pk):
    """
    Eliminar un barbero.
    Si tiene citas activas (PENDIENTE/CONFIRMADA), se bloquea la eliminación.
    Si tiene citas históricas, se desactiva en su lugar.
    """
    barbero = get_object_or_404(Barbero, pk=pk)

    citas_activas = Cita.objects.filter(
        barbero=barbero, estado__in=['PENDIENTE', 'CONFIRMADA']
    ).count()

    if citas_activas:
        messages.error(
            request,
            f'No se puede eliminar a "{barbero}" porque tiene {citas_activas} '
            'cita(s) activa(s). Cambia su estado a Inactivo primero.'
        )
        return redirect('barberos')

    if request.method == 'POST':
        nombre = str(barbero)
        # Elimina el User — en cascada elimina PerfilUsuario y Barbero
        barbero.perfil.usuario.delete()
        messages.success(request, f'Barbero "{nombre}" eliminado correctamente.')
        return redirect('barberos')

    return render(request, 'agenda/admin/confirmar_eliminar.html', {
        'objeto': barbero,
        'tipo':   'barbero',
    })


@login_required
@admin_required
def barbero_toggle_estado(request, pk):
    """Cicla el estado del barbero: ACTIVO → INACTIVO → ACTIVO."""
    barbero = get_object_or_404(Barbero, pk=pk)
    if request.method == 'POST':
        barbero.estado = 'INACTIVO' if barbero.estado == 'ACTIVO' else 'ACTIVO'
        barbero.save()
        messages.success(
            request,
            f'Barbero "{barbero}" ahora está {barbero.get_estado_display()}.'
        )
    return redirect('barberos')


# ===========================================================================
# GESTIÓN DE SERVICIOS
# ===========================================================================

@login_required
@admin_required
def servicios_view(request):
    """Lista todos los servicios."""
    servicios = Servicio.objects.annotate(total_citas=Count('citas_servicio')).order_by('nombre')
    return render(request, 'agenda/admin/servicios.html', {'servicios': servicios})


@login_required
@admin_required
def servicio_crear(request):
    """Crear un nuevo servicio."""
    form = ServicioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio creado correctamente.')
        return redirect('servicios')
    return render(request, 'agenda/admin/servicio_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@admin_required
def servicio_editar(request, pk):
    """Editar servicio existente."""
    servicio = get_object_or_404(Servicio, pk=pk)
    form = ServicioForm(request.POST or None, instance=servicio)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Servicio actualizado correctamente.')
        return redirect('servicios')
    return render(request, 'agenda/admin/servicio_form.html', {'form': form, 'accion': 'Editar', 'servicio': servicio})


@login_required
@admin_required
def servicio_toggle(request, pk):
    """Activar / desactivar servicio."""
    servicio = get_object_or_404(Servicio, pk=pk)
    servicio.activo = not servicio.activo
    servicio.save()
    estado = 'activado' if servicio.activo else 'desactivado'
    messages.success(request, f'Servicio "{servicio.nombre}" {estado}.')
    return redirect('servicios')


@login_required
@admin_required
def servicio_eliminar(request, pk):
    """Eliminar servicio (solo si no tiene citas asociadas)."""
    servicio = get_object_or_404(Servicio, pk=pk)
    if servicio.citas_servicio.exists():
        messages.error(request, f'No se puede eliminar "{servicio.nombre}" porque tiene citas asociadas. Desactívalo en su lugar.')
        return redirect('servicios')
    if request.method == 'POST':
        servicio.delete()
        messages.success(request, 'Servicio eliminado.')
        return redirect('servicios')
    return render(request, 'agenda/admin/confirmar_eliminar.html', {'objeto': servicio, 'tipo': 'servicio'})


# ===========================================================================
# GESTIÓN DE CITAS (Admin)
# ===========================================================================

@login_required
@admin_required
def citas_admin_view(request):
    """Lista todas las citas con filtros."""
    citas = Cita.objects.select_related(
        'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
    ).order_by('-fecha', '-hora_inicio')

    # Filtros GET
    fecha = request.GET.get('fecha', '').strip()
    estado = request.GET.get('estado', '').strip()
    barbero = request.GET.get('barbero', '').strip()
    cliente = request.GET.get('cliente', '').strip()

    if fecha:
        citas = citas.filter(fecha=fecha)
    if estado:
        citas = citas.filter(estado=estado)
    if barbero:
        citas = citas.filter(barbero__id=barbero)
    if cliente:
        citas = citas.filter(
            Q(cliente__usuario__first_name__icontains=cliente) |
            Q(cliente__usuario__last_name__icontains=cliente) |
            Q(cliente__usuario__username__icontains=cliente)
        )

    contexto = {
        'citas': citas,
        'barberos_lista': Barbero.objects.select_related('perfil__usuario').filter(estado='ACTIVO'),
        'estados': Cita.ESTADO_CHOICES,
        'filtros': {'fecha': fecha, 'estado': estado, 'barbero': barbero, 'cliente': cliente},
        'total': citas.count(),
    }
    return render(request, 'agenda/admin/citas_admin.html', contexto)


@login_required
@admin_required
def cita_cambiar_estado(request, pk):
    """Cambiar el estado de una cita vía POST."""
    cita = get_object_or_404(Cita, pk=pk)
    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado', '')
        estados_validos = [e[0] for e in Cita.ESTADO_CHOICES]
        if nuevo_estado in estados_validos:
            cita.estado = nuevo_estado
            cita.save()
            messages.success(request, f'Cita #{cita.pk} → {cita.get_estado_display()}')
        else:
            messages.error(request, 'Estado inválido.')
    return redirect(request.META.get('HTTP_REFERER', 'citas_admin'))


# ===========================================================================
# GESTIÓN DE HORARIOS
# ===========================================================================

@login_required
@admin_required
def horarios_view(request):
    """Lista horarios semanales y días especiales."""
    horarios_semana = Horario.objects.filter(
        fecha_especifica__isnull=True
    ).order_by('dia_semana')

    horarios_especiales = Horario.objects.filter(
        fecha_especifica__isnull=False
    ).order_by('-fecha_especifica')

    return render(request, 'agenda/admin/horarios.html', {
        'horarios_semana': horarios_semana,
        'horarios_especiales': horarios_especiales,
    })


@login_required
@admin_required
def horario_crear(request):
    """Crear horario o bloqueo de día."""
    form = HorarioForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Horario guardado correctamente.')
        return redirect('horarios')
    return render(request, 'agenda/admin/horario_form.html', {'form': form, 'accion': 'Crear'})


@login_required
@admin_required
def horario_editar(request, pk):
    """Editar horario existente."""
    horario = get_object_or_404(Horario, pk=pk)
    form = HorarioForm(request.POST or None, instance=horario)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Horario actualizado.')
        return redirect('horarios')
    return render(request, 'agenda/admin/horario_form.html', {'form': form, 'accion': 'Editar', 'horario': horario})


@login_required
@admin_required
def horario_eliminar(request, pk):
    """Eliminar horario."""
    horario = get_object_or_404(Horario, pk=pk)
    if request.method == 'POST':
        horario.delete()
        messages.success(request, 'Horario eliminado.')
        return redirect('horarios')
    return render(request, 'agenda/admin/confirmar_eliminar.html', {'objeto': horario, 'tipo': 'horario'})


# ===========================================================================
# REPORTES Y ESTADÍSTICAS
# ===========================================================================

@login_required
@admin_required
def reportes_view(request):
    """Panel de reportes con filtro mensual."""
    hoy = timezone.localdate()

    # ── Parámetros del filtro ────────────────────────────────────────────
    try:
        anio  = int(request.GET.get('anio',  hoy.year))
        mes   = int(request.GET.get('mes',   hoy.month))
        if not (1 <= mes <= 12):
            raise ValueError
    except (ValueError, TypeError):
        anio, mes = hoy.year, hoy.month

    from datetime import date as date_type
    import calendar
    ultimo_dia = calendar.monthrange(anio, mes)[1]
    inicio_mes = date_type(anio, mes, 1)
    fin_mes    = date_type(anio, mes, ultimo_dia)

    # ── Citas del mes seleccionado ───────────────────────────────────────
    citas_mes_qs = Cita.objects.filter(fecha__range=(inicio_mes, fin_mes))

    citas_mes          = citas_mes_qs.exclude(estado='CANCELADA').count()
    citas_finalizadas  = citas_mes_qs.filter(estado='FINALIZADA').count()
    citas_canceladas   = citas_mes_qs.filter(estado='CANCELADA').count()
    citas_pendientes   = citas_mes_qs.filter(estado='PENDIENTE').count()
    citas_hoy          = Cita.objects.filter(fecha=hoy).exclude(estado='CANCELADA').count()

    total_clientes = PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count()
    total_barberos = Barbero.objects.filter(estado='ACTIVO').count()

    ingresos_mes = citas_mes_qs.filter(
        estado='FINALIZADA'
    ).aggregate(total=Sum('precio'))['total'] or 0

    ingresos_total = Cita.objects.filter(
        estado='FINALIZADA'
    ).aggregate(total=Sum('precio'))['total'] or 0

    # Top 5 servicios del mes
    servicios_top = citas_mes_qs.filter(
        estado='FINALIZADA'
    ).values('servicio__nombre').annotate(
        total=Count('id'),
        ingresos=Sum('precio'),
    ).order_by('-total')[:5]

    # Top barberos del mes
    barberos_top = citas_mes_qs.filter(
        estado='FINALIZADA'
    ).values(
        'barbero__perfil__usuario__first_name',
        'barbero__perfil__usuario__last_name',
    ).annotate(
        total=Count('id'),
        ingresos=Sum('precio'),
    ).order_by('-total')[:5]

    # Calificaciones (históricas, no filtradas por mes)
    calificaciones_barbero = Calificacion.objects.values(
        'barbero__perfil__usuario__first_name',
        'barbero__perfil__usuario__last_name',
    ).annotate(promedio=Avg('puntuacion'), total=Count('id')).order_by('-promedio')

    # Lista de años disponibles para el selector (desde el primer registro)
    primera_cita = Cita.objects.order_by('fecha').first()
    anio_inicio  = primera_cita.fecha.year if primera_cita else hoy.year
    anios_disponibles = list(range(anio_inicio, hoy.year + 1))

    MESES_ES = [
        (1,'Enero'),(2,'Febrero'),(3,'Marzo'),(4,'Abril'),
        (5,'Mayo'),(6,'Junio'),(7,'Julio'),(8,'Agosto'),
        (9,'Septiembre'),(10,'Octubre'),(11,'Noviembre'),(12,'Diciembre'),
    ]

    contexto = {
        'mes_sel':   mes,
        'anio_sel':  anio,
        'mes_nombre': dict(MESES_ES)[mes],
        'anios_disponibles': anios_disponibles,
        'meses': MESES_ES,
        'citas_hoy':          citas_hoy,
        'citas_mes':          citas_mes,
        'citas_finalizadas':  citas_finalizadas,
        'citas_canceladas':   citas_canceladas,
        'citas_pendientes':   citas_pendientes,
        'total_clientes':     total_clientes,
        'total_barberos':     total_barberos,
        'ingresos_mes':       ingresos_mes,
        'ingresos_total':     ingresos_total,
        'servicios_top':      servicios_top,
        'barberos_top':       barberos_top,
        'calificaciones_barbero': calificaciones_barbero,
    }
    return render(request, 'agenda/admin/reportes.html', contexto)


@login_required
@admin_required
def reportes_pdf_view(request):
    """Genera y descarga el reporte mensual en PDF."""
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )
    from datetime import date as date_type
    import calendar

    hoy = timezone.localdate()
    try:
        anio = int(request.GET.get('anio', hoy.year))
        mes  = int(request.GET.get('mes',  hoy.month))
        if not (1 <= mes <= 12):
            raise ValueError
    except (ValueError, TypeError):
        anio, mes = hoy.year, hoy.month

    ultimo_dia = calendar.monthrange(anio, mes)[1]
    inicio_mes = date_type(anio, mes, 1)
    fin_mes    = date_type(anio, mes, ultimo_dia)

    MESES_ES = {
        1:'Enero',2:'Febrero',3:'Marzo',4:'Abril',5:'Mayo',6:'Junio',
        7:'Julio',8:'Agosto',9:'Septiembre',10:'Octubre',11:'Noviembre',12:'Diciembre'
    }
    mes_nombre = MESES_ES[mes]

    citas_mes_qs = Cita.objects.filter(fecha__range=(inicio_mes, fin_mes))
    citas_total      = citas_mes_qs.count()
    citas_finalizadas= citas_mes_qs.filter(estado='FINALIZADA').count()
    citas_canceladas = citas_mes_qs.filter(estado='CANCELADA').count()
    citas_pendientes = citas_mes_qs.filter(estado='PENDIENTE').count()
    ingresos_mes     = citas_mes_qs.filter(estado='FINALIZADA').aggregate(t=Sum('precio'))['t'] or 0

    servicios_top = list(citas_mes_qs.filter(estado='FINALIZADA').values('servicio__nombre').annotate(
        total=Count('id'), ingresos=Sum('precio')
    ).order_by('-total')[:5])

    barberos_top = list(citas_mes_qs.filter(estado='FINALIZADA').values(
        'barbero__perfil__usuario__first_name',
        'barbero__perfil__usuario__last_name',
    ).annotate(total=Count('id'), ingresos=Sum('precio')).order_by('-total')[:5])

    # ── Construcción del PDF ─────────────────────────────────────────────
    buffer = BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    GOLD   = colors.HexColor('#e9c349')
    DARK   = colors.HexColor('#121414')
    GREY   = colors.HexColor('#c4c7c7')
    DGREY  = colors.HexColor('#333535')
    WHITE  = colors.white

    styles = getSampleStyleSheet()
    h1  = ParagraphStyle('h1',  fontName='Helvetica-Bold', fontSize=20, textColor=GOLD,   spaceAfter=4)
    h2  = ParagraphStyle('h2',  fontName='Helvetica-Bold', fontSize=12, textColor=WHITE,  spaceBefore=14, spaceAfter=6)
    sub = ParagraphStyle('sub', fontName='Helvetica',      fontSize=9,  textColor=GREY,   spaceAfter=12)
    tbl_header = ParagraphStyle('th', fontName='Helvetica-Bold', fontSize=8, textColor=GOLD)
    tbl_cell   = ParagraphStyle('td', fontName='Helvetica',      fontSize=8, textColor=WHITE)

    def cop_fmt(v):
        try:
            return f'$ {int(float(v)):,}'.replace(',', '.') + ' COP'
        except Exception:
            return str(v)

    elements = []

    # Encabezado
    elements.append(Paragraph('BarberHub', h1))
    elements.append(Paragraph(f'Reporte mensual — {mes_nombre} {anio}', sub))
    elements.append(HRFlowable(width='100%', thickness=1, color=GOLD, spaceAfter=12))

    # KPIs
    kpi_data = [
        ['Citas del mes', 'Finalizadas', 'Canceladas', 'Pendientes', 'Ingresos del mes'],
        [str(citas_total), str(citas_finalizadas), str(citas_canceladas),
         str(citas_pendientes), cop_fmt(ingresos_mes)],
    ]
    kpi_table = Table(kpi_data, colWidths=[3.2*cm]*5)
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), DGREY),
        ('BACKGROUND',   (0,1), (-1,1), colors.HexColor('#1e2020')),
        ('TEXTCOLOR',    (0,0), (-1,0), GOLD),
        ('TEXTCOLOR',    (0,1), (-1,1), WHITE),
        ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTNAME',     (0,1), (-1,1), 'Helvetica'),
        ('FONTSIZE',     (0,0), (-1,-1), 8),
        ('ALIGN',        (0,0), (-1,-1), 'CENTER'),
        ('VALIGN',       (0,0), (-1,-1), 'MIDDLE'),
        ('ROWBACKGROUNDS',(0,0),(-1,-1), [DGREY, colors.HexColor('#1e2020')]),
        ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#444748')),
        ('TOPPADDING',   (0,0), (-1,-1), 8),
        ('BOTTOMPADDING',(0,0), (-1,-1), 8),
    ]))
    elements.append(kpi_table)
    elements.append(Spacer(1, 0.5*cm))

    # Servicios más solicitados
    elements.append(Paragraph('Servicios más solicitados', h2))
    if servicios_top:
        s_data = [['Servicio', 'Citas', 'Ingresos']]
        for s in servicios_top:
            s_data.append([
                s['servicio__nombre'],
                str(s['total']),
                cop_fmt(s['ingresos']),
            ])
        s_table = Table(s_data, colWidths=[9*cm, 3*cm, 5*cm])
        s_table.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), DGREY),
            ('TEXTCOLOR',    (0,0), (-1,0), GOLD),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',     (0,0), (-1,-1), 8),
            ('TEXTCOLOR',    (0,1), (-1,-1), WHITE),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.HexColor('#1e2020'), colors.HexColor('#282a2b')]),
            ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#444748')),
            ('ALIGN',        (1,0), (-1,-1), 'CENTER'),
            ('TOPPADDING',   (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ]))
        elements.append(s_table)
    else:
        elements.append(Paragraph('Sin datos para este mes.', sub))

    elements.append(Spacer(1, 0.5*cm))

    # Rendimiento de barberos
    elements.append(Paragraph('Rendimiento de barberos', h2))
    if barberos_top:
        b_data = [['Barbero', 'Citas', 'Ingresos']]
        for b in barberos_top:
            nombre = f"{b['barbero__perfil__usuario__first_name']} {b['barbero__perfil__usuario__last_name']}"
            b_data.append([nombre, str(b['total']), cop_fmt(b['ingresos'])])
        b_table = Table(b_data, colWidths=[9*cm, 3*cm, 5*cm])
        b_table.setStyle(TableStyle([
            ('BACKGROUND',   (0,0), (-1,0), DGREY),
            ('TEXTCOLOR',    (0,0), (-1,0), GOLD),
            ('FONTNAME',     (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTNAME',     (0,1), (-1,-1), 'Helvetica'),
            ('FONTSIZE',     (0,0), (-1,-1), 8),
            ('TEXTCOLOR',    (0,1), (-1,-1), WHITE),
            ('ROWBACKGROUNDS',(0,1),(-1,-1), [colors.HexColor('#1e2020'), colors.HexColor('#282a2b')]),
            ('GRID',         (0,0), (-1,-1), 0.5, colors.HexColor('#444748')),
            ('ALIGN',        (1,0), (-1,-1), 'CENTER'),
            ('TOPPADDING',   (0,0), (-1,-1), 6),
            ('BOTTOMPADDING',(0,0), (-1,-1), 6),
        ]))
        elements.append(b_table)
    else:
        elements.append(Paragraph('Sin datos para este mes.', sub))

    # Pie de página
    elements.append(Spacer(1, 1*cm))
    elements.append(HRFlowable(width='100%', thickness=0.5, color=DGREY))
    elements.append(Paragraph(
        f'Generado el {hoy.strftime("%d/%m/%Y")} · BarberHub',
        ParagraphStyle('footer', fontName='Helvetica', fontSize=7, textColor=GREY, spaceBefore=6)
    ))

    doc.build(elements)
    buffer.seek(0)

    from django.http import FileResponse
    filename = f'reporte_barberhub_{mes_nombre.lower()}_{anio}.pdf'
    return FileResponse(buffer, as_attachment=True, filename=filename, content_type='application/pdf')


# ===========================================================================
# GESTIÓN DE CLIENTES
# ===========================================================================

@login_required
@admin_required
def clientes_view(request):
    """Lista y gestión de clientes registrados."""
    clientes = PerfilUsuario.objects.filter(rol='CLIENTE').select_related('usuario').order_by(
        'usuario__first_name', 'usuario__last_name'
    )

    # Búsqueda
    q = request.GET.get('q', '').strip()
    if q:
        clientes = clientes.filter(
            Q(usuario__first_name__icontains=q) |
            Q(usuario__last_name__icontains=q) |
            Q(usuario__username__icontains=q) |
            Q(usuario__email__icontains=q) |
            Q(telefono__icontains=q)
        )

    # Filtro estado
    estado = request.GET.get('estado', '').strip()
    if estado == 'activo':
        clientes = clientes.filter(activo=True)
    elif estado == 'inactivo':
        clientes = clientes.filter(activo=False)

    # Anotar con total de citas
    clientes = clientes.annotate(total_citas=Count('citas_cliente'))

    contexto = {
        'clientes': clientes,
        'total_clientes': PerfilUsuario.objects.filter(rol='CLIENTE').count(),
        'clientes_activos': PerfilUsuario.objects.filter(rol='CLIENTE', activo=True).count(),
        'clientes_nuevos_mes': PerfilUsuario.objects.filter(
            rol='CLIENTE',
            creado_en__gte=timezone.localdate().replace(day=1)
        ).count(),
        'filtros': {'q': q, 'estado': estado},
    }
    return render(request, 'agenda/admin/clientes.html', contexto)


@login_required
@admin_required
def cliente_toggle(request, pk):
    """
    Activar / desactivar cuenta de cliente.
    Sincroniza PerfilUsuario.activo con User.is_active para que
    un cliente desactivado no pueda autenticarse.
    """
    cliente = get_object_or_404(PerfilUsuario, pk=pk, rol='CLIENTE')
    cliente.activo = not cliente.activo
    cliente.save()

    # Mantener User.is_active en sincronía con el perfil
    cliente.usuario.is_active = cliente.activo
    cliente.usuario.save(update_fields=['is_active'])

    nombre = cliente.usuario.get_full_name() or cliente.usuario.username
    estado = 'activado' if cliente.activo else 'desactivado'
    messages.success(request, f'Cliente "{nombre}" {estado}.')
    return redirect('clientes')


@login_required
@admin_required
def cliente_detalle(request, pk):
    """Detalle de un cliente: historial de citas y estadísticas."""
    cliente = get_object_or_404(PerfilUsuario, pk=pk, rol='CLIENTE')

    citas = Cita.objects.filter(cliente=cliente).select_related(
        'barbero__perfil__usuario', 'servicio'
    ).order_by('-fecha', '-hora_inicio')

    total_gastado = citas.filter(estado='FINALIZADA').aggregate(
        total=Sum('precio')
    )['total'] or 0

    contexto = {
        'cliente': cliente,
        'citas': citas,
        'total_citas': citas.count(),
        'citas_finalizadas': citas.filter(estado='FINALIZADA').count(),
        'citas_canceladas': citas.filter(estado='CANCELADA').count(),
        'total_gastado': total_gastado,
    }
    return render(request, 'agenda/admin/cliente_detalle.html', contexto)


# ===========================================================================
# VALIDAR COMPROBANTE (QR / CÓDIGO MANUAL)
# ===========================================================================

@login_required
@admin_required
def validar_comprobante_view(request):
    """
    Valida un comprobante por código de reserva (ingresado manualmente o leído por QR).
    - Solo admins pueden acceder.
    - Valida el formato antes de consultar la BD.
    - Nunca expone stack traces ni información sensible.
    - No modifica la cita bajo ninguna circunstancia.
    """
    from ..services import CitasService

    cita           = None
    codigo_buscado = ''
    error          = None

    if request.method == 'POST':
        codigo_raw     = request.POST.get('codigo', '')
        codigo_buscado = codigo_raw.strip().upper()

        if not codigo_buscado:
            error = 'Ingresa un código de reserva.'

        elif not CitasService.es_codigo_valido(codigo_buscado):
            # Rechazar formatos inválidos sin consultar la BD
            error = (
                f'El código "{codigo_buscado}" no tiene un formato válido. '
                'El formato correcto es BH-XXXXXX (ej: BH-000042).'
            )

        else:
            try:
                cita = Cita.objects.select_related(
                    'cliente__usuario', 'barbero__perfil__usuario', 'servicio'
                ).get(codigo_reserva=codigo_buscado)
            except Cita.DoesNotExist:
                error = f'No se encontró ninguna reserva con el código "{codigo_buscado}".'
            except Exception:
                # Captura cualquier error de BD sin exponer detalles técnicos
                error = 'Ocurrió un error al consultar la reserva. Intenta de nuevo.'

    return render(request, 'agenda/admin/validar_comprobante.html', {
        'cita':           cita,
        'codigo_buscado': codigo_buscado,
        'error':          error,
    })


# ===========================================================================
# CONFIGURACIÓN DE BARBERÍA
# ===========================================================================

@login_required
@admin_required
def configuracion_view(request):
    """Ver y editar configuración de la barbería (singleton)."""
    config, _ = ConfiguracionBarberia.objects.get_or_create(
        pk=1,
        defaults={'nombre': 'BarberHub'}
    )
    form = ConfiguracionBarberiaForm(
        request.POST or None,
        request.FILES or None,
        instance=config
    )
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Configuración guardada correctamente.')
        return redirect('configuracion')

    return render(request, 'agenda/admin/configuracion.html', {'form': form, 'config': config})
