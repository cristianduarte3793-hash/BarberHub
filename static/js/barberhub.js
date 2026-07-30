/**
 * BarberHub — Scripts principales
 */

document.addEventListener('DOMContentLoaded', function () {

  // ─── Toggle del sidebar ───────────────────────────────────
  const sidebar = document.getElementById('sidebar');
  const mainContent = document.getElementById('main-content');
  const toggleBtn = document.getElementById('sidebar-toggle');

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      if (window.innerWidth <= 768) {
        sidebar.classList.toggle('mobile-open');
      } else {
        sidebar.classList.toggle('collapsed');
        mainContent.classList.toggle('expanded');
        localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
      }
    });

    // Restaurar estado del sidebar
    const sidebarCollapsed = localStorage.getItem('sidebar-collapsed') === 'true';
    if (sidebarCollapsed && window.innerWidth > 768) {
      sidebar.classList.add('collapsed');
      mainContent.classList.add('expanded');
    }
  }

  // Cerrar sidebar en móvil al hacer clic afuera
  document.addEventListener('click', function (e) {
    if (window.innerWidth <= 768 && sidebar && sidebar.classList.contains('mobile-open')) {
      if (!sidebar.contains(e.target) && e.target !== toggleBtn) {
        sidebar.classList.remove('mobile-open');
      }
    }
  });

  // ─── Auto-cerrar alertas ──────────────────────────────────
  const alerts = document.querySelectorAll('.alert.auto-dismiss');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = new bootstrap.Alert(alert);
      bsAlert.close();
    }, 4000);
  });

  // ─── Confirmación de eliminación ─────────────────────────
  document.querySelectorAll('[data-confirm]').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      const msg = this.getAttribute('data-confirm') || '¿Estás seguro de que deseas continuar?';
      if (!confirm(msg)) {
        e.preventDefault();
      }
    });
  });

  // ─── Sistema de estrellas de calificación ─────────────────
  const starInputs = document.querySelectorAll('.star-rating input');
  starInputs.forEach(function (input) {
    input.addEventListener('change', function () {
      document.getElementById('id_puntuacion').value = this.value;
    });
  });

  // ─── Tooltip de Bootstrap ─────────────────────────────────
  const tooltipTriggers = document.querySelectorAll('[data-bs-toggle="tooltip"]');
  tooltipTriggers.forEach(function (el) {
    new bootstrap.Tooltip(el);
  });

  // ─── Marcar enlace activo en el sidebar ───────────────────
  const currentPath = window.location.pathname;
  document.querySelectorAll('#sidebar .nav-item a').forEach(function (link) {
    if (link.getAttribute('href') === currentPath ||
        (link.getAttribute('href') !== '/' && currentPath.startsWith(link.getAttribute('href')))) {
      link.classList.add('active');
    }
  });

});

// ─── Función para agendar citas (carga dinámica de horarios) ─
function cargarBarberosPorServicio(servicioId) {
  if (!servicioId) return;
  fetch(`/citas/api/barberos-por-servicio/?servicio_id=${servicioId}`)
    .then(r => r.json())
    .then(data => {
      const select = document.getElementById('id_barbero');
      if (!select) return;
      select.innerHTML = '<option value="">-- Selecciona un barbero --</option>';
      data.barberos.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.id;
        opt.textContent = b.nombre + (b.especialidad ? ` (${b.especialidad})` : '');
        select.appendChild(opt);
      });
    });
}

function cargarHorariosDisponibles() {
  const servicioId = document.getElementById('id_servicio')?.value;
  const barberoId  = document.getElementById('id_barbero')?.value;
  const fecha      = document.getElementById('id_fecha')?.value;
  const horaSelect = document.getElementById('id_hora_inicio');

  if (!servicioId || !barberoId || !fecha || !horaSelect) return;

  horaSelect.innerHTML = '<option>Cargando...</option>';
  horaSelect.disabled = true;

  fetch(`/citas/api/horarios-disponibles/?servicio_id=${servicioId}&barbero_id=${barberoId}&fecha=${fecha}`)
    .then(r => r.json())
    .then(data => {
      horaSelect.innerHTML = '';
      if (data.slots && data.slots.length > 0) {
        horaSelect.innerHTML = '<option value="">-- Elige un horario --</option>';
        data.slots.forEach(slot => {
          const opt = document.createElement('option');
          opt.value = slot;
          opt.textContent = slot;
          horaSelect.appendChild(opt);
        });
        horaSelect.disabled = false;
      } else {
        horaSelect.innerHTML = '<option value="">Sin horarios disponibles para esta fecha</option>';
      }
    })
    .catch(() => {
      horaSelect.innerHTML = '<option value="">Error al cargar horarios</option>';
    });
}

// Attachar eventos de agendar si existen los elementos
document.addEventListener('DOMContentLoaded', function () {
  const servicioSel = document.getElementById('id_servicio');
  const barberoSel  = document.getElementById('id_barbero');
  const fechaInp    = document.getElementById('id_fecha');

  if (servicioSel) {
    servicioSel.addEventListener('change', function () {
      cargarBarberosPorServicio(this.value);
      // Resetear horarios al cambiar servicio
      const horaSelect = document.getElementById('id_hora_inicio');
      if (horaSelect) horaSelect.innerHTML = '<option value="">-- Primero selecciona barbero y fecha --</option>';
    });
  }

  if (barberoSel) barberoSel.addEventListener('change', cargarHorariosDisponibles);
  if (fechaInp)   fechaInp.addEventListener('change', cargarHorariosDisponibles);
});
