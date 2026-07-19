from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal


class Mesa(models.Model):
    numero = models.PositiveIntegerField(unique=True)
    sillas = models.PositiveIntegerField(default=4)
    activa = models.BooleanField(default=True)

    def __str__(self):
        return f"Mesa {self.numero} ({self.sillas} sillas)"


class InsumoMateriaPrima(models.Model):
    UNIDADES = [('g', 'Gramos'), ('ml', 'Mililitros'), ('ud', 'Unidades')]
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del Ingrediente")
    cantidad_actual = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock Actual")
    cantidad_minima = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Stock Minimo de Alerta")
    unidad_medida = models.CharField(max_length=5, choices=UNIDADES, default='g')

    @property
    def necesita_reposicion(self):
        return self.cantidad_actual <= self.cantidad_minima

    def __str__(self):
        return f"{self.nombre} ({self.cantidad_actual} {self.unidad_medida})"


class CategoriaProducto(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    icono = models.CharField(max_length=10, default="☕")

    def __str__(self):
        return f"{self.icono} {self.nombre}"


class Articulo(models.Model):
    TIPO_IVA_CHOICES = [
        ('10.00', '10% (Hosteleria / Alimentacion)'),
        ('21.00', '21% (Bebidas Alcoholicas / General)'),
        ('4.00', '4% (Superreducido)'),
    ]
    nombre = models.CharField(max_length=100, unique=True)
    precio_sin_iva = models.DecimalField(max_digits=6, decimal_places=2, verbose_name="Precio Base (Sin IVA)")
    tipo_iva = models.CharField(max_length=5, choices=TIPO_IVA_CHOICES, default='10.00')
    categoria = models.ForeignKey(CategoriaProducto, on_delete=models.CASCADE, related_name="articulos")
    codigo_barras = models.CharField(max_length=50, blank=True, unique=True, null=True, help_text="Codigo de barras EAN-13")
    activo = models.BooleanField(default=True)

    @property
    def precio_con_iva(self):
        porcentaje_iva = Decimal(self.tipo_iva) / Decimal('100')
        return (self.precio_sin_iva * (1 + porcentaje_iva)).quantize(Decimal('0.01'))

    def __str__(self):
        return f"{self.nombre} - {self.precio_con_iva}€ (IVA Inc.)"


class ComposicionReceta(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name="receta")
    insumo = models.ForeignKey(InsumoMateriaPrima, on_delete=models.CASCADE)
    cantidad_consumida = models.DecimalField(max_digits=6, decimal_places=2, help_text="Cantidad usada por cada venta")

    def __str__(self):
        return f"{self.articulo.nombre} usa {self.cantidad_consumida} de {self.insumo.nombre}"


class OperacionVenta(models.Model):
    METODOS = [('EFECTIVO', 'Efectivo'), ('TARJETA', 'Tarjeta')]
    fecha_registro = models.DateTimeField(auto_now_add=True)
    empleado_caja = models.ForeignKey(User, on_delete=models.PROTECT)
    mesa = models.ForeignKey(Mesa, on_delete=models.SET_NULL, null=True, blank=True, related_name="ventas")
    subtotal_base = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_impuestos = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_facturado = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    forma_pago = models.CharField(max_length=15, choices=METODOS, default='EFECTIVO')
    hash_seguridad = models.CharField(max_length=64, editable=False, blank=True)
    cupon = models.ForeignKey('CuponDescuento', on_delete=models.SET_NULL, null=True, blank=True)
    cliente = models.ForeignKey('Cliente', on_delete=models.SET_NULL, null=True, blank=True, related_name='compras')
    puntos_ganados = models.PositiveIntegerField(default=0)
    descuento_aplicado = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    satisfaccion = models.CharField(max_length=10, blank=True, choices=[
        ('EXCELENTE', '😍'), ('BUENA', '🙂'), ('NORMAL', '😐'), ('MALA', '😠'),
    ], help_text="Valoracion del cliente")

    def __str__(self):
        return f"Ticket N° {self.id} | {self.fecha_registro.strftime('%d/%m/%Y %H:%M')} | {self.total_facturado}€"


class LineaVenta(models.Model):
    venta = models.ForeignKey(OperacionVenta, on_delete=models.CASCADE, related_name="lineas")
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    unidades = models.PositiveIntegerField(default=1)
    precio_aplicado_con_iva = models.DecimalField(max_digits=6, decimal_places=2)


class RegistroGasto(models.Model):
    concepto = models.CharField(max_length=255)
    importe_total = models.DecimalField(max_digits=8, decimal_places=2)
    fecha_gasto = models.DateTimeField(auto_now_add=True)
    empleado_autoriza = models.ForeignKey(User, on_delete=models.PROTECT)

    def __str__(self):
        return f"Gasto: {self.concepto} (-{self.importe_total}€)"


class AuditLog(models.Model):
    ACCIONES = [
        ('LOGIN', 'Inicio de sesion'),
        ('LOGOUT', 'Cierre de sesion'),
        ('VENTA', 'Cobro / Venta'),
        ('GASTO', 'Registro de gasto'),
        ('CREAR', 'Creacion'),
        ('EDITAR', 'Edicion'),
        ('ELIMINAR', 'Eliminacion'),
    ]
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    modelo = models.CharField(max_length=50, blank=True)
    objeto_id = models.CharField(max_length=50, blank=True)
    descripcion = models.TextField(blank=True)
    detalles_json = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']
        verbose_name = 'Registro de Auditoria'
        verbose_name_plural = 'Registros de Auditoria'

    def __str__(self):
        u = self.usuario.username if self.usuario else 'Sistema'
        return f"[{self.fecha.strftime('%d/%m %H:%M')}] {u} - {self.get_accion_display()} - {self.descripcion[:80]}"


class TurnoCaja(models.Model):
    cajero = models.ForeignKey(User, on_delete=models.PROTECT)
    fecha_apertura = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField(null=True, blank=True)
    saldo_inicial = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_efectivo = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_tarjeta = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_gastos = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_teorico = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    total_real = models.DecimalField(max_digits=8, decimal_places=2, default=0.00, null=True, blank=True)
    tickets_cerrados = models.PositiveIntegerField(default=0)
    cerrado = models.BooleanField(default=False)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha_apertura']

    def __str__(self):
        estado = "Cerrado" if self.cerrado else "Abierto"
        return f"Turno {self.id} | {self.cajero.username} | {self.fecha_apertura.strftime('%d/%m %H:%M')} | {estado}"


class PedidoCocina(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('PREPARANDO', 'En preparacion'),
        ('LISTO', 'Listo para servir'),
        ('ENTREGADO', 'Entregado'),
    ]
    venta = models.ForeignKey(OperacionVenta, on_delete=models.CASCADE, related_name="pedidos_cocina")
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    unidades = models.PositiveIntegerField(default=1)
    notas = models.CharField(max_length=200, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_listo = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['fecha_creacion']

    def __str__(self):
        return f"Cocina: {self.unidades}x {self.articulo.nombre} [{self.estado}]"


class PedidoPendiente(models.Model):
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='pedidos_pendientes')
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    notas = models.CharField(max_length=200, blank=True)
    empleado = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Pendiente Mesa {self.mesa.numero}: {self.cantidad}x {self.articulo.nombre}"


class MenuDelDia(models.Model):
    FRANJAS = [
        ('MANANA', 'Manana (8h-12h)'),
        ('MEDIODIA', 'Mediodia (12h-16h)'),
        ('TARDE', 'Tarde (16h-20h)'),
        ('TODO', 'Todo el dia'),
    ]
    nombre = models.CharField(max_length=100)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name="menu_dia")
    precio_promo = models.DecimalField(max_digits=6, decimal_places=2)
    franja = models.CharField(max_length=10, choices=FRANJAS, default='TODO')
    activo = models.BooleanField(default=True)
    fecha = models.DateField(auto_now_add=True)

    class Meta:
        verbose_name = "Menu del Dia"
        verbose_name_plural = "Menus del Dia"

    def __str__(self):
        return f"{self.nombre} - {self.articulo.nombre} ({self.precio_promo}€)"


