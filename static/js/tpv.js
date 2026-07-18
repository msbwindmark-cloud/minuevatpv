// ========== TPV CAFETERIA PREMIUM - MULTI-MESA ==========
var pedidosMesa = {};  // { mesaId: { items: {}, nombre: '' } }
var mesaActual = null;
var mesasInfo = {};

function getCookie(name) {
    var value = document.cookie.split('; ').find(function(row) {
        return row.startsWith(name + '=');
    });
    return value ? value.split('=')[1] : null;
}

// ========== SONIDOS ==========
function sonido(freq, dur, tipo) {
    try {
        var AC = window.AudioContext || window.webkitAudioContext;
        if (!AC) return;
        var ctx = new AC();
        var osc = ctx.createOscillator();
        var gain = ctx.createGain();
        osc.type = tipo || 'sine';
        osc.frequency.setValueAtTime(freq, ctx.currentTime);
        gain.gain.setValueAtTime(0.08, ctx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + dur);
        osc.connect(gain);
        gain.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + dur);
    } catch(e) {}
}
function sonidoAdd() { sonido(880, 0.08, 'sine'); setTimeout(function() { sonido(1100, 0.08, 'sine'); }, 50); }
function sonidoRemove() { sonido(440, 0.1, 'triangle'); }
function sonidoCobro() { sonido(523, 0.12, 'sine'); setTimeout(function(){ sonido(659, 0.12, 'sine'); }, 100); setTimeout(function(){ sonido(784, 0.15, 'sine'); }, 200); setTimeout(function(){ sonido(1047, 0.25, 'sine'); }, 320); }
function sonidoAlerta() { sonido(300, 0.3, 'sawtooth'); }

// ========== PARTICULAS / RELOJ ==========
function crearParticulas() {
    var c = document.getElementById('particles-container');
    if (!c) return;
    var colores = ['#00d4ff', '#a855f7', '#00ff88', '#f43f5e', '#f97316'];
    for (var i = 0; i < 25; i++) {
        var p = document.createElement('div');
        p.className = 'particle';
        p.style.left = Math.random() * 100 + 'vw';
        p.style.animationDuration = (8 + Math.random() * 15) + 's';
        p.style.animationDelay = (Math.random() * 10) + 's';
        p.style.background = colores[Math.floor(Math.random() * colores.length)];
        var sz = (2 + Math.random() * 3) + 'px';
        p.style.width = sz; p.style.height = sz;
        c.appendChild(p);
    }
}

function actualizarReloj() {
    var el = document.getElementById('reloj');
    if (!el) return;
    var now = new Date();
    var dias = ['Dom','Lun','Mar','Mie','Jue','Vie','Sab'];
    var meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
    el.textContent = dias[now.getDay()] + ' ' + now.getDate() + ' ' + meses[now.getMonth()] + ' ' +
        String(now.getHours()).padStart(2,'0') + ':' + String(now.getMinutes()).padStart(2,'0') + ':' + String(now.getSeconds()).padStart(2,'0');
}

function crearRipple(e, el) {
    var ripple = document.createElement('span');
    ripple.className = 'ripple';
    var rect = el.getBoundingClientRect();
    var size = Math.max(rect.width, rect.height);
    ripple.style.width = size + 'px'; ripple.style.height = size + 'px';
    ripple.style.left = (e.clientX - rect.left - size/2) + 'px';
    ripple.style.top = (e.clientY - rect.top - size/2) + 'px';
    el.appendChild(ripple);
    setTimeout(function() { ripple.remove(); }, 600);
}

// ========== CATEGORIAS ==========
function filtrarCategoria(catId, btn) {
    var pills = document.querySelectorAll('.cat-pill');
    for (var i = 0; i < pills.length; i++) pills[i].classList.remove('active');
    btn.classList.add('active');
    var items = document.querySelectorAll('.item-producto');
    for (var j = 0; j < items.length; j++) {
        items[j].style.display = (catId === 'todas' || items[j].getAttribute('data-categoria') === catId) ? '' : 'none';
    }
}

