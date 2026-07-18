from decimal import Decimal
from django.core.management.base import BaseCommand
from tpv.models import (
    CategoriaProducto, Articulo, InsumoMateriaPrima, ComposicionReceta
)


class Command(BaseCommand):
    help = 'Carga datos iniciales de prueba para la cafeteria'

    def handle(self, *args, **kwargs):
        # --- INSUMOS / MATERIA PRIMA ---
        insumos_data = [
            ('Cafe en graos', Decimal('5000'), Decimal('500'), 'g'),
            ('Leche entera', Decimal('10000'), Decimal('1000'), 'ml'),
            ('Leche desnatada', Decimal('5000'), Decimal('500'), 'ml'),
            ('Azucar', Decimal('3000'), Decimal('300'), 'g'),
            ('Chocolate en polvo', Decimal('1500'), Decimal('200'), 'g'),
            ('Te verde', Decimal('200'), Decimal('20'), 'ud'),
            ('Te negro', Decimal('200'), Decimal('20'), 'ud'),
            ('Hojaldrados', Decimal('60'), Decimal('10'), 'ud'),
            ('Pan de molde', Decimal('100'), Decimal('10'), 'ud'),
            ('Jamón serrano', Decimal('500'), Decimal('50'), 'g'),
            ('Queso manchego', Decimal('500'), Decimal('50'), 'g'),
            ('Mantequilla', Decimal('500'), Decimal('50'), 'g'),
            ('Nata montada', Decimal('1000'), Decimal('100'), 'ml'),
            ('Licor Baileys', Decimal('500'), Decimal('50'), 'ml'),
            ('Hielo', Decimal('3000'), Decimal('200'), 'g'),
            ('Zumo de naranja', Decimal('2000'), Decimal('200'), 'ml'),
            ('Harina', Decimal('2000'), Decimal('200'), 'g'),
            ('Huevos', Decimal('30'), Decimal('6'), 'ud'),
        ]

        insumos = {}
        for nombre, cantidad, minima, unidad in insumos_data:
            obj, created = InsumoMateriaPrima.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'cantidad_actual': cantidad,
                    'cantidad_minima': minima,
                    'unidad_medida': unidad,
                }
            )
            insumos[nombre] = obj
            if created:
                self.stdout.write(f'  + Insumo: {obj}')

        # --- CATEGORIAS ---
        cats_data = [
            ('Calientes', '☕'),
            ('Frias', '🧊'),
            ('Bocadillos', '🥪'),
            ('Pasteleria', '🥐'),
            ('Licores', '🥃'),
        ]

        cats = {}
        for nombre, icono in cats_data:
            obj, created = CategoriaProducto.objects.get_or_create(
                nombre=nombre,
                defaults={'icono': icono}
            )
            cats[nombre] = obj
            if created:
                self.stdout.write(f'  + Categoria: {obj.nombre}')

        # --- ARTICULOS ---
        articulos_data = [
            # Bebidas Calientes
            ('Cafe Solo', Decimal('0.80'), '10.00', 'Calientes', [
                ('Cafe en graos', Decimal('8')),
            ]),
            ('Cafe con Leche', Decimal('1.10'), '10.00', 'Calientes', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('200')),
            ]),
            ('Cortado', Decimal('1.00'), '10.00', 'Calientes', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('50')),
            ]),
            ('Capuchino', Decimal('1.50'), '10.00', 'Calientes', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('250')),
                ('Chocolate en polvo', Decimal('5')),
            ]),
            ('Chocolate Caliente', Decimal('1.60'), '10.00', 'Calientes', [
                ('Leche entera', Decimal('300')),
                ('Chocolate en polvo', Decimal('25')),
            ]),
            ('Te Verde', Decimal('1.00'), '10.00', 'Calientes', [
                ('Te verde', Decimal('1')),
            ]),
            ('Te Negro', Decimal('1.00'), '10.00', 'Calientes', [
                ('Te negro', Decimal('1')),
            ]),

            # Bebidas Frias
            ('Cafe Frio', Decimal('1.80'), '10.00', 'Frias', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('150')),
                ('Hielo', Decimal('100')),
            ]),
            ('Capuchino Frio', Decimal('2.20'), '10.00', 'Frias', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('200')),
                ('Hielo', Decimal('80')),
                ('Chocolate en polvo', Decimal('5')),
            ]),
            ('Zumo de Naranja', Decimal('1.80'), '10.00', 'Frias', [
                ('Zumo de naranja', Decimal('250')),
            ]),
            ('Agua Mineral', Decimal('0.80'), '4.00', 'Frias', []),

            # Bocadillos
            ('Bocadillo Jamon', Decimal('2.50'), '10.00', 'Bocadillos', [
                ('Pan de molde', Decimal('2')),
                ('Jamón serrano', Decimal('60')),
                ('Mantequilla', Decimal('5')),
            ]),
            ('Bocadillo Queso', Decimal('2.20'), '10.00', 'Bocadillos', [
                ('Pan de molde', Decimal('2')),
                ('Queso manchego', Decimal('50')),
                ('Mantequilla', Decimal('5')),
            ]),
            ('Bocadillo Mixto', Decimal('2.80'), '10.00', 'Bocadillos', [
                ('Pan de molde', Decimal('2')),
                ('Jamón serrano', Decimal('40')),
                ('Queso manchego', Decimal('30')),
                ('Mantequilla', Decimal('5')),
            ]),

            # Pasteleria
            ('Croissant', Decimal('1.20'), '10.00', 'Pasteleria', [
                ('Hojaldrados', Decimal('1')),
                ('Mantequilla', Decimal('10')),
            ]),
            ('Napolitana Chocolate', Decimal('1.50'), '10.00', 'Pasteleria', [
                ('Hojaldrados', Decimal('1')),
                ('Chocolate en polvo', Decimal('15')),
                ('Azucar', Decimal('10')),
            ]),
            ('Ensaimada', Decimal('1.30'), '10.00', 'Pasteleria', [
                ('Harina', Decimal('50')),
                ('Azucar', Decimal('15')),
                ('Huevos', Decimal('1')),
            ]),

            # Licores
            ('Baileys', Decimal('2.50'), '21.00', 'Licores', [
                ('Licor Baileys', Decimal('40')),
                ('Hielo', Decimal('50')),
            ]),
            ('Cafe con Baileys', Decimal('3.00'), '21.00', 'Licores', [
                ('Cafe en graos', Decimal('8')),
                ('Leche entera', Decimal('100')),
                ('Licor Baileys', Decimal('30')),
            ]),
        ]

        for nombre, precio, iva, cat_nombre, receta in articulos_data:
            if cat_nombre not in cats:
                cat_nombre = 'Calientes'
            articulo, created = Articulo.objects.get_or_create(
                nombre=nombre,
                defaults={
                    'precio_sin_iva': precio,
                    'tipo_iva': iva,
                    'categoria': cats[cat_nombre],
                    'activo': True,
                }
            )
            if created:
                self.stdout.write(f'  + Articulo: {articulo}')
                for insumo_nombre, cantidad in receta:
                    if insumo_nombre in insumos:
                        ComposicionReceta.objects.create(
                            articulo=articulo,
                            insumo=insumos[insumo_nombre],
                            cantidad_consumida=cantidad
                        )

        total_art = Articulo.objects.count()
        total_cats = CategoriaProducto.objects.count()
        total_ins = InsumoMateriaPrima.objects.count()
        self.stdout.write(self.style.SUCCESS(
            f'\nDatos cargados: {total_cats} categorias, {total_art} articulos, {total_ins} insumos'
        ))
