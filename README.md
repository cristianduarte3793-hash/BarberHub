# 💈 BarberHub - Sistema de Agendamiento de Citas

Sistema profesional de gestión de citas para barberías desarrollado con Django siguiendo arquitectura MVC con capa de servicios.

## 🏗️ Arquitectura del Proyecto

```
Agenda_Barberhub/
├── agenda/                       # 📦 Aplicación principal
│   ├── __init__.py
│   ├── apps.py
│   ├── admin.py                  # Panel de administración Django
│   ├── urls.py                   # 🔀 Enrutador (URLs → Controladores)
│   ├── forms.py                  # Formularios Django
│   ├── utils.py                  # Decoradores y helpers
│   ├── context_processors.py     # Context processors
│   │
│   ├── models/                   # 🗄️ MODELOS (La "M" en MVC)
│   │   ├── __init__.py          # Exporta todos los modelos
│   │   ├── usuarios.py           # PerfilUsuario
│   │   ├── barberos.py           # Barbero, Servicio
│   │   ├── citas.py              # Cita, Calificacion, Horario
│   │   └── configuracion.py      # ConfiguracionBarberia
│   │
│   ├── views/                    # 🎮 CONTROLADORES (La "C" en MVC)
│   │   ├── __init__.py          # Exporta todas las vistas
│   │   ├── auth.py               # Login, Logout, Registro, Landing
│   │   ├── comunes.py            # Dashboard, Perfil
│   │   ├── cliente.py            # Agendar, ver y cancelar citas
│   │   ├── admin.py              # Gestión admin (servicios, horarios)
│   │   └── barbero.py            # Dashboard barbero, agenda
│   │
│   ├── services/                 # ⚙️ LÓGICA DE NEGOCIO (Service Layer)
│   │   ├── __init__.py
│   │   ├── citas_service.py      # Validaciones y lógica de citas
│   │   └── horarios_service.py   # Lógica de horarios
│   │
│   ├── templates/                # 🎨 VISTAS / INTERFAZ (La "V" en MVC)
│   │   ├── base.html
│   │   ├── landing.html
│   │   ├── login.html
│   │   ├── registro.html
│   │   ├── dashboard.html
│   │   ├── perfil.html
│   │   ├── cambiar_password.html
│   │   ├── agendar_cita.html
│   │   ├── mis_citas.html
│   │   ├── barberos.html
│   │   ├── admin/               # Templates de administración
│   │   └── barbero/             # Templates de barbero
│   │
│   ├── management/              # Comandos personalizados Django
│   │   └── commands/
│   │       └── seed.py           # Poblar BD con datos de prueba
│   │
│   ├── migrations/              # Migraciones de base de datos
│   └── templatetags/            # Template tags personalizados
│       └── barberhub_filters.py
│
├── Agenda_Barberhub/            # ⚙️ Configuración del proyecto
│   ├── settings.py               # Configuración principal
│   ├── urls.py                   # URLs raíz del proyecto
│   ├── wsgi.py
│   └── asgi.py
│
├── static/                      # 🎨 Archivos estáticos (CSS, JS, img)
│   ├── css/
│   │   └── barberhub.css
│   └── js/
│       └── barberhub.js
│
├── media/                       # 📁 Archivos subidos por usuarios
│   └── perfiles/
│
├── templates/                   # 🖼️ Templates globales
│
├── manage.py                    # Script de gestión Django
├── requirements.txt             # Dependencias Python
├── .env                         # Variables de entorno (NO subir a git)
├── .env.example                 # Ejemplo de variables de entorno
└── .gitignore                   # Archivos ignorados por git
```

## 🚀 Características

### 👥 Sistema de Roles
- **Administrador**: Gestión completa del sistema
- **Barbero**: Visualización de agenda y gestión de citas propias
- **Cliente**: Agendamiento y seguimiento de citas

### 📅 Gestión de Citas
- Agendamiento con validación de disponibilidad
- Estados: Pendiente, Confirmada, En Proceso, Finalizada, Cancelada
- Visualización de agenda por día, semana y mes
- Sistema de calificaciones