// ========== GESTION DE MESAS ==========
function seleccionarMesa(id, el) {
    // Guardar pedido de la mesa actual antes de cambiar
    if (mesaActual !== null) {
        guardarPedidoMesaActual();
    }

    // Deseleccionar todas
    var cards = document.querySelectorAll('.mesa-card');
    for (var i = 0; i < cards.length; i++) {
        cards[i].style.opacity = '0.5';
        cards[i].classList.remove('mesa-seleccionada');
    }
    el.style.opacity = '1';
    el.classList.add('mesa-seleccionada');

    // Cargar pedido de la mesa seleccionada
    mesaActual = (id === '0') ? 0 : parseInt(id);
    var nombreMesa = (id === '0') ? 'Para llevar' : el.querySelector('.mesa-num').textContent;
    mesasInfo[mesaActual] = { nombre: nombreMesa, el: el };

    document.getElementById('mesa-actual-label').textContent = (id === '0') ? 'Para llevar' : 'Mesa ' + nombreMesa;
    document.getElementById('ticket-mesa-info').textContent = (id === '0') ? 'Pedido para llevar' : 'Mesa ' + nombreMesa;

    // Restaurar items de esta mesa
    if (pedidosMesa[mesaActual]) {
        ordenActual = JSON.parse(JSON.stringify(pedidosMesa[mesaActual]));
    } else {
        ordenActual = {};
    }
    actualizarGraficosTicket();
    actualizarBadgesMesas();
    sonidoAdd();
}

function guardarPedidoMesaActual() {
    if (mesaActual !== null) {
        pedidosMesa[mesaActual] = JSON.parse(JSON.stringify(ordenActual));
    }
}

function actualizarBadgesMesas() {
    var ids = Object.keys(pedidosMesa);
    for (var i = 0; i < ids.length; i++) {
        var mesaId = ids[i];
        var items = pedidosMesa[mesaId];
        var badgeEl = document.getElementById('mesa-badge-' + mesaId);
        if (!badgeEl) continue;

        var totalItems = 0;
        var keys = Object.keys(items);
        for (var j = 0; j < keys.length; j++) {
            totalItems += items[keys[j]].cantidad;
        }

        if (totalItems > 0) {
            badgeEl.style.display = 'block';
            badgeEl.textContent = totalItems;
            var card = document.getElementById('mesa-' + mesaId);
            if (card && mesaId != mesaActual) {
                card.classList.add('mesa-pendiente');
            }
        } else {
            badgeEl.style.display = 'none';
            var card = document.getElementById('mesa-' + mesaId);
            if (card) card.classList.remove('mesa-pendiente');
        }
    }
}

function crearMesa() {
    Swal.fire({
        title: 'Nueva Mesa',
        html: '<input id="swal-num" class="swal2-input" placeholder="Numero de mesa" type="number" min="1">' +
              '<input id="swal-sillas" class="swal2-input" placeholder="Sillas" type="number" min="1" value="4">',
        confirmButtonText: 'Crear',
        confirmButtonColor: '#00d4ff',
        background: '#1e293b',
        color: '#e2e8f0',
        preConfirm: function() {
            var num = document.getElementById('swal-num').value;
            var sillas = document.getElementById('swal-sillas').value;
            if (!num) { Swal.showValidationMessage('Introduce un numero'); return false; }
            return { numero: num, sillas: sillas };
        }
    }).then(function(result) {
        if (result.isConfirmed && result.value) {
            fetch('/api/mesas/crear/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify(result.value)
            })
            .then(function(r) { return r.json(); })
            .then(function(data) {
                if (data.status === 'success') {
                    var container = document.getElementById('mesas-container');
                    var html = '<div class="mesa-card" style="min-width:70px;" id="mesa-' + data.id + '" onclick="seleccionarMesa(\'' + data.id + '\', this)">' +
                        '<div class="mesa-badge" id="mesa-badge-' + data.id + '" style="display:none;"></div>' +
                        '<div class="mesa-num">' + result.value.numero + '</div>' +
                        '<div class="mesa-sillas">' + result.value.sillas + ' sillas</div></div>';
                    var addBtn = document.getElementById('btn-add-mesa');
                    container.insertBefore(document.createRange().createContextualFragment(html), addBtn);
                    sonidoAdd();
                }
            });
        }
    });
}

