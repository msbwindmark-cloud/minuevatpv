from django.contrib import admin
from django.contrib import messages
from django.db.models import Sum, F, Count, DecimalField, ExpressionWrapper
from django.utils import timezone
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from datetime import timedelta, date
from .views import es_admin_panel
from .models import (
    InsumoMateriaPrima, CategoriaProducto, Articulo,
    ComposicionReceta, OperacionVenta, LineaVenta, RegistroGasto, Mesa,
    AuditLog, TurnoCaja, PedidoCocina, MenuDelDia, Reserva,
    CuponDescuento, PerfilEmpleado, MetaDiaria, Cliente,
    ColaNumero, PedidoMovil, LineaPedidoMovil, PlanoRestaurante, MesaPosicion,
    MensajeChat, PedidoProveedor, FirmaDigital, PasoReceta, NotificacionPush,
    DescuentoInteligente, ReviewRestaurante, RatingProducto, Combo, ComboItem,
    EmailLog
)


@admin.register(InsumoMateriaPrima)
class InsumoMateriaPrimaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'stock_estado', 'cantidad_actual', 'cantidad_minima', 'unidad_medida', 'necesita_reposicion_display')
    list_editable = ('cantidad_actual', 'cantidad_minima')
    search_fields = ('nombre',)
    list_filter = ('unidad_medida',)
    actions = ['marcar_para_reposicion', 'actualizar_stock_minimo']
    fieldsets = (
        ('Información del Insumo', {
            'fields': ('nombre', 'unidad_medida')
        }),
        ('Stock', {
            'fields': ('cantidad_actual', 'cantidad_minima'),
            'description': 'Edita directamente el stock actual o el mínimo de alerta'
        }),
    )

    def stock_estado(self, obj):
        if obj.cantidad_actual <= 0:
            return '🔴 AGOTADO'
        elif obj.cantidad_actual <= obj.cantidad_minima:
            return '🟡 BAJO'
        else:
            return '🟢 OK'
    stock_estado.short_description = 'Estado'
    stock_estado.admin_order_field = 'cantidad_actual'

    def necesita_reposicion_display(self, obj):
        return obj.necesita_reposicion
    necesita_reposicion_display.short_description = '¿Necesita reposición?'
    necesita_reposicion_display.boolean = True

    @admin.action(description='Marcar seleccionados para reposición')
    def marcar_para_reposicion(self, request, queryset):
        count = queryset.update(cantidad_actual=0)
        self.message_user(request, f'{count} insumos marcados como agotados (stock = 0)')

    @admin.action(description='Establecer stock mínimo a la cantidad actual')
    def actualizar_stock_minimo(self, request, queryset):
        count = 0
        for insumo in queryset:
            insumo.cantidad_minima = insumo.cantidad_actual
            insumo.save()
            count += 1
        self.message_user(request, f'{count} insumos: stock mínimo actualizado')


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
    list_display = ('articulo', 'insumo', 'cantidad_consumida', 'stock_insumo', 'unidades_posibles')
    list_filter = ('articulo__categoria',)
    search_fields = ('articulo__nombre', 'insumo__nombre')
    raw_id_fields = ('articulo', 'insumo')

    def stock_insumo(self, obj):
        return f"{obj.insumo.cantidad_actual} {obj.insumo.unidad_medida}"
    stock_insumo.short_description = 'Stock del insumo'

    def unidades_posibles(self, obj):
        if obj.cantidad_consumida > 0:
            unidades = int(obj.insumo.cantidad_actual / obj.cantidad_consumida)
            return f"{unidades} uds"
        return '-'
    unidades_posibles.short_description = 'Unidades posibles'


@admin.register(OperacionVenta)
class OperacionVentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'fecha_registro', 'empleado_caja', 'mesa', 'total_facturado', 'forma_pago', 'satisfaccion')
    list_filter = ('forma_pago', 'fecha_registro', 'satisfaccion')
    search_fields = ('empleado_caja__username',)
    date_hierarchy = 'fecha_registro'
    readonly_fields = ('fecha_registro', 'hash_seguridad')


@admin.register(LineaVenta)
class LineaVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'articulo', 'unidades', 'precio_aplicado_con_iva')


