from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save, post_delete
from django.db.models import F
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import (
    AuditLog, Articulo, CategoriaProducto, InsumoMateriaPrima,
    Mesa, RegistroGasto, OperacionVenta, ComposicionReceta,
    TurnoCaja, PedidoCocina, MenuDelDia, Reserva,
    CuponDescuento, PerfilEmpleado
)


def get_ip(request):
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def registrar_log(usuario, accion, modelo, objeto_id, descripcion, detalles=None, ip=None):
    AuditLog.objects.create(
        usuario=usuario, accion=accion, modelo=modelo,
        objeto_id=str(objeto_id), descripcion=descripcion,
        detalles_json=detalles or {}, ip_address=ip,
    )


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    registrar_log(user, 'LOGIN', 'Auth', user.id,
                  f'{user.username} inicio sesion', ip=get_ip(request))


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user is None:
        return
    registrar_log(user, 'LOGOUT', 'Auth', user.id,
                  f'{user.username} cerro sesion', ip=get_ip(request))


def _track_model(model_class, modelo_nombre):
    @receiver(post_save, sender=model_class)
    def on_save(sender, instance, created, **kwargs):
        accion = 'CREAR' if created else 'EDITAR'
        desc = f'{modelo_nombre} #{instance.id}: {"creado" if created else "actualizado"}'
        try:
            user = instance.empleado_caja or instance.empleado_autoriza
        except Exception:
            user = None
        registrar_log(user, accion, modelo_nombre, instance.id, desc)

    @receiver(post_delete, sender=model_class)
    def on_delete(sender, instance, **kwargs):
        desc = f'{modelo_nombre} #{instance.id}: eliminado'
        try:
            user = instance.empleado_caja or instance.empleado_autoriza
        except Exception:
            user = None
        registrar_log(user, 'ELIMINAR', modelo_nombre, instance.id, desc)


_track_model(Articulo, 'Articulo')
_track_model(CategoriaProducto, 'Categoria')
_track_model(InsumoMateriaPrima, 'Insumo')
_track_model(Mesa, 'Mesa')
_track_model(RegistroGasto, 'Gasto')
_track_model(OperacionVenta, 'Venta')
_track_model(ComposicionReceta, 'Receta')
_track_model(TurnoCaja, 'TurnoCaja')
_track_model(PedidoCocina, 'PedidoCocina')
_track_model(MenuDelDia, 'MenuDelDia')
_track_model(Reserva, 'Reserva')
_track_model(CuponDescuento, 'Cupon')
_track_model(PerfilEmpleado, 'PerfilEmpleado')


@receiver(post_save, sender=InsumoMateriaPrima)
def alerta_stock_bajo(sender, instance, **kwargs):
    """Envia email automatico cuando un insumo baja del minimo."""
    if instance.necesita_reposicion:
        from .emails import enviar_alerta_stock_bajo
        insumos_bajos = []
        for ins in InsumoMateriaPrima.objects.filter(cantidad_actual__lte=F('cantidad_minima')):
            falta = ins.cantidad_minima - ins.cantidad_actual
            insumos_bajos.append({
                'nombre': ins.nombre,
                'cantidad_actual': ins.cantidad_actual,
                'cantidad_minima': ins.cantidad_minima,
                'unidad_medida': ins.unidad_medida,
                'falta': falta,
            })
        if insumos_bajos:
            enviar_alerta_stock_bajo(insumos_bajos)


@receiver(post_save, sender=Reserva)
def notificar_reserva_confirmada(sender, instance, **kwargs):
    """Envia email cuando una reserva pasa a CONFIRMADA."""
    if instance.estado == 'CONFIRMADA' and instance.email_cliente:
        from .emails import enviar_reserva_confirmacion_email
        enviar_reserva_confirmacion_email(instance)