// ========== PRODUCTOS / TICKET ==========
function agregarAlTicket(id, nombre, precio, event) {
    if (mesaActual === null) {
        sonidoAlerta();
        return Swal.fire({
            icon: 'info',
            title: 'Selecciona mesa',
            text: 'Elige una mesa o "Para llevar" antes de anadir productos.',
            confirmButtonColor: '#00d4ff',
            background: '#1e293b',
            color: '#e2e8f0'
        });
    }
    sonidoAdd();
    if (event && event.currentTarget) crearRipple(event, event.currentTarget);
    if (ordenActual[id]) { ordenActual[id].cantidad += 1; }
    else { ordenActual[id] = { nombre: nombre, precio: precio, cantidad: 1 }; }
    actualizarGraficosTicket();
    actualizarBadgeMesaActual();
}

function quitarDelTicket(id) {
    sonidoRemove();
    if (ordenActual[id]) {
        if (ordenActual[id].cantidad > 1) { ordenActual[id].cantidad -= 1; }
        else { delete ordenActual[id]; }
        actualizarGraficosTicket();
        actualizarBadgeMesaActual();
    }
}

function actualizarBadgeMesaActual() {
    if (mesaActual === null) return;
    pedidosMesa[mesaActual] = JSON.parse(JSON.stringify(ordenActual));
    actualizarBadgesMesas();
}

function actualizarGraficosTicket() {
    var container = document.getElementById('caja-ticket');
    var vacio = document.getElementById('ticket-vacio');
    var keys = Object.keys(ordenActual);
    if (vacio) vacio.style.display = keys.length === 0 ? 'flex' : 'none';

    var html = '';
    var acumulado = 0;
    for (var i = 0; i < keys.length; i++) {
        var id = keys[i];
        var item = ordenActual[id];
        var sub = item.precio * item.cantidad;
        acumulado += sub;
        html += '<div class="ticket-item">' +
            '<div style="display:flex;align-items:center;gap:8px;">' +
            '<button class="btn-remove-item" onclick="quitarDelTicket(\'' + id + '\')">&#10005;</button>' +
            '<span class="qty-badge">' + item.cantidad + 'x</span>' +
            '<span style="font-weight:600;font-size:0.85rem;color:#e2e8f0;">' + item.nombre + '</span>' +
            '</div>' +
            '<span class="item-subtotal">' + sub.toFixed(2) + ' \u20ac</span>' +
            '</div>';
    }
    container.innerHTML = html;

    var base = acumulado / 1.10;
    var iva = acumulado - base;
    document.getElementById('txt-base').textContent = base.toFixed(2) + ' \u20ac';
    document.getElementById('txt-iva').textContent = iva.toFixed(2) + ' \u20ac';
    var totalEl = document.getElementById('txt-total');
    totalEl.textContent = acumulado.toFixed(2) + ' \u20ac';
    totalEl.classList.remove('pulse');
    void totalEl.offsetWidth;
    totalEl.classList.add('pulse');
}

function lanzarToastAlerta(msg) {
    var contenedor = document.getElementById('contenedor-toasts');
    var idToast = 'toast' + Date.now();
    contenedor.insertAdjacentHTML('beforeend',
        '<div id="' + idToast + '" class="toast align-items-center text-bg-danger border-0 show mb-2" role="alert">' +
        '<div class="d-flex"><div class="toast-body fw-bold">&#9888; ' + msg + '</div>' +
        '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>'
    );
    setTimeout(function() { var el = document.getElementById(idToast); if (el) el.remove(); }, 5000);
}

