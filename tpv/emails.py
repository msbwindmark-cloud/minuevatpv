import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone

logger = logging.getLogger(__name__)

COOLDOWN_STOCK = 3600  # 1 hora en segundos


def _get_destinatarios_staff():
    """Devuelve emails de todos los staff + superusers."""
    destinatarios = []
    for u in User.objects.filter(is_staff=True, is_active=True):
        if u.email:
            destinatarios.append(u.email)
    return destinatarios


def _get_destinatarios_gerente():
    """Devuelve emails solo de superusers."""
    return [u.email for u in User.objects.filter(is_superuser=True, is_active=True) if u.email]


def _registrar_log_email(asunto, destinatarios, tipo, enviado=True, error=''):
    """Registra cada email enviado en EmailLog."""
    from .models import EmailLog
    EmailLog.objects.create(
        asunto=asunto,
        destinatarios=', '.join(destinatarios),
        tipo=tipo,
        enviado=enviado,
        error=error,
    )


def _cooldownactivo(tipo, segundos=COOLDOWN_STOCK):
    """Verifica si ya se envio un email de este tipo recientemente."""
    from .models import EmailLog
    reciente = EmailLog.objects.filter(
        tipo=tipo, enviado=True,
        fecha_envio__gte=timezone.now() - timezone.timedelta(seconds=segundos)
    ).exists()
    return reciente


def enviar_email_html(asunto, destinatarios, template_html, context=None, tipo='general'):
    """Funcion base para enviar emails HTML."""
    if not destinatarios:
        logger.warning(f'Email sin destinatarios: {asunto}')
        return False
    try:
        context = context or {}
        context['asunto'] = asunto
        context['fecha'] = timezone.now().strftime('%d/%m/%Y %H:%M')
        context['sistema'] = 'Sistema TPV Cafeteria'

        html_content = render_to_string(template_html, context)
        text_content = f'{asunto}\n\nFecha: {context["fecha"]}\nSistema: {context["sistema"]}'

        msg = EmailMultiAlternatives(
            subject=asunto,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=destinatarios,
        )
        msg.attach_alternative(html_content, 'text/html')
        msg.send(fail_silently=False)

        _registrar_log_email(asunto, destinatarios, tipo, enviado=True)
        logger.info(f'Email enviado: {asunto} -> {destinatarios}')
        return True
    except Exception as e:
        error_msg = str(e)
        _registrar_log_email(asunto, destinatarios, tipo, enviado=False, error=error_msg)
        logger.error(f'Error enviando email: {error_msg}')
        return False


def enviar_alerta_stock_bajo(insumos_bajos):
    """Envia email de alerta cuando hay insumos con stock bajo."""
    if _cooldownactivo('stock_bajo'):
        return False

    destinatarios = _get_destinatarios_staff()
    if not destinatarios:
        return False

    asunto = f'⚠️ Alerta Stock Bajo - {len(insumos_bajos)} insumo(s) por debajo del minimo'
    context = {'insumos': insumos_bajos}
    return enviar_email_html(asunto, destinatarios, 'email/stock_bajo.html', context, tipo='stock_bajo')


def enviar_informe_semanal_email(datos_semana):
    """Envia el informe semanal por email."""
    destinatarios = _get_destinatarios_staff()
    if not destinatarios:
        return False

    asunto = f'📊 Informe Semanal Cafeteria - {datos_semana.get("fecha_inicio", "")} a {datos_semana.get("fecha_fin", "")}'
    return enviar_email_html(asunto, destinatarios, 'email/informe_semanal.html', datos_semana, tipo='informe_semanal')


def enviar_pedido_proveedor_email(pedido):
    """Envia confirmacion de pedido al proveedor + copia al superuser."""
    destinatarios = []
    if pedido.email_proveedor:
        destinatarios.append(pedido.email_proveedor)
    else:
        logger.warning(f'Pedido #{pedido.id} sin email de proveedor')
        return False

    # Copia al superuser
    copias = _get_destinatarios_gerente()
    asunto = f'📦 PedidoProveedor #{pedido.id} - {pedido.insumo.nombre}: {pedido.cantidad_solicitada} {pedido.insumo.unidad_medida}'
    context = {'pedido': pedido}
    msg = enviar_email_html(asunto, destinatarios, 'email/pedido_proveedor.html', context, tipo='pedido_proveedor')

    # Enviar copia por separado al superuser
    if copias:
        enviar_email_html(
            f'[COPIA] {asunto}',
            copias,
            'email/pedido_proveedor_copia.html',
            {'pedido': pedido},
            tipo='pedido_proveedor_copia'
        )
    return msg


def enviar_reserva_confirmacion_email(reserva):
    """Envia confirmacion de reserva al cliente."""
    if not reserva.email_cliente:
        return False

    destinatarios = [reserva.email_cliente]
    copias = _get_destinatarios_staff()

    asunto = f'✅ Reserva Confirmada - Mesa {reserva.mesa.numero} el {reserva.fecha_reserva.strftime("%d/%m/%Y")}'
    context = {'reserva': reserva}
    msg = enviar_email_html(asunto, destinatarios, 'email/reserva_confirmacion.html', context, tipo='reserva_confirmacion')

    if copias:
        enviar_email_html(
            f'[INFO] Nueva reserva: {reserva.cliente_nombre}',
            copias,
            'email/reserva_notificacion_staff.html',
            {'reserva': reserva},
            tipo='reserva_staff'
        )
    return msg


def enviar_cierre_caja_email(turno):
    """Envia el resumen del cierre de caja."""
    destinatarios = _get_destinatarios_staff()
    if not destinatarios:
        return False

    asunto = f'💰 Cierre de Caja - Turno #{turno.id} - {turno.cajero.username}'
    context = {'turno': turno}
    return enviar_email_html(asunto, destinatarios, 'email/cierre_caja.html', context, tipo='cierre_caja')