@admin.register(RegistroGasto)
class RegistroGastoAdmin(admin.ModelAdmin):
    list_display = ('concepto', 'importe_total', 'fecha_gasto', 'empleado_autoriza')
    list_filter = ('fecha_gasto',)
    search_fields = ('concepto',)
    date_hierarchy = 'fecha_gasto'
    readonly_fields = ('fecha_gasto',)
    fieldsets = (
        ('Detalle del Gasto', {
            'fields': ('concepto', 'importe_total', 'empleado_autoriza')
        }),
        ('Información', {
            'fields': ('fecha_gasto',),
            'classes': ('collapse',)
        }),
    )


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
    actions = ['enviar_cierre_email']

    @admin.action(description='Enviar cierre de caja por email')
    def enviar_cierre_email(self, request, queryset):
        from .emails import enviar_cierre_caja_email
        count = 0
        for turno in queryset.filter(cerrado=True):
            enviar_cierre_caja_email(turno)
            count += 1
        self.message_user(request, f'{count} cierre(s) de caja enviado(s) por email')


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
    list_display = ('cliente_nombre', 'mesa', 'fecha_reserva', 'hora_reserva', 'num_personas', 'email_cliente', 'estado')
    list_filter = ('estado', 'fecha_reserva')
    search_fields = ('cliente_nombre', 'email_cliente')
    fieldsets = (
        ('Cliente', {
            'fields': ('cliente_nombre', 'cliente_telefono', 'email_cliente')
        }),
        ('Reserva', {
            'fields': ('mesa', 'fecha_reserva', 'hora_reserva', 'num_personas', 'notas')
        }),
        ('Estado', {
            'fields': ('estado', 'creado_por')
        }),
    )
    actions = ['confirmar_y_enviar_email']

    @admin.action(description='Confirmar reserva y enviar email al cliente')
    def confirmar_y_enviar_email(self, request, queryset):
        from .emails import enviar_reserva_confirmacion_email
        count = 0
        for reserva in queryset.filter(estado='PENDIENTE'):
            reserva.estado = 'CONFIRMADA'
            reserva.save()
            enviar_reserva_confirmacion_email(reserva)
            count += 1
        self.message_user(request, f'{count} reserva(s) confirmada(s) y email(s) enviado(s)')


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
    list_display = ('insumo', 'cantidad_solicitada', 'unidad_insumo', 'email_proveedor', 'estado', 'creado', 'creado_por')
    list_filter = ('estado', 'creado')
    search_fields = ('insumo__nombre', 'notas', 'email_proveedor')
    date_hierarchy = 'creado'
    readonly_fields = ('creado',)
    actions = ['marcar_enviado', 'marcar_recibido', 'cancelar_pedido', 'enviar_pedido_email']
    fieldsets = (
        ('Detalle del Pedido', {
            'fields': ('insumo', 'cantidad_solicitada', 'email_proveedor', 'notas')
        }),
        ('Estado', {
            'fields': ('estado',)
        }),
        ('Información', {
            'fields': ('creado', 'creado_por'),
            'classes': ('collapse',)
        }),
    )

    def unidad_insumo(self, obj):
        return obj.insumo.unidad_medida
    unidad_insumo.short_description = 'Unidad'

    @admin.action(description='Marcar como enviado al proveedor')
    def marcar_enviado(self, request, queryset):
        count = queryset.filter(estado='PENDIENTE').update(estado='ENVIADO')
        self.message_user(request, f'{count} pedidos marcados como enviados')

    @admin.action(description='Marcar como recibido (actualizar stock)')
    def marcar_recibido(self, request, queryset):
        count = 0
        for pedido in queryset.filter(estado='ENVIADO'):
            pedido.estado = 'RECIBIDO'
            pedido.save()
            pedido.insumo.cantidad_actual += pedido.cantidad_solicitada
            pedido.insumo.save()
            count += 1
        self.message_user(request, f'{count} pedidos recibidos. Stock actualizado automáticamente.')

    @admin.action(description='Cancelar pedidos seleccionados')
    def cancelar_pedido(self, request, queryset):
        count = queryset.filter(estado__in=['PENDIENTE', 'ENVIADO']).update(estado='CANCELADO')
        self.message_user(request, f'{count} pedidos cancelados')

    @admin.action(description='Enviar pedido por email al proveedor')
    def enviar_pedido_email(self, request, queryset):
        from .emails import enviar_pedido_proveedor_email
        enviados = 0
        for pedido in queryset.filter(estado='PENDIENTE'):
            if pedido.email_proveedor:
                enviar_pedido_proveedor_email(pedido)
                enviados += 1
            else:
                self.message_user(request, f'Pedido #{pedido.id} sin email de proveedor — saltado', level=messages.WARNING)
        self.message_user(request, f'{enviados} pedido(s) enviado(s) por email')


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


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('asunto', 'tipo', 'destinatarios', 'enviado', 'fecha_envio')
    list_filter = ('tipo', 'enviado')
    search_fields = ('asunto', 'destinatarios')
    readonly_fields = ('asunto', 'destinatarios', 'tipo', 'enviado', 'error', 'fecha_envio')

    def has_add_permission(self, request):
        return False


# ── Views de envio de email por boton ──────────────────────────────────────

