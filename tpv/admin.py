from django.contrib import admin
from .models import (
    InsumoMateriaPrima, CategoriaProducto, Articulo,
    ComposicionReceta, OperacionVenta, LineaVenta, RegistroGasto, Mesa,
    AuditLog, TurnoCaja, PedidoCocina, MenuDelDia, Reserva,
    CuponDescuento, PerfilEmpleado, MetaDiaria, Cliente,
    ColaNumero, PedidoMovil, LineaPedidoMovil, PlanoRestaurante, MesaPosicion,
    MensajeChat, PedidoProveedor, FirmaDigital, PasoReceta, NotificacionPush,
    DescuentoInteligente, ReviewRestaurante, RatingProducto, Combo, ComboItem
)


@admin.register(InsumoMateriaPrima)
class InsumoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'cantidad_actual', 'cantidad_minima', 'unidad_medida')
    search_fields = ('nombre',)


@admin.register(CategoriaProducto)
class CategoriaProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'icono')


@admin.register(Articulo)
class ArticuloAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio_sin_iva', 'tipo_iva', 'categoria', 'activo')
    list_filter = ('activo', 'categoria', 'tipo_iva')
    search_fields = ('nombre',)


@admin.register(ComposicionReceta)
class ComposicionRecetaAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'insumo', 'cantidad_consumida')


@admin.register(OperacionVenta)
class OperacionVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_registro', 'empleado_caja', 'total_facturado', 'forma_pago')
    list_filter = ('forma_pago', 'fecha_registro')


@admin.register(LineaVenta)
class LineaVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'articulo', 'unidades', 'precio_aplicado_con_iva')


@admin.register(RegistroGasto)
class RegistroGastoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'importe_total', 'fecha_gasto', 'empleado_autoriza')


@admin.register(Mesa)
class MesaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'sillas', 'activa')
    list_filter = ('activa',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'usuario', 'accion', 'modelo', 'objeto_id', 'descripcion_corta', 'ip_address')
    list_filter = ('accion', 'modelo', 'fecha')
    search_fields = ('descripcion', 'usuario__username', 'objeto_id')
    readonly_fields = ('fecha', 'usuario', 'accion', 'modelo', 'objeto_id', 'descripcion', 'detalles_json', 'ip_address')
    date_hierarchy = 'fecha'

    def descripcion_corta(self, obj):
        return obj.descripcion[:80] if obj.descripcion else '-'
    descripcion_corta.short_description = 'Descripcion'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(TurnoCaja)
class TurnoCajaAdmin(admin.ModelAdmin):
    list_display = ('id', 'cajero', 'fecha_apertura', 'fecha_cierre', 'saldo_inicial', 'total_teorico', 'total_real', 'cerrado')
    list_filter = ('cerrado', 'cajero')


@admin.register(PedidoCocina)
class PedidoCocinaAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'unidades', 'estado', 'fecha_creacion', 'fecha_listo', 'notas')
    list_filter = ('estado',)


@admin.register(MenuDelDia)
class MenuDelDiaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'articulo', 'precio_promo', 'franja', 'activo')
    list_filter = ('activo', 'franja')


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('cliente_nombre', 'mesa', 'fecha_reserva', 'hora_reserva', 'num_personas', 'estado')
    list_filter = ('estado', 'fecha_reserva')


@admin.register(CuponDescuento)
class CuponDescuentoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'descripcion', 'tipo', 'valor', 'usos_realizados', 'usos_maximos', 'activo')
    list_filter = ('activo', 'tipo')
    search_fields = ('codigo', 'descripcion')


@admin.register(PerfilEmpleado)
class PerfilEmpleadoAdmin(admin.ModelAdmin):
    list_display = ('user', 'rol', 'telefono')
    list_filter = ('rol',)


@admin.register(MetaDiaria)
class MetaDiariaAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'objetivo_tickets', 'objetivo_ingresos')
    list_filter = ('fecha',)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'nivel', 'puntos', 'activo')
    list_filter = ('nivel', 'activo')
    search_fields = ('nombre', 'email', 'telefono')


@admin.register(ColaNumero)
class ColaNumeroAdmin(admin.ModelAdmin):
    list_display = ('numero', 'fecha', 'nombre_cliente', 'estado', 'creado')
    list_filter = ('estado', 'fecha')


@admin.register(PedidoMovil)
class PedidoMovilAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'estado', 'cliente_nombre', 'fecha')
    list_filter = ('estado',)


@admin.register(LineaPedidoMovil)
class LineaPedidoMovilAdmin(admin.ModelAdmin):
    list_display = ('pedido', 'articulo', 'unidades', 'notas')


@admin.register(PlanoRestaurante)
class PlanoRestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'ancho', 'alto', 'activo')


@admin.register(MesaPosicion)
class MesaPosicionAdmin(admin.ModelAdmin):
    list_display = ('mesa', 'plano', 'x', 'y', 'color')
    list_filter = ('plano',)


@admin.register(MensajeChat)
class MensajeChatAdmin(admin.ModelAdmin):
    list_display = ('emisor', 'texto', 'fecha', 'leido')
    list_filter = ('emisor', 'leido')


@admin.register(PedidoProveedor)
class PedidoProveedorAdmin(admin.ModelAdmin):
    list_display = ('insumo', 'cantidad_solicitada', 'estado', 'creado')
    list_filter = ('estado',)


@admin.register(FirmaDigital)
class FirmaDigitalAdmin(admin.ModelAdmin):
    list_display = ('venta', 'cliente_nombre', 'fecha')


@admin.register(PasoReceta)
class PasoRecetaAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'orden', 'titulo', 'tiempo_minutos')
    list_filter = ('articulo',)


@admin.register(NotificacionPush)
class NotificacionPushAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'mensaje', 'enviada', 'fecha')
    list_filter = ('enviada',)


@admin.register(DescuentoInteligente)
class DescuentoInteligenteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'tipo', 'porcentaje', 'activo')
    list_filter = ('tipo', 'activo')


@admin.register(ReviewRestaurante)
class ReviewRestauranteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'estrellas', 'fecha', 'visible')
    list_filter = ('estrellas', 'visible')


@admin.register(RatingProducto)
class RatingProductoAdmin(admin.ModelAdmin):
    list_display = ('articulo', 'cliente_nombre', 'estrellas', 'fecha')
    list_filter = ('estrellas',)


@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'activo')
    list_filter = ('activo',)


@admin.register(ComboItem)
class ComboItemAdmin(admin.ModelAdmin):
    list_display = ('combo', 'articulo', 'cantidad')