// ========== COBRO ==========
function ejecutarTransaccion(metodo) {
    if (mesaActual === null) {
        sonidoAlerta();
        return Swal.fire({
            icon: 'info',
            title: 'Selecciona mesa',
            text: 'Elige una mesa o "Para llevar" antes de cobrar.',
            confirmButtonColor: '#00d4ff',
            background: '#1e293b',
            color: '#e2e8f0'
        });
    }
    if (Object.keys(ordenActual).length === 0) {
        sonidoAlerta();
        return Swal.fire({
            icon: 'warning',
            title: 'Ticket Vacio',
            text: 'Anade productos primero.',
            confirmButtonColor: '#f59e0b',
            background: '#1e293b',
            color: '#e2e8f0'
        });
    }

    var total = 0;
    var keys = Object.keys(ordenActual);
    for (var i = 0; i < keys.length; i++) {
        total += ordenActual[keys[i]].precio * ordenActual[keys[i]].cantidad;
    }

    var metodoIcono = metodo === 'EFECTIVO' ? '\uD83D\uDCB5' : '\uD83D\uDCB3';
    var metodoColor = metodo === 'EFECTIVO' ? '#10b981' : '#3b82f6';
    var nombreMesa = mesasInfo[mesaActual] ? mesasInfo[mesaActual].nombre : 'Mesa ' + mesaActual;

    Swal.fire({
        title: 'Confirmar cobro',
        html: '<div style="margin:10px 0;color:#94a3b8;">' + nombreMesa + '</div>' +
              '<div style="font-size:1.3rem;font-weight:700;margin:10px 0;">' + metodoIcono + ' ' + metodo + '</div>' +
              '<div style="font-size:2.2rem;font-weight:900;color:#00ff88;">' + total.toFixed(2) + ' \u20ac</div>',
        showCancelButton: true,
        confirmButtonText: 'COBRAR',
        cancelButtonText: 'Cancelar',
        confirmButtonColor: metodoColor,
        cancelButtonColor: '#64748b',
        background: '#1e293b',
        color: '#e2e8f0'
    }).then(function(result) {
        if (!result.isConfirmed) return;

        var listaEnviar = [];
        for (var i = 0; i < keys.length; i++) {
            listaEnviar.push({ id: keys[i], cantidad: ordenActual[keys[i]].cantidad });
        }

        fetch('/api/registrar-cobro/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
            body: JSON.stringify({ items: listaEnviar, forma_pago: metodo, mesa_id: (mesaActual > 0) ? mesaActual : null })
        })
        .then(function(res) { return res.json(); })
        .then(function(data) {
            if (data.status === 'success') {
                sonidoCobro();
                Swal.fire({
                    icon: 'success',
                    title: 'Cobro completado',
                    html: '<div style="font-size:0.9rem;color:#94a3b8;margin-bottom:5px;">Ticket #' + data.ticket_id + ' | ' + nombreMesa + '</div>' +
                        '<div style="font-size:1.2rem;margin:10px 0;">' + metodoIcono + ' ' + metodo + '</div>' +
                        '<div style="font-size:2rem;font-weight:900;color:#00ff88;">' + data.total.toFixed(2) + ' \u20ac</div>',
                    confirmButtonColor: '#10b981',
                    background: '#1e293b',
                    color: '#e2e8f0'
                });

                if (data.alertas && data.alertas.length > 0) {
                    for (var j = 0; j < data.alertas.length; j++) {
                        var a = data.alertas[j];
                        lanzarToastAlerta('REPOSICION: Quedan ' + a.restante + ' ' + a.unidad + ' de ' + a.ingrediente);
                    }
                }

                // Limpiar esta mesa
                delete pedidosMesa[mesaActual];
                ordenActual = {};
                actualizarGraficosTicket();
                actualizarBadgesMesas();
            } else {
                Swal.fire({ icon: 'error', title: 'Error', text: data.error || 'Error', confirmButtonColor: '#f43f5e', background: '#1e293b', color: '#e2e8f0' });
            }
        })
        .catch(function() {
            Swal.fire({ icon: 'error', title: 'Sin conexion', text: 'No se pudo contactar con el servidor.', confirmButtonColor: '#f43f5e', background: '#1e293b', color: '#e2e8f0' });
        });
    });
}

// ========== INIT ==========
document.addEventListener('DOMContentLoaded', function() {
    crearParticulas();
    actualizarReloj();
    setInterval(actualizarReloj, 1000);
});
