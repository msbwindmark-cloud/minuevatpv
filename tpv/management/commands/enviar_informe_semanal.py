import os
import sys
from decimal import Decimal
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Sum

from tpv.models import OperacionVenta, LineaVenta, RegistroGasto
from tpv.emails import enviar_informe_semanal_email


class Command(BaseCommand):
    help = 'Envia el informe semanal por email a staff y superusers'

    def add_arguments(self, parser):
        parser.add_argument(
            '--semana', type=int, default=0,
            help='Offset de semana (0=actual, -1=anterior, etc)'
        )

    def handle(self, *args, **options):
        semana_offset = options['semana']
        hoy = timezone.now().date()
        fecha_inicio = hoy - timedelta(days=hoy.weekday()) + timedelta(weeks=semana_offset)
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

        # Desglose diario
        dias_nombres = ['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes', 'Sabado', 'Domingo']
        desglose_diario = []
        for i in range(7):
            dia = fecha_inicio + timedelta(days=i)
            v_dia = ventas.filter(fecha_registro__date=dia).aggregate(t=Sum('total_facturado'))['t'] or Decimal('0.00')
            t_dia = ventas.filter(fecha_registro__date=dia).count()
            desglose_diario.append({
                'nombre': dias_nombres[i],
                'ventas': float(v_dia),
                'tickets': t_dia,
            })

        # Top productos
        top_raw = (
            LineaVenta.objects
            .filter(venta__fecha_registro__date__gte=fecha_inicio, venta__fecha_registro__date__lte=fecha_fin)
            .values('articulo__nombre')
            .annotate(total=Sum('unidades'))
            .order_by('-total')[:10]
        )
        top_productos = [{'nombre': t['articulo__nombre'], 'total': t['total']} for t in top_raw]

        # Comparativa semana anterior
        comparativa = None
        fecha_inicio_ant = fecha_inicio - timedelta(days=7)
        fecha_fin_ant = fecha_fin - timedelta(days=7)
        ventas_ant = OperacionVenta.objects.filter(
            fecha_registro__date__gte=fecha_inicio_ant,
            fecha_registro__date__lte=fecha_fin_ant
        )
        total_ant = ventas_ant.aggregate(t=Sum('total_facturado'))['t'] or Decimal('0.00')
        if total_ant > 0:
            pct = float((total_ventas - total_ant) / total_ant * 100)
            comparativa = {'pct': pct}

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
            self.stdout.write(self.style.SUCCESS(
                f'Informe semanal enviado: {fecha_inicio} - {fecha_fin}'
            ))
        else:
            self.stdout.write(self.style.ERROR('Error al enviar el informe semanal'))