class Reserva(models.Model):
    ESTADOS = [
        ('PENDIENTE', 'Pendiente'),
        ('CONFIRMADA', 'Confirmada'),
        ('CANCELADA', 'Cancelada'),
        ('COMPLETADA', 'Completada'),
    ]
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name="reservas")
    cliente_nombre = models.CharField(max_length=100)
    cliente_telefono = models.CharField(max_length=20, blank=True)
    email_cliente = models.EmailField(blank=True, verbose_name="Email del Cliente")
    fecha_reserva = models.DateField()
    hora_reserva = models.TimeField()
    num_personas = models.PositiveIntegerField(default=2)
    estado = models.CharField(max_length=15, choices=ESTADOS, default='PENDIENTE')
    notas = models.CharField(max_length=200, blank=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_reserva', 'hora_reserva']

    def __str__(self):
        return f"{self.cliente_nombre} | Mesa {self.mesa.numero} | {self.fecha_reserva} {self.hora_reserva}"


class CuponDescuento(models.Model):
    TIPOS = [
        ('PORCENTAJE', 'Porcentaje (%)'),
        ('FIJO', 'Importe fijo (EUR)'),
    ]
    codigo = models.CharField(max_length=30, unique=True)
    descripcion = models.CharField(max_length=200)
    tipo = models.CharField(max_length=12, choices=TIPOS, default='PORCENTAJE')
    valor = models.DecimalField(max_digits=6, decimal_places=2)
    minimo_pedido = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    usos_maximos = models.PositiveIntegerField(default=0, help_text="0 = sin limite")
    usos_realizados = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    fecha_inicio = models.DateField(null=True, blank=True)
    fecha_fin = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.codigo} - {self.descripcion}"

    @property
    def esta_disponible(self):
        from datetime import date
        if not self.activo:
            return False
        hoy = date.today()
        if self.fecha_inicio and hoy < self.fecha_inicio:
            return False
        if self.fecha_fin and hoy > self.fecha_fin:
            return False
        if self.usos_maximos > 0 and self.usos_realizados >= self.usos_maximos:
            return False
        return True

    def calcular_descuento(self, subtotal):
        if not self.esta_disponible or subtotal < self.minimo_pedido:
            return Decimal('0.00')
        if self.tipo == 'PORCENTAJE':
            return (subtotal * self.valor / Decimal('100')).quantize(Decimal('0.01'))
        return min(self.valor, subtotal)


