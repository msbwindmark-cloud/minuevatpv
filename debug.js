    <script>
    var ordenActual = {};
    var pedidosMesa = {};
    var mesaActual = null;
    var mesasInfo = {};

    function getCookie(name) {
        var v = document.cookie.split('; ').find(function(r){ return r.startsWith(name+'='); });
        return v ? v.split('=')[1] : null;
    }

    function sonido(f, d, t) {
        try {
            var AC = window.AudioContext || window.webkitAudioContext;
            if (!AC) return;
            var c = new AC(), o = c.createOscillator(), g = c.createGain();
            o.type = t || 'sine';
            o.frequency.setValueAtTime(f, c.currentTime);
            g.gain.setValueAtTime(0.08, c.currentTime);
            g.gain.exponentialRampToValueAtTime(0.001, c.currentTime + d);
            o.connect(g); g.connect(c.destination);
            o.start(); o.stop(c.currentTime + d);
        } catch(e) {}
    }
    function sonidoAdd() { sonido(880, 0.08, 'sine'); setTimeout(function(){ sonido(1100, 0.08, 'sine'); }, 50); }
    function sonidoRemove() { sonido(440, 0.1, 'triangle'); }
    function sonidoCobro() {
        sonido(523, 0.12, 'sine');
        setTimeout(function(){ sonido(659, 0.12, 'sine'); }, 100);
        setTimeout(function(){ sonido(784, 0.15, 'sine'); }, 200);
        setTimeout(function(){ sonido(1047, 0.25, 'sine'); }, 320);
    }
    function sonidoAlerta() { sonido(300, 0.3, 'sawtooth'); }

    function crearParticulas() {
        var c = document.getElementById('particles-container');
        if (!c) return;
        var cols = ['#00d4ff','#a855f7','#00ff88','#f43f5e','#f97316'];
        for (var i = 0; i < 25; i++) {
            var p = document.createElement('div');
            p.className = 'particle';
            p.style.left = Math.random() * 100 + 'vw';
            p.style.animationDuration = (8 + Math.random() * 15) + 's';
            p.style.animationDelay = (Math.random() * 10) + 's';
            p.style.background = cols[Math.floor(Math.random() * cols.length)];
            var s = (2 + Math.random() * 3) + 'px';
            p.style.width = s; p.style.height = s;
            c.appendChild(p);
        }
    }

    function actualizarReloj() {
        var el = document.getElementById('reloj');
        if (!el) return;
        var n = new Date();
        var d = ['Dom','Lun','Mar','Mie','Jue','Vie','Sab'];
        var m = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic'];
        el.textContent = d[n.getDay()] + ' ' + n.getDate() + ' ' + m[n.getMonth()] + ' ' +
            String(n.getHours()).padStart(2, '0') + ':' +
            String(n.getMinutes()).padStart(2, '0') + ':' +
            String(n.getSeconds()).padStart(2, '0');
    }

    function crearRipple(e, el) {
        var r = document.createElement('span');
        r.className = 'ripple';
        var rect = el.getBoundingClientRect();
        var s = Math.max(rect.width, rect.height);
        r.style.width = s + 'px'; r.style.height = s + 'px';
        r.style.left = (e.clientX - rect.left - s / 2) + 'px';
        r.style.top = (e.clientY - rect.top - s / 2) + 'px';
        el.appendChild(r);
        setTimeout(function(){ r.remove(); }, 600);
    }

    function filtrarCategoria(catId, btn) {
        var pills = document.querySelectorAll('.cat-pill');
        for (var i = 0; i < pills.length; i++) pills[i].classList.remove('active');
        btn.classList.add('active');
        var items = document.querySelectorAll('.item-producto');
        for (var j = 0; j < items.length; j++) {
            items[j].style.display = (catId === 'todas' || items[j].getAttribute('data-categoria') === catId) ? '' : 'none';
        }
    }

    function seleccionarMesa(id, el) {
        if (mesaActual !== null) guardarPedidoMesaActual();
        var cards = document.querySelectorAll('.mesa-card');
        for (var i = 0; i < cards.length; i++) {
            cards[i].style.opacity = '0.5';
            cards[i].classList.remove('mesa-seleccionada');
        }
        el.style.opacity = '1';
        el.classList.add('mesa-seleccionada');
        mesaActual = id;
        var nombre = (id === 0) ? 'Para llevar' : el.querySelector('.mesa-num').textContent;
        mesasInfo[mesaActual] = { nombre: nombre, el: el };
        document.getElementById('mesa-actual-label').textContent = (id === 0) ? 'Para llevar' : 'Mesa ' + nombre;
        document.getElementById('ticket-mesa-info').textContent = (id === 0) ? 'Pedido para llevar' : 'Mesa ' + nombre;
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
        if (mesaActual !== null) pedidosMesa[mesaActual] = JSON.parse(JSON.stringify(ordenActual));
    }

    function actualizarBadgesMesas() {
        var ids = Object.keys(pedidosMesa);
        for (var i = 0; i < ids.length; i++) {
            var mid = ids[i];
            var items = pedidosMesa[mid];
            var b = document.getElementById('mesa-badge-' + mid);
            if (!b) continue;
            var total = 0;
            var k = Object.keys(items);
            for (var j = 0; j < k.length; j++) total += items[k[j]].cantidad;
            if (total > 0) {
                b.style.display = 'block'; b.textContent = total;
                var card = document.getElementById('mesa-' + mid);
                if (card && mid != mesaActual) card.classList.add('mesa-pendiente');
            } else {
                b.style.display = 'none';
                var card2 = document.getElementById('mesa-' + mid);
                if (card2) card2.classList.remove('mesa-pendiente');
            }
        }
    }

    function crearMesa() {
        Swal.fire({
            title: 'Nueva Mesa',
            html: '<input id="swal-num" class="swal2-input" placeholder="Numero de mesa" type="number" min="1"><input id="swal-sillas" class="swal2-input" placeholder="Sillas" type="number" min="1" value="4">',
            confirmButtonText: 'Crear',
            confirmButtonColor: '#00d4ff',
            background: '#1e293b',
            color: '#e2e8f0',
            preConfirm: function() {
                var n = document.getElementById('swal-num').value;
                var s = document.getElementById('swal-sillas').value;
                if (!n) { Swal.showValidationMessage('Introduce un numero'); return false; }
                return { numero: n, sillas: s };
            }
        }).then(function(r) {
            if (r.isConfirmed && r.value) {
                fetch('/api/mesas/crear/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                    body: JSON.stringify(r.value)
                }).then(function(res) { return res.json(); }).then(function(d) {
                    if (d.status === 'success') {
                        var c = document.getElementById('mesas-container');
                        var a = document.getElementById('btn-add-mesa');
                        var div = document.createElement('div');
                        div.className = 'mesa-card';
                        div.style.minWidth = '70px';
                        div.id = 'mesa-' + d.id;
                        div.onclick = function() { seleccionarMesa(d.id, this); };
                        div.innerHTML = '<div class="mesa-badge" id="mesa-badge-' + d.id + '" style="display:none;">0</div><div class="mesa-num">' + r.value.numero + '</div><div class="mesa-sillas">' + r.value.sillas + ' sillas</div>';
                        c.insertBefore(div, a);
                        sonidoAdd();
                    }
                });
            }
        });
    }

    function agregarAlTicket(el) {
        if (mesaActual === null) {
            sonidoAlerta();
            return Swal.fire({
                icon: 'info',
                title: 'Selecciona una mesa',
                text: 'Debes elegir una mesa o "Para llevar" antes de anadir productos.',
                confirmButtonColor: '#00d4ff',
                background: '#1e293b',
                color: '#e2e8f0'
            });
        }
        var id = el.getAttribute('data-id');
        var nombre = el.getAttribute('data-nombre');
        var precio = parseFloat(el.getAttribute('data-precio'));
        sonidoAdd();
        crearRipple(event, el);
        if (ordenActual[id]) {
            ordenActual[id].cantidad += 1;
        } else {
            ordenActual[id] = { nombre: nombre, precio: precio, cantidad: 1 };
        }
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
        var c = document.getElementById('caja-ticket');
        var v = document.getElementById('ticket-vacio');
        var keys = Object.keys(ordenActual);
        if (v) v.style.display = keys.length === 0 ? 'flex' : 'none';
        var html = '';
        var ac = 0;
        for (var i = 0; i < keys.length; i++) {
            var id = keys[i];
            var it = ordenActual[id];
            var sub = it.precio * it.cantidad;
            ac += sub;
            html += '<div class="ticket-item"><div style="display:flex;align-items:center;gap:8px;"><button class="btn-remove-item" onclick="quitarDelTicket(\'' + id + '\')">&#10005;</button><span class="qty-badge">' + it.cantidad + 'x</span><span style="font-weight:600;font-size:0.85rem;color:#e2e8f0;">' + it.nombre + '</span></div><span class="item-subtotal">' + sub.toFixed(2) + ' \u20ac</span></div>';
        }
        c.innerHTML = html;
        var base = ac / 1.10;
        var iva = ac - base;
        document.getElementById('txt-base').textContent = base.toFixed(2) + ' \u20ac';
        document.getElementById('txt-iva').textContent = iva.toFixed(2) + ' \u20ac';
        var t = document.getElementById('txt-total');
        t.textContent = ac.toFixed(2) + ' \u20ac';
        t.classList.remove('pulse');
        void t.offsetWidth;
        t.classList.add('pulse');
    }

    function lanzarToastAlerta(msg) {
        var c = document.getElementById('contenedor-toasts');
        var id = 'toast' + Date.now();
        c.insertAdjacentHTML('beforeend', '<div id="' + id + '" class="toast align-items-center text-bg-danger border-0 show mb-2" role="alert"><div class="d-flex"><div class="toast-body fw-bold">&#9888; ' + msg + '</div><button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>');
        setTimeout(function(){ var e = document.getElementById(id); if (e) e.remove(); }, 5000);
    }

    function ejecutarTransaccion(metodo) {
        if (mesaActual === null) {
            sonidoAlerta();
            return Swal.fire({
                icon: 'info',
                title: 'Selecciona una mesa',
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
        for (var i = 0; i < keys.length; i++) total += ordenActual[keys[i]].precio * ordenActual[keys[i]].cantidad;
        var icono = metodo === 'EFECTIVO' ? '\uD83D\uDCB5' : '\uD83D\uDCB3';
        var color = metodo === 'EFECTIVO' ? '#10b981' : '#3b82f6';
        var nombreMesa = mesasInfo[mesaActual] ? mesasInfo[mesaActual].nombre : 'Mesa ' + mesaActual;
        Swal.fire({
            title: 'Confirmar cobro',
            html: '<div style="margin:10px 0;color:#94a3b8;">' + nombreMesa + '</div><div style="font-size:1.3rem;font-weight:700;margin:10px 0;">' + icono + ' ' + metodo + '</div><div style="font-size:2.2rem;font-weight:900;color:#00ff88;">' + total.toFixed(2) + ' \u20ac</div>',
            showCancelButton: true,
            confirmButtonText: 'COBRAR',
            cancelButtonText: 'Cancelar',
            confirmButtonColor: color,
            cancelButtonColor: '#64748b',
            background: '#1e293b',
            color: '#e2e8f0'
        }).then(function(r) {
            if (!r.isConfirmed) return;
            var lista = [];
            for (var i = 0; i < keys.length; i++) lista.push({ id: keys[i], cantidad: ordenActual[keys[i]].cantidad });
            fetch('/api/registrar-cobro/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': getCookie('csrftoken') },
                body: JSON.stringify({ items: lista, forma_pago: metodo, mesa_id: (mesaActual > 0) ? mesaActual : null })
            }).then(function(res) { return res.json(); }).then(function(d) {
                if (d.status === 'success') {
                    sonidoCobro();
                    Swal.fire({
                        icon: 'success',
                        title: 'Cobro completado',
                        html: '<div style="font-size:0.9rem;color:#94a3b8;margin-bottom:5px;">Ticket #' + d.ticket_id + ' | ' + nombreMesa + '</div><div style="font-size:1.2rem;margin:10px 0;">' + icono + ' ' + metodo + '</div><div style="font-size:2rem;font-weight:900;color:#00ff88;">' + d.total.toFixed(2) + ' \u20ac</div>',
                        confirmButtonColor: '#10b981',
                        background: '#1e293b',
                        color: '#e2e8f0'
                    });
                    if (d.alertas && d.alertas.length > 0) {
                        for (var j = 0; j < d.alertas.length; j++) {
                            var a = d.alertas[j];
                            lanzarToastAlerta('REPOSICION: Quedan ' + a.restante + ' ' + a.unidad + ' de ' + a.ingrediente);
                        }
                    }
                    delete pedidosMesa[mesaActual];
                    ordenActual = {};
                    actualizarGraficosTicket();
                    actualizarBadgesMesas();
                } else {
                    Swal.fire({ icon: 'error', title: 'Error', text: d.error || 'Error', confirmButtonColor: '#f43f5e', background: '#1e293b', color: '#e2e8f0' });
                }
            }).catch(function() {
                Swal.fire({ icon: 'error', title: 'Sin conexion', text: 'No se pudo contactar con el servidor.', confirmButtonColor: '#f43f5e', background: '#1e293b', color: '#e2e8f0' });
            });
        });
    }

    crearParticulas();
    actualizarReloj();
    setInterval(actualizarReloj, 1000);
    </script>