### ⚙️ Funcionalidades Admin
- Gestión de barberos y sus servicios
- Configuración de horarios semanales y especiales
- Reportes y estadísticas
- Gestión de servicios y precios

### 📊 Dashboard Inteligente
- Métricas en tiempo real según el rol
- Próximas citas y alertas
- Estadísticas de rendimiento

## 🛠️ Tecnologías

- **Backend**: Django 5.1.4
- **Base de Datos**: MySQL 8.4
- **Frontend**: HTML5, TailwindCSS, JavaScript
- **Autenticación**: Django Auth
- **ORM**: Django ORM

## ⚡ Instalación y Configuración

### 1. Clonar el repositorio
```bash
git clone <url-repo>
cd Agenda_Barberhub
```

### 2. Crear entorno virtual
```bash
python -m venv venv
```

### 3. Activar entorno virtual
**Windows:**
```bash
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 5. Configurar variables de entorno
Copiar `.env.example` a `.env` y configurar:
```env
SECRET_KEY=tu-clave-secreta-aqui
DEBUG=True
DB_NAME=barberhub
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

### 6. Crear base de datos
En MySQL:
```sql
CREATE DATABASE barberhub CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 7. Ejecutar migraciones
```bash
python manage.py migrate
```

### 8. Cargar datos de prueba (opcional)
```bash
python manage.py seed
```

### 9. Crear superusuario
```bash
python manage.py createsuperuser
```

### 10. Iniciar servidor
```bash
python manage.py runserver
```

Visitar: `http://127.0.0.1:8000/`

## 📖 Guía de Desarrollo

### Agregar un nuevo modelo
1. Crear en `agenda/models/nuevo_modelo.py`
2. Exportar en `agenda/models/__init__.py`
3. Importar en `agenda/models.py` para compatibilidad
4. Ejecutar migraciones: `python manage.py makemigrations && python manage.py migrate`

### Agregar lógica de negocio
1. Crear servicio en `agenda/services/nuevo_service.py`
2. Exportar en `agenda/services/__init__.py`
3. Usar desde las vistas:
```python
from agenda.services import NuevoService
resultado = NuevoService.metodo()
```

### Agregar una nueva vista
1. Identificar el módulo correcto en `agenda/views/`
2. Crear la función de vista
3. Exportar en `agenda/views/__init__.py`
4. Agregar ruta en `agenda/urls.py`
5. Crear template en `templates/`

## 🎯 Patrones y Convenciones

### Estructura MVC + Services
- **Modelos** (`models/`): Representan la base de datos
- **Vistas** (`templates/`): Interfaz de usuario
- **Controladores** (`views/`): Lógica de presentación
- **Servicios** (`services/`): Lógica de negocio compleja

### Decoradores de Seguridad
```python
@login_required              # Requiere autenticación
@admin_required             # Solo administradores
@barbero_required          # Solo barberos
@cliente_required          # Solo clientes
```

### Helpers de Rol
```python
es_admin(user)      # Verifica si es administrador
es_barbero(user)    # Verifica si es barbero
es_cliente(user)    # Verifica si es cliente
```

## 📝 Comandos Útiles

```bash
# Crear migraciones
python manage.py makemigrations

# Aplicar migraciones
python manage.py migrate

# Cargar datos de prueba
python manage.py seed

# Crear superusuario
python manage.py createsuperuser

# Ejecutar servidor de desarrollo
python manage.py runserver

# Abrir shell de Django
python manage.py shell

# Colectar archivos estáticos (producción)
python manage.py collectstatic
```

## 🔒 Seguridad

- Contraseñas hasheadas con Django Auth
- Protección CSRF activada
- Validación de roles en todas las vistas
- Variables sensibles en `.env` (no versionado)

## 📄 Licencia

Este proyecto es de uso privado.

## 👨‍💻 Autor

Cristian - Proyecto BarberHub

---

**Nota**: Para más detalles sobre la estructura de cada módulo, consulta los README específicos en cada carpeta.