class PerfilEmpleado(models.Model):
    ROL_CHOICES = [
        ('CAJERO', 'Cajero'),
        ('COCINERO', 'Cocinero'),
        ('CAMARERO', 'Camarero'),
        ('GERENTE', 'Gerente'),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    rol = models.CharField(max_length=10, choices=ROL_CHOICES, default='CAJERO')
    telefono = models.CharField(max_length=20, blank=True)
    pin_acceso = models.CharField(max_length=6, blank=True, help_text="PIN para acceso rapido")

    def __str__(self):
        return f"{self.user.username} ({self.get_rol_display()})"


class MetaDiaria(models.Model):
    fecha = models.DateField(unique=True)
    objetivo_tickets = models.PositiveIntegerField(default=50)
    objetivo_ingresos = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('500.00'))

    def __str__(self):
        return f"Meta {self.fecha}: {self.objetivo_tickets} tickets / {self.objetivo_ingresos} EUR"

    @property
    def tickets_hoy(self):
        return OperacionVenta.objects.filter(fecha_registro__date=self.fecha).count()

    @property
    def ingresos_hoy(self):
        result = OperacionVenta.objects.filter(fecha_registro__date=self.fecha).aggregate(
            total=models.Sum('total_facturado'))
        return result['total'] or Decimal('0.00')

    @property
    def porcentaje_tickets(self):
        return min(100, round((self.tickets_hoy / self.objetivo_tickets) * 100)) if self.objetivo_tickets else 0

    @property
    def porcentaje_ingresos(self):
        return min(100, round((float(self.ingresos_hoy) / float(self.objetivo_ingresos)) * 100)) if self.objetivo_ingresos else 0

    @property
    def porcentaje_total(self):
        return round((self.porcentaje_tickets + self.porcentaje_ingresos) / 2)

    @property
    def badges(self):
        earned = []
        tickets = self.tickets_hoy
        ingresos = float(self.ingresos_hoy)
        if tickets >= 1: earned.append({'icono': '🌟', 'nombre': 'Primer Ticket', 'desc': 'Primera venta del dia'})
        if tickets >= 10: earned.append({'icono': '🔥', 'nombre': 'En racha', 'desc': '10+ tickets vendidos'})
        if tickets >= 25: earned.append({'icono': '⚡', 'nombre': 'Imparable', 'desc': '25+ tickets vendidos'})
        if tickets >= 50: earned.append({'icono': '🏆', 'nombre': 'Leyenda', 'desc': '50+ tickets vendidos'})
        if ingresos >= 100: earned.append({'icono': '💰', 'nombre': '100EUR Club', 'desc': 'Facturacion supera 100EUR'})
        if ingresos >= 500: earned.append({'icono': '💎', 'nombre': 'Diamante', 'desc': 'Facturacion supera 500EUR'})
        if self.porcentaje_total >= 100: earned.append({'icono': '👑', 'nombre': 'Meta cumplida', 'desc': 'Objetivo del dia alcanzado'})
        return earned