@login_required
@user_passes_test(es_admin_panel)
def admin_enviar_informe_email(request):
    """Genera y envia el informe semanal al email del usuario conectado."""
    from decimal import Decimal
    from .models import OperacionVenta, RegistroGasto, LineaVenta
    from .emails import enviar_informe_semanal_email

    if not request.user.email:
        messages.error(request, 'Tu usuario no tiene email configurado. Anade tu email en tu perfil.')
        return redirect('/admin/')

    hoy = timezone.now().date()
    fecha_inicio = hoy - timedelta(days=hoy.weekday())
    fecha_fin = fecha_inicio + timedelta(days=6)

    ventas = OperacionVenta.objects.filter(
        fecha_registro__date__gte=fecha_inicio,
        fecha_registro__date__lte=fecha_fin
    )
    gastos = RegistroGasto.objects.filter(
        fecha_gasto__date__gte=fecha_inicio,
        fecha_gasto__date__lte=fecha_fin
    )

    total_ventas = ventas.aggregate(t=Sum('total_facturado'))['t'] or Decimal('0.00')
    total_gastos = gastos.aggregate(t=Sum('importe_total'))['t'] or Decimal('0.00')
    total_tickets = ventas.count()

    dias_nombres = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
    desglose_diario = []
    for i in range(7):
        dia = fecha_inicio + timedelta(days=i)
        v_dia = ventas.filter(fecha_registro__date=dia).aggregate(t=Sum('total_facturado'))['t'] or Decimal('0.00')
        t_dia = ventas.filter(fecha_registro__date=dia).count()
        desglose_diario.append({'nombre': dias_nombres[i], 'ventas': float(v_dia), 'tickets': t_dia})

    top_raw = (
        LineaVenta.objects
        .filter(venta__fecha_registro__date__gte=fecha_inicio, venta__fecha_registro__date__lte=fecha_fin)
        .values('articulo__nombre')
        .annotate(total=Sum('unidades'))
        .order_by('-total')[:10]
    )
    top_productos = [{'nombre': t['articulo__nombre'], 'total': t['total']} for t in top_raw]

    comparativa = None
    fecha_inicio_ant = fecha_inicio - timedelta(days=7)
    fecha_fin_ant = fecha_fin - timedelta(days=7)
    total_ant = OperacionVenta.objects.filter(
        fecha_registro__date__gte=fecha_inicio_ant,
        fecha_registro__date__lte=fecha_fin_ant
    ).aggregate(t=Sum('total_facturado'))['t'] or Decimal('0.00')
    if total_ant > 0:
        comparativa = {'pct': float((total_ventas - total_ant) / total_ant * 100)}

    context = {
        'fecha_inicio': fecha_inicio.strftime('%d/%m/%Y'),
        'fecha_fin': fecha_fin.strftime('%d/%m/%Y'),
        'total_ventas': float(total_ventas),
        'total_tickets': total_tickets,
        'total_gastos': float(total_gastos),
        'desglose_diario': desglose_diario,
        'top_productos': top_productos,
        'comparativa': comparativa,
    }

    enviado = enviar_informe_semanal_email(context)
    if enviado:
        messages.success(request, f'Informe semanal enviado a {request.user.email}')
    else:
        messages.error(request, 'Error al enviar el informe. Comprueba la configuracion SMTP.')
    return redirect('/admin/informe-semanal/')


@login_required
@user_passes_test(es_admin_panel)
def admin_enviar_pedidos_email(request):
    """Envia por email todos los pedidos pendientes al proveedor."""
    from .emails import enviar_pedido_proveedor_email

    if not request.user.email:
        messages.error(request, 'Tu usuario no tiene email configurado. Anade tu email en tu perfil.')
        return redirect('/admin/')

    pendientes = PedidoProveedor.objects.filter(estado='PENDIENTE')
    if not pendientes.exists():
        messages.warning(request, 'No hay pedidos pendientes para enviar.')
        return redirect('/admin/tpv/pedidoproveedor/')

    enviados = 0
    sin_email = 0
    for pedido in pendientes:
        if pedido.email_proveedor:
            pedido.estado = 'ENVIADO'
            pedido.save()
            enviar_pedido_proveedor_email(pedido)
            enviados += 1
        else:
            sin_email += 1

    if enviados > 0:
        messages.success(request, f'{enviados} pedido(s) enviado(s) por email. {f"({sin_email} sin email de proveedor)" if sin_email else ""}')
    else:
        messages.warning(request, f'Ningun pedido tenia email de proveedor configurado.')
    return redirect('/admin/tpv/pedidoproveedor/')


@login_required
@user_passes_test(es_admin_panel)
def admin_enviar_cierre_email(request):
    """Envia el ultimo turno cerrado por email al usuario conectado."""
    from .emails import enviar_cierre_caja_email

    if not request.user.email:
        messages.error(request, 'Tu usuario no tiene email configurado. Anade tu email en tu perfil.')
        return redirect('/admin/')

    turno = TurnoCaja.objects.filter(cerrado=True).order_by('-fecha_cierre').first()
    if not turno:
        messages.warning(request, 'No hay turnos cerrados para enviar.')
        return redirect('/admin/tpv/turnocaja/')

    enviado = enviar_cierre_caja_email(turno)
    if enviado:
        messages.success(request, f'Cierre de caja #{turno.id} enviado a {request.user.email}')
    else:
        messages.error(request, 'Error al enviar el cierre. Comprueba la configuracion SMTP.')
    return redirect('/admin/tpv/turnocaja/')


# Template personalizado para el admin index con enlaces a gestiones
admin.site.index_template = 'admin/custom_index.html'


# Ocultar Users y Groups para staff (no-superuser)
class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if not request.user.is_superuser:
            app_list = [app for app in app_list if app['app_label'] != 'auth']
        return app_list

admin.site.__class__ = CustomAdminSite
