"""
Management command: seed
Uso: python manage.py seed
     python manage.py seed --flush   (limpia datos previos antes de insertar)

Crea datos de prueba coherentes y realistas para BarberHub:
  - 1 admin
  - 4 barberos con especialidades distintas
  - 10 clientes
  - 4 servicios
  - Horarios semanales (lunes-sábado)
  - 40 citas distribuidas en las últimas 4 semanas y próximas 2 semanas
  - Calificaciones para las citas finalizadas
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date, time, timedelta
from decimal import Decimal

from agenda.models import (
    PerfilUsuario, Barbero, Servicio, Horario, Cita, Calificacion,
    ConfiguracionBarberia,
)


# ---------------------------------------------------------------------------
# Datos maestros
# ---------------------------------------------------------------------------

SERVICIOS_DATA = [
    {
        'nombre': 'Corte Clásico',
        'descripcion': 'Corte tradicional con tijera y máquina, acabado impecable.',
        'precio': Decimal('25.00'),
        'duracion': 45,
    },
    {
        'nombre': 'Corte Degradado (Fade)',
        'descripcion': 'Degradado de alta precisión con distintos niveles de máquina.',
        'precio': Decimal('30.00'),
        'duracion': 60,
    },
    {
        'nombre': 'Arreglo de Barba',
        'descripcion': 'Perfilado con navaja, toalla caliente y aceite hidratante.',
        'precio': Decimal('20.00'),
        'duracion': 30,
    },
    {
        'nombre': 'Corte + Barba',
        'descripcion': 'Experiencia completa: corte clásico y arreglo de barba con ritual de toalla.',
        'precio': Decimal('45.00'),
        'duracion': 75,
    },
]

BARBEROS_DATA = [
    {
        'username': 'marco.rossi',
        'first_name': 'Marco',
        'last_name': 'Rossi',
        'email': 'marco.rossi@barberhub.co',
        'telefono': '+57 312 100 0001',
        'especialidad': 'Master Barber — Cortes clásicos y degradados',
        'descripcion': 'Con más de 10 años de experiencia, Marco domina técnicas europeas y latinoamericanas.',
        'servicios': ['Corte Clásico', 'Corte Degradado (Fade)', 'Corte + Barba'],
    },
    {
        'username': 'alex.chen',
        'first_name': 'Alex',
        'last_name': 'Chen',
        'email': 'alex.chen@barberhub.co',
        'telefono': '+57 312 100 0002',
        'especialidad': 'Fading Expert — Degradados y diseños modernos',
        'descripcion': 'Especialista en fades de alta precisión y diseños creativos con navaja.',
        'servicios': ['Corte Degradado (Fade)', 'Corte + Barba'],
    },
    {
        'username': 'julian.mora',
        'first_name': 'Julián',
        'last_name': 'Mora',
        'email': 'julian.mora@barberhub.co',
        'telefono': '+57 312 100 0003',
        'especialidad': 'Classic Specialist — Barba y afeitado tradicional',
        'descripcion': 'Maestro del afeitado clásico con navaja y especialista en cuidado de barba.',
        'servicios': ['Corte Clásico', 'Arreglo de Barba', 'Corte + Barba'],
    },
    {
        'username': 'santi.ruiz',
        'first_name': 'Santiago',
        'last_name': 'Ruiz',
        'email': 'santi.ruiz@barberhub.co',
        'telefono': '+57 312 100 0004',
        'especialidad': 'Creative Stylist — Estilos urbanos y tendencias',
        'descripcion': 'El más joven del equipo, especializado en tendencias urbanas y estilos contemporáneos.',
        'servicios': ['Corte Clásico', 'Corte Degradado (Fade)', 'Arreglo de Barba', 'Corte + Barba'],
    },
]

CLIENTES_DATA = [
    ('carlos.gutierrez',  'Carlos',    'Gutiérrez',  'carlos.g@gmail.com',      '+57 300 111 2233'),
    ('andres.lopez',      'Andrés',    'López',       'andres.l@hotmail.com',    '+57 301 222 3344'),
    ('roberto.vargas',    'Roberto',   'Vargas',      'roberto.v@gmail.com',     '+57 302 333 4455'),
    ('miguel.torres',     'Miguel',    'Torres',      'miguel.t@outlook.com',    '+57 303 444 5566'),
    ('david.ramirez',     'David',     'Ramírez',     'david.r@gmail.com',       '+57 304 555 6677'),
    ('juan.perez',        'Juan',      'Pérez',       'juan.p@gmail.com',        '+57 305 666 7788'),
    ('nicolas.herrera',   'Nicolás',   'Herrera',     'nicolas.h@yahoo.com',     '+57 306 777 8899'),
    ('felipe.castro',     'Felipe',    'Castro',      'felipe.c@gmail.com',      '+57 307 888 9900'),
    ('sebastian.rojas',   'Sebastián', 'Rojas',       'sebastian.r@gmail.com',   '+57 308 999 0011'),
    ('camilo.mendez',     'Camilo',    'Méndez',      'camilo.m@outlook.com',    '+57 309 000 1122'),
]

COMENTARIOS_POSITIVOS = [
    "Excelente servicio, el mejor corte que me han hecho en años.",
    "Marco es un artista, salí muy satisfecho con el resultado.",
    "El ambiente de la barbería es increíble, volveré sin duda.",
    "El degradado quedó perfecto, exactamente lo que pedí.",
    "Muy profesional y atento. La barba quedó impecable.",
    "El ritual de toalla caliente fue una experiencia increíble.",
    "Puntual, limpio y excelente resultado. 100% recomendado.",
    "Santi entendió perfectamente lo que quería. Gran trabajo.",
    "Primera vez aquí y ya soy cliente fijo. El nivel es muy alto.",
    "Julián es un maestro con la navaja. Mi barba nunca había lucido así.",
]


class Command(BaseCommand):
    help = 'Crea datos de prueba realistas y coherentes para BarberHub'

    def add_arguments(self, parser):
        parser.add_argument(
            '--flush',
            action='store_true',
            help='Elimina todos los datos existentes antes de insertar',
        )

    def handle(self, *args, **options):
        if options['flush']:
            self.stdout.write(self.style.WARNING('⚠  Eliminando datos existentes...'))
            Calificacion.objects.all().delete()
            Cita.objects.all().delete()
            Horario.objects.all().delete()
            Barbero.objects.all().delete()
            PerfilUsuario.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Servicio.objects.all().delete()
            ConfiguracionBarberia.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('   Datos eliminados.\n'))

        self._crear_configuracion()
        servicios = self._crear_servicios()
        self._crear_admin()
        barberos = self._crear_barberos(servicios)
        clientes = self._crear_clientes()
        self._crear_horarios()
        citas = self._crear_citas(barberos, clientes, servicios)
        self._crear_calificaciones(citas, clientes)

        self.stdout.write(self.style.SUCCESS('\n✅  Seed completado exitosamente.'))
        self.stdout.write('   Admin:    admin / admin1234')
        self.stdout.write('   Barbero:  marco.rossi / barber1234')
        self.stdout.write('   Cliente:  carlos.gutierrez / cliente1234\n')

    # -----------------------------------------------------------------------
    # Configuración de la barbería
    # -----------------------------------------------------------------------
    def _crear_configuracion(self):
        obj, created = ConfiguracionBarberia.objects.get_or_create(
            id=1,
            defaults={
                'nombre': 'BarberHub Premium',
                'descripcion': 'La mejor barbería premium de la ciudad.',
                'direccion': 'Calle 123 #45-67, Bogotá, Colombia',
                'telefono': '+57 310 000 0000',
                'correo': 'hola@barberhub.co',
                'instagram': 'https://instagram.com/barberhub',
                'whatsapp': '+573100000000',
            }
        )
        label = 'creada' if created else 'ya existe'
        self.stdout.write(f'  Configuración barbería: {label}')

    # -----------------------------------------------------------------------
    # Servicios
    # -----------------------------------------------------------------------
    def _crear_servicios(self):
        servicios = {}
        self.stdout.write('\n📋 Servicios:')
        for data in SERVICIOS_DATA:
            obj, created = Servicio.objects.get_or_create(
                nombre=data['nombre'],
                defaults={
                    'descripcion': data['descripcion'],
                    'precio': data['precio'],
                    'duracion': data['duracion'],
                    'activo': True,
                }
            )
            servicios[obj.nombre] = obj
            label = '✔' if created else '—'
            self.stdout.write(f'  {label} {obj.nombre} (${obj.precio}, {obj.duracion} min)')
        return servicios

    # -----------------------------------------------------------------------
    # Admin
    # -----------------------------------------------------------------------
    def _crear_admin(self):
        self.stdout.write('\n👑 Admin:')
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser(
                username='admin',
                email='admin@barberhub.co',
                password='admin1234',
                first_name='Admin',
                last_name='BarberHub',
            )
            PerfilUsuario.objects.create(
                usuario=user,
                telefono='+57 310 000 0000',
                rol='ADMIN',
                activo=True,
            )
            self.stdout.write('  ✔ admin creado')
        else:
            self.stdout.write('  — admin ya existe')

    # -----------------------------------------------------------------------
    # Barberos
    # -----------------------------------------------------------------------
    def _crear_barberos(self, servicios):
        self.stdout.write('\n✂  Barberos:')
        barberos = []
        for data in BARBEROS_DATA:
            if not User.objects.filter(username=data['username']).exists():
                user = User.objects.create_user(
                    username=data['username'],
                    email=data['email'],
                    password='barber1234',
                    first_name=data['first_name'],
                    last_name=data['last_name'],
                )
                perfil = PerfilUsuario.objects.create(
                    usuario=user,
                    telefono=data['telefono'],
                    rol='BARBERO',
                    activo=True,
                )
                barbero = Barbero.objects.create(
                    perfil=perfil,
                    especialidad=data['especialidad'],
                    descripcion=data['descripcion'],
                    estado='ACTIVO',
                )
                # Asignar servicios válidos
                for nombre_servicio in data['servicios']:
                    if nombre_servicio in servicios:
                        barbero.servicios.add(servicios[nombre_servicio])
                barberos.append(barbero)
                self.stdout.write(f'  ✔ {data["first_name"]} {data["last_name"]} — {len(data["servicios"])} servicios')
            else:
                barbero = Barbero.objects.get(perfil__usuario__username=data['username'])
                barberos.append(barbero)
                self.stdout.write(f'  — {data["first_name"]} {data["last_name"]} ya existe')
        return barberos

    # -----------------------------------------------------------------------
    # Clientes
    # -----------------------------------------------------------------------
    def _crear_clientes(self):
        self.stdout.write('\n👤 Clientes:')
        clientes = []
        for username, first, last, email, telefono in CLIENTES_DATA:
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='cliente1234',
                    first_name=first,
                    last_name=last,
                )
                perfil = PerfilUsuario.objects.create(
                    usuario=user,
                    telefono=telefono,
                    rol='CLIENTE',
                    activo=True,
                )
                clientes.append(perfil)
                self.stdout.write(f'  ✔ {first} {last}')
            else:
                perfil = PerfilUsuario.objects.get(usuario__username=username)
                clientes.append(perfil)
                self.stdout.write(f'  — {first} {last} ya existe')
        return clientes

    # -----------------------------------------------------------------------
    # Horarios semanales
    # Lun-Vie: 09:00-20:00  |  Sáb: 09:00-18:00  |  Dom: cerrado
    # -----------------------------------------------------------------------
    def _crear_horarios(self):
        self.stdout.write('\n🕐 Horarios:')
        if Horario.objects.exists():
            self.stdout.write('  — Horarios ya existen, se omiten')
            return

        semana = [
            (0, time(9, 0),  time(20, 0), True),   # Lunes
            (1, time(9, 0),  time(20, 0), True),   # Martes
            (2, time(9, 0),  time(20, 0), True),   # Miércoles
            (3, time(9, 0),  time(20, 0), True),   # Jueves
            (4, time(9, 0),  time(20, 0), True),   # Viernes
            (5, time(9, 0),  time(18, 0), True),   # Sábado
            (6, time(9, 0),  time(18, 0), False),  # Domingo cerrado
        ]
        DIAS = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        for dia, inicio, fin, abierto in semana:
            Horario.objects.create(
                dia_semana=dia,
                hora_inicio=inicio,
                hora_fin=fin,
                abierto=abierto,
                motivo_bloqueo=None if abierto else 'Domingo — día de descanso',
            )
            estado = f'{inicio.strftime("%H:%M")}–{fin.strftime("%H:%M")}' if abierto else 'Cerrado'
            self.stdout.write(f'  ✔ {DIAS[dia]}: {estado}')

    # -----------------------------------------------------------------------
    # Citas
    # Plan: 40 citas en un rango de -4 semanas a +2 semanas desde hoy.
    # Estados: pasadas=FINALIZADA/CANCELADA, futuras=PENDIENTE/CONFIRMADA
    # Se evitan solapamientos por barbero en el mismo día/hora.
    # -----------------------------------------------------------------------
    def _crear_citas(self, barberos, clientes, servicios):
        self.stdout.write('\n📅 Citas:')
        if Cita.objects.exists():
            self.stdout.write('  — Citas ya existen, se omiten')
            return []

        hoy = timezone.localdate()

        # Plan de citas: (días_desde_hoy, hora, barbero_idx, cliente_idx, servicio_nombre, estado)
        # Días negativos = pasado, positivos = futuro
        plan = [
            # — SEMANA -4 —
            (-28, time(9, 0),  0, 0, 'Corte Clásico',          'FINALIZADA'),
            (-28, time(10, 0), 1, 1, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-28, time(11, 0), 2, 2, 'Arreglo de Barba',        'FINALIZADA'),
            (-27, time(9, 0),  3, 3, 'Corte + Barba',           'FINALIZADA'),
            (-27, time(10, 30),0, 4, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-26, time(9, 0),  1, 5, 'Corte Clásico',           'FINALIZADA'),
            (-26, time(11, 0), 2, 6, 'Corte + Barba',           'FINALIZADA'),
            (-25, time(9, 0),  0, 7, 'Arreglo de Barba',        'FINALIZADA'),
            (-25, time(14, 0), 3, 8, 'Corte Clásico',           'FINALIZADA'),
            (-24, time(10, 0), 1, 9, 'Corte Degradado (Fade)',  'FINALIZADA'),
            # — SEMANA -3 —
            (-21, time(9, 0),  0, 0, 'Corte + Barba',           'FINALIZADA'),
            (-21, time(11, 0), 2, 1, 'Corte Clásico',           'FINALIZADA'),
            (-20, time(9, 30), 3, 2, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-20, time(14, 0), 1, 3, 'Arreglo de Barba',        'FINALIZADA'),
            (-19, time(10, 0), 0, 4, 'Corte Clásico',           'FINALIZADA'),
            (-19, time(16, 0), 2, 5, 'Corte + Barba',           'CANCELADA'),
            (-18, time(9, 0),  1, 6, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-17, time(11, 0), 3, 7, 'Corte Clásico',           'FINALIZADA'),
            (-17, time(14, 30),0, 8, 'Arreglo de Barba',        'FINALIZADA'),
            (-16, time(10, 0), 2, 9, 'Corte + Barba',           'FINALIZADA'),
            # — SEMANA -2 —
            (-14, time(9, 0),  0, 0, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-14, time(10, 30),1, 1, 'Corte + Barba',           'FINALIZADA'),
            (-13, time(9, 0),  2, 2, 'Corte Clásico',           'FINALIZADA'),
            (-13, time(11, 0), 3, 3, 'Arreglo de Barba',        'FINALIZADA'),
            (-12, time(9, 0),  0, 4, 'Corte + Barba',           'FINALIZADA'),
            (-11, time(14, 0), 1, 5, 'Corte Clásico',           'FINALIZADA'),
            (-10, time(10, 0), 2, 6, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-10, time(16, 0), 3, 7, 'Corte Clásico',           'CANCELADA'),
            # — SEMANA -1 —
            (-7,  time(9, 0),  0, 0, 'Corte Clásico',           'FINALIZADA'),
            (-7,  time(10, 30),1, 1, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-6,  time(9, 0),  2, 2, 'Corte + Barba',           'FINALIZADA'),
            (-5,  time(11, 0), 3, 3, 'Arreglo de Barba',        'FINALIZADA'),
            (-4,  time(9, 0),  0, 4, 'Corte Degradado (Fade)',  'FINALIZADA'),
            (-3,  time(14, 0), 1, 5, 'Corte + Barba',           'FINALIZADA'),
            # — PRÓXIMAS —
            (1,   time(9, 0),  0, 6, 'Corte Clásico',           'CONFIRMADA'),
            (1,   time(10, 30),1, 7, 'Corte Degradado (Fade)',  'PENDIENTE'),
            (2,   time(9, 0),  2, 8, 'Corte + Barba',           'CONFIRMADA'),
            (3,   time(11, 0), 3, 9, 'Arreglo de Barba',        'PENDIENTE'),
            (5,   time(9, 0),  0, 0, 'Corte + Barba',           'PENDIENTE'),
            (7,   time(14, 0), 1, 1, 'Corte Clásico',           'PENDIENTE'),
        ]

        citas_creadas = []
        servicios_map = {s.nombre: s for s in Servicio.objects.all()}

        for dias, hora, b_idx, c_idx, servicio_nombre, estado in plan:
            fecha = hoy + timedelta(days=dias)
            # Saltar domingos (día 6 = domingo en Python, weekday())
            if fecha.weekday() == 6:
                fecha += timedelta(days=1)

            servicio = servicios_map.get(servicio_nombre)
            if not servicio:
                continue

            barbero = barberos[b_idx % len(barberos)]
            cliente = clientes[c_idx % len(clientes)]

            # Calcular hora_fin según duración del servicio
            from datetime import datetime as dt
            inicio_dt = dt.combine(fecha, hora)
            fin_dt = inicio_dt + timedelta(minutes=servicio.duracion)
            hora_fin = fin_dt.time()

            # Verificar que no haya solapamiento con otra cita del mismo barbero
            solapamiento = Cita.objects.filter(
                barbero=barbero,
                fecha=fecha,
                hora_inicio__lt=hora_fin,
                hora_fin__gt=hora,
            ).exclude(estado='CANCELADA').exists()

            if solapamiento:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Solapamiento omitido: {barbero} el {fecha} a las {hora}')
                )
                continue

            cita = Cita.objects.create(
                cliente=cliente,
                barbero=barbero,
                servicio=servicio,
                fecha=fecha,
                hora_inicio=hora,
                hora_fin=hora_fin,
                precio=servicio.precio,
                estado=estado,
                observaciones=None,
            )
            citas_creadas.append(cita)

        self.stdout.write(f'  ✔ {len(citas_creadas)} citas creadas')
        return citas_creadas

    # -----------------------------------------------------------------------
    # Calificaciones — solo para citas FINALIZADAS
    # -----------------------------------------------------------------------
    def _crear_calificaciones(self, citas, clientes):
        self.stdout.write('\n⭐ Calificaciones:')
        if Calificacion.objects.exists():
            self.stdout.write('  — Calificaciones ya existen, se omiten')
            return

        finalizadas = Cita.objects.filter(estado='FINALIZADA').select_related(
            'cliente', 'barbero'
        )

        # Puntuaciones realistas: mayoría 5, algunos 4, raramente 3
        puntuaciones = [5, 5, 5, 5, 4, 5, 5, 4, 5, 3, 5, 5, 4, 5, 5, 5, 4, 5, 5, 5]
        comentarios_ciclo = COMENTARIOS_POSITIVOS

        creadas = 0
        for i, cita in enumerate(finalizadas):
            # No todas las citas tienen calificación (80% de probabilidad simulada)
            if i % 5 == 4:  # Omite cada quinta cita — simula que no todos califican
                continue
            puntuacion = puntuaciones[i % len(puntuaciones)]
            comentario = comentarios_ciclo[i % len(comentarios_ciclo)] if puntuacion >= 4 else None

            Calificacion.objects.get_or_create(
                cita=cita,
                defaults={
                    'cliente': cita.cliente,
                    'barbero': cita.barbero,
                    'puntuacion': puntuacion,
                    'comentario': comentario,
                }
            )
            creadas += 1

        self.stdout.write(f'  ✔ {creadas} calificaciones creadas')