class Cliente(models.Model):
    nombre = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    telefono = models.CharField(max_length=20, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    puntos = models.PositiveIntegerField(default=0)
    nivel = models.CharField(max_length=10, choices=[
        ('BRONCE', 'Bronce'), ('PLATA', 'Plata'), ('ORO', 'Oro'), ('PLATINO', 'Platino'),
    ], default='BRONCE')
    creado = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Clientes'

    def __str__(self):
        return f"{self.nombre} ({self.get_nivel_display()}) - {self.puntos} pts"

    @property
    def descuento_nivel(self):
        return {'BRONCE': 0, 'PLATA': 5, 'ORO': 10, 'PLATINO': 15}.get(self.nivel, 0)

    def actualizar_nivel(self):
        if self.puntos >= 500: self.nivel = 'PLATINO'
        elif self.puntos >= 200: self.nivel = 'ORO'
        elif self.puntos >= 50: self.nivel = 'PLATA'
        else: self.nivel = 'BRONCE'
        self.save()

    def agregar_puntos(self, importe):
        puntos_ganados = int(float(importe) * 10)
        self.puntos += puntos_ganados
        self.actualizar_nivel()
        return puntos_ganados


class ColaNumero(models.Model):
    ESTADO_CHOICES = [
        ('ESPERANDO', 'Esperando'), ('LLAMANDO', 'Llamando'), ('ATENDIDO', 'Atendido'), ('CANCELADO', 'Cancelado'),
    ]
    numero = models.PositiveIntegerField()
    fecha = models.DateField(auto_now_add=True)
    nombre_cliente = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='ESPERANDO')
    creado = models.DateTimeField(auto_now_add=True)
    atendido = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['numero']
        unique_together = [('numero', 'fecha')]

    def __str__(self):
        return f"#{self.numero} - {self.estado}"


class PedidoMovil(models.Model):
    ESTADO_CHOICES = [
        ('RECIBIDO', 'Recibido'), ('CONFIRMADO', 'Confirmado'),
        ('PREPARANDO', 'Preparando'), ('LISTO', 'Listo'), ('ENTREGADO', 'Entregado'), ('CANCELADO', 'Cancelado'),
    ]
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE, related_name='pedidos_movil')
    fecha = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=12, choices=ESTADO_CHOICES, default='RECIBIDO')
    cliente_nombre = models.CharField(max_length=100, blank=True)
    notas = models.TextField(blank=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"Mesa {self.mesa.numero} - {self.get_estado_display()}"


class LineaPedidoMovil(models.Model):
    pedido = models.ForeignKey(PedidoMovil, on_delete=models.CASCADE, related_name='lineas')
    articulo = models.ForeignKey(Articulo, on_delete=models.PROTECT)
    unidades = models.PositiveIntegerField(default=1)
    notas = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"{self.unidades}x {self.articulo.nombre}"


class PlanoRestaurante(models.Model):
    nombre = models.CharField(max_length=100, default='Plano Principal')
    ancho = models.PositiveIntegerField(default=800)
    alto = models.PositiveIntegerField(default=600)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return self.nombre


class MesaPosicion(models.Model):
    plano = models.ForeignKey(PlanoRestaurante, on_delete=models.CASCADE, related_name='mesas_pos')
    mesa = models.OneToOneField(Mesa, on_delete=models.CASCADE, related_name='posicion')
    x = models.PositiveIntegerField(default=100)
    y = models.PositiveIntegerField(default=100)
    color = models.CharField(max_length=7, default='#00d4ff')

    def __str__(self):
        return f"Mesa {self.mesa.numero} en ({self.x},{self.y})"


class MensajeChat(models.Model):
    REMITENTE_CHOICES = [('CAJERO', 'Cajero'), ('COCINA', 'Cocina')]
    emisor = models.CharField(max_length=10, choices=REMITENTE_CHOICES)
    texto = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)

    class Meta:
        ordering = ['fecha']

    def __str__(self):
        return f"[{self.emisor}] {self.texto[:40]}"


class PedidoProveedor(models.Model):
    ESTADO_CHOICES = [
        ('PENDIENTE', 'Pendiente'), ('ENVIADO', 'Enviado'),
        ('RECIBIDO', 'Recibido'), ('CANCELADO', 'Cancelado'),
    ]
    insumo = models.ForeignKey(InsumoMateriaPrima, on_delete=models.CASCADE)
    cantidad_solicitada = models.DecimalField(max_digits=10, decimal_places=2)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='PENDIENTE')
    email_proveedor = models.EmailField(blank=True, verbose_name="Email del Proveedor")
    notas = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"Pedido {self.insumo.nombre}: {self.cantidad_solicitada} {self.insumo.unidad_medida}"


class FirmaDigital(models.Model):
    venta = models.OneToOneField(OperacionVenta, on_delete=models.CASCADE, related_name='firma')
    imagen_firma = models.TextField()  # Base64 PNG
    fecha = models.DateTimeField(auto_now_add=True)
    cliente_nombre = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f"Firma Venta #{self.venta.id}"


class PasoReceta(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='pasos')
    orden = models.PositiveIntegerField(default=1)
    titulo = models.CharField(max_length=200)
    descripcion = models.TextField()
    tiempo_minutos = models.PositiveIntegerField(default=0)
    consejo = models.TextField(blank=True)

    class Meta:
        ordering = ['orden']

    def __str__(self):
        return f"{self.orden}. {self.titulo}"


class NotificacionPush(models.Model):
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    url = models.CharField(max_length=300, blank=True)
    enviada = models.BooleanField(default=False)
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo


class DescuentoInteligente(models.Model):
    TIPO_CHOICES = [
        ('3X2', '3x2'),
        ('2DA_50', '2da unidad 50%'),
        ('COMBO', 'Combo especial'),
        ('HAPPY_HOUR', 'Happy Hour'),
        ('VOLUMEN', 'Descuento por volumen'),
    ]
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=10, choices=TIPO_CHOICES)
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, null=True, blank=True, related_name='descuentos_inteligentes')
    porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    cantidad_minima = models.PositiveIntegerField(default=1)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)
    activo = models.BooleanField(default=True)
    dias_semana = models.CharField(max_length=20, default='0,1,2,3,4,5,6')

    def __str__(self):
        return f"{self.nombre} ({self.get_tipo_display()})"


class ReviewRestaurante(models.Model):
    nombre = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    estrellas = models.PositiveIntegerField(default=5)
    comentario = models.TextField()
    fecha = models.DateTimeField(auto_now_add=True)
    visible = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.nombre} - {self.estrellas}⭐"


class RatingProducto(models.Model):
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='ratings')
    cliente_nombre = models.CharField(max_length=200)
    estrellas = models.PositiveIntegerField(default=5)
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.articulo.nombre} - {self.estrellas}⭐"


class Combo(models.Model):
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField(blank=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    activo = models.BooleanField(default=True)
    hora_inicio = models.TimeField(null=True, blank=True)
    hora_fin = models.TimeField(null=True, blank=True)

    def __str__(self):
        return self.nombre


class ComboItem(models.Model):
    combo = models.ForeignKey(Combo, on_delete=models.CASCADE, related_name='items')
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.cantidad}x {self.articulo.nombre} en {self.combo.nombre}"


class EmailLog(models.Model):
    asunto = models.CharField(max_length=200)
    destinatarios = models.TextField()
    tipo = models.CharField(max_length=50)
    enviado = models.BooleanField(default=True)
    error = models.TextField(blank=True)
    fecha_envio = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_envio']
        verbose_name = 'Log de Email'
        verbose_name_plural = 'Logs de Emails'

    def __str__(self):
        estado = '✓' if self.enviado else '✗'
        return f'{estado} [{self.tipo}] {self.asunto} ({self.fecha_envio.strftime("%d/%m %H:%M")})'
